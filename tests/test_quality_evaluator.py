import asyncio

from agents.quality_evaluator import QualityEvaluator
from models.video_result import VideoResult


def test_quality_evaluator_prioritizes_product_consistency_over_raw_total(monkeypatch):
    evaluator = QualityEvaluator()

    monkeypatch.setattr(
        evaluator,
        "_extract_keyframes",
        lambda video_path: [f"{video_path}-frame-0.jpg"],
    )

    async def fake_evaluate(product_image, frames, video):
        if video.model_name == "consistent":
            return evaluator._build_evaluation_result(
                model_name=video.model_name,
                video_path="/tmp/consistent.mp4",
                raw_result={
                    "product_consistency": 22,
                    "visual_quality": 18,
                    "creativity": 16,
                    "ad_effectiveness": 15,
                },
            )
        return evaluator._build_evaluation_result(
            model_name=video.model_name,
            video_path="/tmp/flashy.mp4",
            raw_result={
                "product_consistency": 14,
                "visual_quality": 24,
                "creativity": 24,
                "ad_effectiveness": 24,
            },
        )

    monkeypatch.setattr(evaluator, "_evaluate_video", fake_evaluate)

    best = asyncio.run(
        evaluator.execute(
            videos=[
                VideoResult(model_name="flashy", video_path="/tmp/flashy.mp4", success=True),
                VideoResult(model_name="consistent", video_path="/tmp/consistent.mp4", success=True),
            ],
            product_image="/tmp/product.png",
        )
    )

    assert best.model_name == "consistent"
    assert best.is_best is True


def test_quality_evaluator_disqualifies_videos_with_critical_consistency_issues(monkeypatch):
    evaluator = QualityEvaluator()

    monkeypatch.setattr(
        evaluator,
        "_extract_keyframes",
        lambda video_path: [f"{video_path}-frame-0.jpg"],
    )

    async def fake_evaluate(product_image, frames, video):
        if video.model_name == "qualified":
            return evaluator._build_evaluation_result(
                model_name=video.model_name,
                video_path="/tmp/qualified.mp4",
                raw_result={
                    "product_consistency": 20,
                    "visual_quality": 16,
                    "creativity": 16,
                    "ad_effectiveness": 16,
                },
            )
        return evaluator._build_evaluation_result(
            model_name=video.model_name,
            video_path="/tmp/rejected.mp4",
            raw_result={
                "product_consistency": 21,
                "visual_quality": 22,
                "creativity": 20,
                "ad_effectiveness": 20,
                "critical_issues": ["logo missing"],
            },
        )

    monkeypatch.setattr(evaluator, "_evaluate_video", fake_evaluate)

    best = asyncio.run(
        evaluator.execute(
            videos=[
                VideoResult(model_name="rejected", video_path="/tmp/rejected.mp4", success=True),
                VideoResult(model_name="qualified", video_path="/tmp/qualified.mp4", success=True),
            ],
            product_image="/tmp/product.png",
        )
    )

    assert best.model_name == "qualified"
    assert best.metadata["qualified"] is True


def test_quality_evaluator_builds_weighted_metadata_and_comments():
    evaluator = QualityEvaluator()

    evaluation = evaluator._build_evaluation_result(
        model_name="kling",
        video_path="/tmp/test.mp4",
        raw_result={
            "product_consistency": 23,
            "visual_quality": 15,
            "creativity": 14,
            "ad_effectiveness": 13,
            "consistency_checks": {
                "shape_structure": 5,
                "material_finish": 4,
                "primary_color": 5,
                "brand_elements": 4,
                "key_details": 5,
            },
            "summary": "Product identity is stable across all sampled frames.",
        },
    )

    assert evaluation.comments.startswith("Product identity is stable")
    assert evaluation.score.product_consistency == 23.0
    assert evaluation.score.total_score == 65.0
    assert evaluation.metadata["weighted_score"] == 18.95
    assert evaluation.metadata["qualified"] is True
    assert evaluation.metadata["consistency_checks"]["shape_structure"] == 5
