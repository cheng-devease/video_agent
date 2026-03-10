"""质量评估Agent"""
from typing import List
from agents.base import BaseAgent
from models.video_result import VideoResult, EvaluationResult, EvaluationScore
from tools.llm import GPT4VisionTool
from tools.video_edit import MoviePyEditor
from config.prompts import prompts
from config.settings import settings


class QualityEvaluator(BaseAgent):
    """质量评估Agent - 评估视频质量并选择最佳"""

    def __init__(self):
        super().__init__("QualityEvaluator")
        self.vision_tool = GPT4VisionTool()
        self.video_editor = MoviePyEditor()

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
                score = await self._evaluate_video(product_image, frames, video.model_name)

                evaluations.append(EvaluationResult(
                    model_name=video.model_name,
                    video_path=video.video_path,
                    score=score,
                ))

            except Exception as e:
                self.log_error(f"Evaluating {video.model_name}", e)
                evaluations.append(EvaluationResult(
                    model_name=video.model_name,
                    video_path=video.video_path,
                    score=EvaluationScore(),
                ))

        # 排序并选择最佳
        evaluations.sort(key=lambda e: e.score.total_score, reverse=True)

        for i, ev in enumerate(evaluations):
            ev.ranking = i + 1
            if i == 0:
                ev.is_best = True

        best = evaluations[0] if evaluations else None

        self.log_complete(
            "Quality evaluation",
            f"Best: {best.model_name if best else 'none'} (Score: {best.score.total_score if best else 0})",
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
        model_name: str,
    ) -> EvaluationScore:
        """评估单个视频"""
        system_prompt, user_prompt = prompts.get_quality_evaluator_prompts()

        try:
            result = await self.vision_tool.analyze_images_json(
                image_paths=[product_image] + frames,
                prompt=user_prompt,
                system_prompt=system_prompt,
            )

            return EvaluationScore(
                product_consistency=float(result.get("product_consistency", 0)),
                visual_quality=float(result.get("visual_quality", 0)),
                creativity=float(result.get("creativity", 0)),
                ad_effectiveness=float(result.get("ad_effectiveness", 0)),
            )

        except Exception as e:
            self.log_error(f"Scoring {model_name}", e)
            return EvaluationScore()
