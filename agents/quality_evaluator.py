"""质量评估Agent"""
from typing import Any, Dict, List
from agents.base import BaseAgent
from models.video_result import VideoResult, EvaluationResult, EvaluationScore
from tools.llm import GPT4VisionTool
from config.prompts import prompts
from config.settings import settings


class QualityEvaluator(BaseAgent):
    """质量评估Agent - 评估视频质量并选择最佳"""

    SCORE_WEIGHTS = {
        "product_consistency": 0.55,
        "visual_quality": 0.15,
        "creativity": 0.15,
        "ad_effectiveness": 0.15,
    }
    CONSISTENCY_THRESHOLD = 18.0
    CONSISTENCY_CHECK_FIELDS = (
        "shape_structure",
        "material_finish",
        "primary_color",
        "brand_elements",
        "key_details",
    )

    def __init__(self):
        super().__init__("QualityEvaluator")
        self.vision_tool = GPT4VisionTool()

    async def execute(
        self,
        videos: List[VideoResult],
        product_image: str,
    ) -> EvaluationResult:
        """
        评估视频质量

        Args:
            videos: 视频结果列表
            product_image: 原始产品图片

        Returns:
            EvaluationResult: 最佳视频的评估结果
        """
        self.log_start(f"Evaluating {len(videos)} videos")

        successful_videos = [v for v in videos if v.success]
        if not successful_videos:
            self.logger.warning("No successful videos to evaluate")
            return EvaluationResult(
                model_name="none",
                video_path="",
                score=EvaluationScore(),
            )

        evaluations = []

        for video in successful_videos:
            try:
                # 提取关键帧
                frames = self._extract_keyframes(video.video_path)

                # 评估
                evaluation = await self._evaluate_video(product_image, frames, video)
                evaluations.append(evaluation)

            except Exception as e:
                self.log_error(f"Evaluating {video.model_name}", e)
                evaluations.append(EvaluationResult(
                    model_name=video.model_name,
                    video_path=video.video_path,
                    score=EvaluationScore(),
                    comments="Evaluation failed.",
                    metadata={
                        "weighted_score": 0.0,
                        "qualified": False,
                        "rejection_reason": "evaluation_error",
                        "critical_issues": [],
                        "consistency_checks": {},
                    },
                ))

        # 排序并选择最佳
        evaluations.sort(key=self._ranking_key, reverse=True)

        for i, ev in enumerate(evaluations):
            ev.ranking = i + 1
            if i == 0:
                ev.is_best = True

        best = evaluations[0] if evaluations else None

        self.log_complete(
            "Quality evaluation",
            (
                "Best: "
                f"{best.model_name if best else 'none'} "
                f"(Weighted: {best.metadata.get('weighted_score', 0) if best else 0}, "
                f"Consistency: {best.score.product_consistency if best else 0})"
            ),
        )

        return best

    def _extract_keyframes(self, video_path: str, num_frames: int = 3) -> List[str]:
        """提取视频关键帧"""
        from pathlib import Path
        import subprocess

        output_dir = Path(settings.temp_dir) / "frames"
        output_dir.mkdir(parents=True, exist_ok=True)

        frames = []

        # 使用ffmpeg提取帧
        for i in range(num_frames):
            timestamp = i * 1.5  # 每1.5秒一帧
            output_path = str(output_dir / f"{Path(video_path).stem}_frame_{i}.jpg")

            cmd = [
                "ffmpeg", "-y",
                "-ss", str(timestamp),
                "-i", video_path,
                "-frames:v", "1",
                output_path,
            ]

            try:
                subprocess.run(cmd, capture_output=True, check=True)
                frames.append(output_path)
            except Exception as e:
                self.logger.warning(f"Failed to extract frame {i}: {e}")

        return frames

    async def _evaluate_video(
        self,
        product_image: str,
        frames: List[str],
        video: VideoResult,
    ) -> EvaluationResult:
        """评估单个视频"""
        system_prompt, user_prompt = prompts.get_quality_evaluator_prompts()
        enhanced_user_prompt = (
            f"{user_prompt.strip()}\n\n"
            "Return JSON with these fields:\n"
            "- product_consistency\n"
            "- visual_quality\n"
            "- creativity\n"
            "- ad_effectiveness\n"
            "- consistency_checks: {\n"
            '    "shape_structure": 0-5,\n'
            '    "material_finish": 0-5,\n'
            '    "primary_color": 0-5,\n'
            '    "brand_elements": 0-5,\n'
            '    "key_details": 0-5\n'
            "  }\n"
            "- critical_issues: []\n"
            "- summary: short string\n"
            "Use critical_issues for severe consistency failures such as shape change, wrong color, "
            "logo missing, material mismatch, or missing signature details."
        )

        try:
            result = await self.vision_tool.analyze_images_json(
                image_paths=[product_image] + frames,
                prompt=enhanced_user_prompt,
                system_prompt=system_prompt,
            )
            return self._build_evaluation_result(
                model_name=video.model_name,
                video_path=video.video_path,
                raw_result=result,
            )

        except Exception as e:
            self.log_error(f"Scoring {video.model_name}", e)
            return EvaluationResult(
                model_name=video.model_name,
                video_path=video.video_path,
                score=EvaluationScore(),
                comments="Evaluation failed.",
                metadata={
                    "weighted_score": 0.0,
                    "qualified": False,
                    "rejection_reason": "scoring_error",
                    "critical_issues": [],
                    "consistency_checks": {},
                },
            )

    def _build_evaluation_result(
        self,
        model_name: str,
        video_path: str,
        raw_result: Dict[str, Any],
    ) -> EvaluationResult:
        score = EvaluationScore(
            product_consistency=self._safe_float(raw_result.get("product_consistency", 0)),
            visual_quality=self._safe_float(raw_result.get("visual_quality", 0)),
            creativity=self._safe_float(raw_result.get("creativity", 0)),
            ad_effectiveness=self._safe_float(raw_result.get("ad_effectiveness", 0)),
        )
        consistency_checks = self._normalize_consistency_checks(raw_result.get("consistency_checks"))
        critical_issues = self._normalize_critical_issues(raw_result.get("critical_issues"))
        qualified, rejection_reason = self._qualify_result(score, critical_issues)
        weighted_score = self._weighted_total(score)

        summary = str(raw_result.get("summary", "")).strip()
        comments = summary or self._build_default_comment(score, qualified, rejection_reason, critical_issues)

        return EvaluationResult(
            model_name=model_name,
            video_path=video_path,
            score=score,
            comments=comments,
            metadata={
                "weighted_score": weighted_score,
                "qualified": qualified,
                "rejection_reason": rejection_reason,
                "critical_issues": critical_issues,
                "consistency_checks": consistency_checks,
            },
        )

    def _ranking_key(self, evaluation: EvaluationResult):
        return (
            1 if evaluation.metadata.get("qualified") else 0,
            evaluation.metadata.get("weighted_score", 0.0),
            evaluation.score.product_consistency,
            evaluation.score.total_score,
        )

    def _weighted_total(self, score: EvaluationScore) -> float:
        weighted_total = (
            score.product_consistency * self.SCORE_WEIGHTS["product_consistency"]
            + score.visual_quality * self.SCORE_WEIGHTS["visual_quality"]
            + score.creativity * self.SCORE_WEIGHTS["creativity"]
            + score.ad_effectiveness * self.SCORE_WEIGHTS["ad_effectiveness"]
        )
        return round(weighted_total, 2)

    def _qualify_result(
        self,
        score: EvaluationScore,
        critical_issues: List[str],
    ) -> tuple[bool, str]:
        if critical_issues:
            return False, "critical_consistency_issues"
        if score.product_consistency < self.CONSISTENCY_THRESHOLD:
            return False, "product_consistency_below_threshold"
        return True, ""

    def _normalize_consistency_checks(self, value: Any) -> Dict[str, float]:
        checks = value if isinstance(value, dict) else {}
        return {
            field: self._safe_float(checks.get(field, 0))
            for field in self.CONSISTENCY_CHECK_FIELDS
        }

    def _normalize_critical_issues(self, value: Any) -> List[str]:
        if not isinstance(value, list):
            return []
        normalized = []
        for item in value:
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized

    def _build_default_comment(
        self,
        score: EvaluationScore,
        qualified: bool,
        rejection_reason: str,
        critical_issues: List[str],
    ) -> str:
        if qualified:
            return (
                "Product identity remains acceptably consistent across sampled frames. "
                f"Consistency score: {score.product_consistency:.1f}/25."
            )
        if rejection_reason == "critical_consistency_issues":
            issues = ", ".join(critical_issues)
            return f"Rejected for critical consistency issues: {issues}."
        return (
            "Rejected because product consistency fell below the acceptance threshold. "
            f"Consistency score: {score.product_consistency:.1f}/25."
        )

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
