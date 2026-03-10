import asyncio
import json

from models.video_result import EvaluationResult, EvaluationScore, VideoResult
from scripts import test_prompt_generator, test_quality_evaluator, test_video_editor, test_video_generator


def test_prompt_generator_script_main_prints_json(monkeypatch, capsys, tmp_path):
    scene_image = tmp_path / "scene.jpg"
    product_image = tmp_path / "product.jpg"
    scene_image.write_bytes(b"scene")
    product_image.write_bytes(b"product")

    async def fake_run(**kwargs):
        assert kwargs["scene_image"] == str(scene_image)
        assert kwargs["product_image"] == str(product_image)
        assert kwargs["ad_style"] == "高端科技风格"
        return {"kling": {"prompt": "test prompt", "additional_params": {}}}

    monkeypatch.setattr(test_prompt_generator, "run", fake_run)

    exit_code = test_prompt_generator.main([
        "--scene-image",
        str(scene_image),
        "--product-image",
        str(product_image),
        "--ad-style",
        "高端科技风格",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["kling"]["prompt"] == "test prompt"


def test_video_generator_script_run_calls_kling_with_all_params(monkeypatch):
    calls = []

    class DummyGenerator:
        async def generate_kling(self, **kwargs):
            calls.append(kwargs)
            return VideoResult(
                model_name="kling",
                video_path="/tmp/generated.mp4",
                prompt_used=kwargs["prompt_config"]["prompt"],
                success=True,
                metadata={"additional_params": kwargs["prompt_config"]["additional_params"]},
            )

    monkeypatch.setattr(test_video_generator, "VideoGenerator", DummyGenerator)

    result = asyncio.run(
        test_video_generator.run(
            model="kling",
            reference_image="/tmp/scene.png",
            prompt="Premium product reveal",
            negative_prompt="distorted",
            duration=5,
            product_images=["/tmp/product-1.png", "/tmp/product-2.png"],
            additional_params={
                "aspect_ratio": "9:16",
                "cfg_scale": 0.8,
            },
        )
    )

    assert result["video_path"] == "/tmp/generated.mp4"
    assert calls[0]["reference_image"] == "/tmp/scene.png"
    assert calls[0]["reference_images"] == ["/tmp/product-1.png", "/tmp/product-2.png"]
    assert calls[0]["prompt_config"]["additional_params"]["aspect_ratio"] == "9:16"
    assert calls[0]["prompt_config"]["additional_params"]["cfg_scale"] == 0.8


def test_video_generator_script_main_prints_json(monkeypatch, capsys, tmp_path):
    reference_image = tmp_path / "scene.png"
    product_image = tmp_path / "product.png"
    reference_image.write_bytes(b"scene")
    product_image.write_bytes(b"product")

    async def fake_run(**kwargs):
        assert kwargs["reference_image"] == str(reference_image)
        assert kwargs["product_images"] == [str(product_image)]
        return {
            "model_name": "kling",
            "video_path": "/tmp/generated.mp4",
            "success": True,
        }

    monkeypatch.setattr(test_video_generator, "run", fake_run)

    exit_code = test_video_generator.main([
        "--reference-image",
        str(reference_image),
        "--prompt",
        "Premium product reveal",
        "--product-image",
        str(product_image),
        "--aspect-ratio",
        "9:16",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["video_path"] == "/tmp/generated.mp4"


def test_video_editor_script_run_passes_all_params(monkeypatch):
    calls = []

    class DummyEditor:
        async def edit_video(self, **kwargs):
            calls.append(kwargs)
            return "/tmp/edited.mp4"

    monkeypatch.setattr(test_video_editor, "VideoEditor", DummyEditor)

    result = asyncio.run(
        test_video_editor.run(
            video_path="/tmp/input.mp4",
            prompt="Turn this into a stronger premium edit",
            source_prompt="Original product reveal",
            additional_params={
                "image_urls": ["/tmp/style.png"],
                "keep_audio": False,
                "shot_type": "customize",
                "elements": [
                    {
                        "frontal_image_url": "/tmp/front.png",
                        "reference_image_urls": ["/tmp/ref.png"],
                    }
                ],
            },
        )
    )

    assert result["edited_video_path"] == "/tmp/edited.mp4"
    assert calls[0]["video_path"] == "/tmp/input.mp4"
    assert calls[0]["prompt"] == "Turn this into a stronger premium edit"
    assert calls[0]["source_prompt"] == "Original product reveal"
    assert calls[0]["additional_params"]["keep_audio"] is False


def test_video_editor_script_main_prints_json(monkeypatch, capsys, tmp_path):
    video_path = tmp_path / "input.mp4"
    video_path.write_bytes(b"video")

    async def fake_run(**kwargs):
        assert kwargs["video_path"] == str(video_path)
        return {"edited_video_path": "/tmp/edited.mp4"}

    monkeypatch.setattr(test_video_editor, "run", fake_run)

    exit_code = test_video_editor.main([
        "--video-path",
        str(video_path),
        "--prompt",
        "Turn this into a stronger premium edit",
        "--no-keep-audio",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["edited_video_path"] == "/tmp/edited.mp4"


def test_quality_evaluator_script_run_passes_video_results(monkeypatch):
    calls = []

    class DummyEvaluator:
        async def execute(self, videos, product_image):
            calls.append({
                "videos": videos,
                "product_image": product_image,
            })
            return EvaluationResult(
                model_name="kling",
                video_path="/tmp/best.mp4",
                score=EvaluationScore(
                    product_consistency=22,
                    visual_quality=16,
                    creativity=15,
                    ad_effectiveness=14,
                ),
                comments="Best match",
                is_best=True,
                metadata={"weighted_score": 18.7, "qualified": True},
            )

    monkeypatch.setattr(test_quality_evaluator, "QualityEvaluator", DummyEvaluator)

    result = asyncio.run(
        test_quality_evaluator.run(
            product_image="/tmp/product.png",
            video_paths=["/tmp/a.mp4", "/tmp/b.mp4"],
            model_names=["sora2", "kling"],
        )
    )

    assert result["model_name"] == "kling"
    assert calls[0]["product_image"] == "/tmp/product.png"
    assert calls[0]["videos"][0].model_name == "sora2"
    assert calls[0]["videos"][1].video_path == "/tmp/b.mp4"


def test_quality_evaluator_script_main_prints_json(monkeypatch, capsys, tmp_path):
    product_image = tmp_path / "product.png"
    video_path = tmp_path / "video.mp4"
    product_image.write_bytes(b"product")
    video_path.write_bytes(b"video")

    async def fake_run(**kwargs):
        assert kwargs["product_image"] == str(product_image)
        assert kwargs["video_paths"] == [str(video_path)]
        assert kwargs["model_names"] == ["kling"]
        return {"model_name": "kling", "video_path": "/tmp/best.mp4", "is_best": True}

    monkeypatch.setattr(test_quality_evaluator, "run", fake_run)

    exit_code = test_quality_evaluator.main([
        "--product-image",
        str(product_image),
        "--video-path",
        str(video_path),
        "--model-name",
        "kling",
    ])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["video_path"] == "/tmp/best.mp4"
