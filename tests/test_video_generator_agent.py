import asyncio

from agents.video_generator import VideoGenerator


class DummyKlingAPI:
    def __init__(self):
        self.calls = []

    async def generate(self, **kwargs):
        self.calls.append(kwargs)
        return "/tmp/generated-kling.mp4"


def test_video_generator_passes_kling_additional_params():
    generator = VideoGenerator()
    dummy_api = DummyKlingAPI()
    generator.apis = {"kling": dummy_api}

    results = asyncio.run(
        generator.execute(
            prompts={
                "kling": {
                    "prompt": "Fast camera push-in on the product",
                    "negative_prompt": "distorted, shaky",
                    "additional_params": {
                        "aspect_ratio": "9:16",
                        "generate_audio": False,
                        "cfg_scale": 0.9,
                    },
                }
            },
            reference_image="https://example.com/product.png",
            duration=5,
        )
    )

    assert len(results) == 1
    assert results[0].success is True
    assert dummy_api.calls[0]["additional_params"]["aspect_ratio"] == "9:16"
    assert dummy_api.calls[0]["additional_params"]["generate_audio"] is False
    assert dummy_api.calls[0]["additional_params"]["cfg_scale"] == 0.9


def test_video_generator_can_run_standalone_for_kling_only():
    generator = VideoGenerator()
    dummy_api = DummyKlingAPI()
    generator.apis = {"kling": dummy_api}

    result = asyncio.run(
        generator.generate_kling(
            reference_image="https://example.com/product.png",
            prompt_config={
                "prompt": "Hero shot with cinematic lighting",
                "negative_prompt": "artifacts",
                "additional_params": {
                    "duration": "10",
                    "aspect_ratio": "16:9",
                },
            },
        )
    )

    assert result.success is True
    assert result.model_name == "kling"
    assert result.video_path == "/tmp/generated-kling.mp4"
    assert dummy_api.calls[0]["duration"] == 10
    assert dummy_api.calls[0]["additional_params"]["aspect_ratio"] == "16:9"


def test_video_generator_injects_all_reference_images_for_kling():
    generator = VideoGenerator()
    dummy_api = DummyKlingAPI()
    generator.apis = {"kling": dummy_api}

    results = asyncio.run(
        generator.execute(
            prompts={
                "kling": {
                    "prompt": "Hero product close-up with stable identity",
                    "negative_prompt": "distorted",
                    "additional_params": {
                        "aspect_ratio": "9:16",
                    },
                }
            },
            reference_image="https://example.com/scene.png",
            duration=5,
            reference_images=[
                "https://example.com/product-1.png",
                "https://example.com/product-2.png",
            ],
        )
    )

    assert len(results) == 1
    assert results[0].success is True
    assert "@Element1" in dummy_api.calls[0]["prompt"]
    assert dummy_api.calls[0]["additional_params"]["elements"][0]["frontal_image_url"] == "https://example.com/product-1.png"
    assert dummy_api.calls[0]["additional_params"]["elements"][0]["reference_image_urls"] == [
        "https://example.com/product-2.png",
    ]


def test_generate_kling_merges_explicit_and_existing_reference_images():
    generator = VideoGenerator()
    dummy_api = DummyKlingAPI()
    generator.apis = {"kling": dummy_api}

    result = asyncio.run(
        generator.generate_kling(
            reference_image="https://example.com/scene.png",
            prompt_config={
                "prompt": "Premium product reveal",
                "additional_params": {
                    "elements": [
                        {
                            "frontal_image_url": "https://example.com/product-1.png",
                            "reference_image_urls": [
                                "https://example.com/product-2.png",
                            ],
                        }
                    ],
                },
            },
            reference_images=[
                "https://example.com/product-1.png",
                "https://example.com/product-2.png",
                "https://example.com/product-3.png",
            ],
        )
    )

    assert result.success is True
    assert "@Element1" in dummy_api.calls[0]["prompt"]
    assert dummy_api.calls[0]["additional_params"]["elements"][0]["frontal_image_url"] == "https://example.com/product-1.png"
    assert dummy_api.calls[0]["additional_params"]["elements"][0]["reference_image_urls"] == [
        "https://example.com/product-2.png",
        "https://example.com/product-3.png",
    ]
