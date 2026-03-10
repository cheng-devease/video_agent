import asyncio

from agents.prompt_generator import PromptGenerator
from models.creative_plan import CreativePlan


class DummyVisionTool:
    def __init__(self, response):
        self.response = response
        self.calls = []

    async def analyze_images_json(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def test_prompt_generator_uses_system_prompt_file_and_normalizes_outputs(tmp_path):
    scene_image = tmp_path / "scene.jpg"
    product_image = tmp_path / "product.jpg"
    scene_image.write_bytes(b"scene")
    product_image.write_bytes(b"product")

    generator = PromptGenerator()
    dummy_tool = DummyVisionTool(
        {
            "model_prompts": {
                "kling": {
                    "prompt": {
                        "Subject Description": "Premium silver bottle",
                        "Subject Movement": "slow controlled turn",
                        "Scene Setting": "clean luxury bathroom counter",
                        "Additional Scene Elements": "small water droplets",
                        "Camera Movement": "slow push in",
                        "Lighting and Mood": "soft cinematic rim light",
                    },
                    "negative_prompt": "blurry, distorted",
                    "generation_params": {
                        "aspect_ratio": "9:16",
                        "duration": "10",
                        "generate_audio": False,
                    },
                },
                "sora2": {
                    "prompt": "A refined close-up studio shot.",
                    "dialogue_block": "",
                    "audio_description": "quiet studio ambience",
                    "generation_params": {
                        "aspect_ratio": "16:9",
                        "duration": "5",
                    },
                },
                "seedance": {
                    "prompt": {
                        "subject": "Bottle in center frame",
                        "action": "cap opens smoothly",
                        "camera": "locked macro shot",
                        "scene": "bright countertop setup",
                        "style": "premium ad realism",
                        "constraints": "keep product geometry stable",
                    },
                    "generation_params": {
                        "duration": "5",
                        "camera_fixed": True,
                    },
                },
                "veo3": {
                    "full_prompt": "Cinematic product reveal with soft reflections.",
                    "generation_params": {
                        "duration": "6",
                        "resolution": "1080p",
                    },
                },
            }
        }
    )
    generator.vision_tool = dummy_tool

    result = asyncio.run(
        generator.execute(
            scene_image=str(scene_image),
            product_image=str(product_image),
            creative_plan=CreativePlan(
                ad_style="高端科技风格",
                emotional_tone="clean and premium",
                hook_strategy="slow reveal",
            ),
        )
    )

    assert "图生视频4秒Hook广告提示词生成系统" in dummy_tool.calls[0]["system_prompt"]
    assert result["kling"]["prompt"].startswith("Premium silver bottle")
    assert result["kling"]["negative_prompt"] == "blurry, distorted"
    assert result["kling"]["additional_params"]["aspect_ratio"] == "9:16"
    assert result["kling"]["additional_params"]["duration"] == "10"

    assert result["sora2"]["prompt"].startswith("A refined close-up studio shot.")
    assert result["sora2"]["additional_params"]["aspect_ratio"] == "16:9"

    assert "Bottle in center frame" in result["seedance"]["prompt"]
    assert result["seedance"]["additional_params"]["camera_fixed"] is True

    assert result["veo3"]["prompt"] == "Cinematic product reveal with soft reflections."
    assert result["veo3"]["additional_params"]["resolution"] == "1080p"
