import asyncio

from agents.scene_generator import SceneGenerator
from models.creative_plan import CreativePlan, ScenePrompt
from models.product_info import ProductInfo
from tools.image_gen import NanoBananaEditTool


class DummyNanoBananaTool:
    def __init__(self):
        self.calls = []

    async def edit(self, **kwargs):
        self.calls.append(kwargs)
        return "/tmp/generated-scene.png"


def test_nano_banana_builds_payload_with_multiple_product_images(tmp_path):
    product_1 = tmp_path / "product-1.png"
    product_2 = tmp_path / "product-2.png"
    product_1.write_bytes(b"product-1")
    product_2.write_bytes(b"product-2")

    tool = NanoBananaEditTool()
    payload = tool._build_payload(
        prompt="Create a premium first-frame product composition.",
        image_paths=[str(product_1), str(product_2)],
        additional_params={
            "aspect_ratio": "16:9",
            "num_images": 1,
            "resolution": "1K",
            "output_format": "png",
            "limit_generations": True,
            "enable_web_search": False,
        },
    )

    assert payload["prompt"].startswith("Create a premium first-frame")
    assert len(payload["image_urls"]) == 2
    assert payload["image_urls"][0].startswith("data:image/png;base64,")
    assert payload["image_urls"][1].startswith("data:image/png;base64,")
    assert payload["aspect_ratio"] == "16:9"
    assert payload["num_images"] == 1
    assert payload["limit_generations"] is True
    assert payload["enable_web_search"] is False


def test_scene_generator_uses_system_prompt_product_info_and_all_product_images():
    generator = SceneGenerator()
    dummy_tool = DummyNanoBananaTool()
    generator.image_tool = dummy_tool
    generator.system_prompt = "Keep the hero product perfectly consistent with the references."

    creative_plan = CreativePlan(
        ad_style="premium tech",
        emotional_tone="clean and futuristic",
        hook_strategy="hero reveal",
        scenes=[
            ScenePrompt(
                scene_id=1,
                scene_name="Hero Countertop",
                image_prompt="A premium countertop scene with dramatic highlights",
                video_prompt_hint="Slow push in with stable hero framing",
            )
        ],
    )
    product_info = ProductInfo(
        product_type="serum bottle",
        product_name="Aurora Serum",
        material="glass",
        color_palette=["silver", "white"],
        shape_description="tall cylindrical bottle with rounded cap",
        selling_points=["premium hydration"],
    )

    results = asyncio.run(
        generator.execute(
            creative_plan=creative_plan,
            product_images=[
                "https://example.com/product-front.png",
                "https://example.com/product-side.png",
                "https://example.com/product-detail.png",
            ],
            product_info=product_info,
        )
    )

    assert results == ["/tmp/generated-scene.png"]
    assert len(dummy_tool.calls) == 1
    call = dummy_tool.calls[0]
    assert call["image_paths"] == [
        "https://example.com/product-front.png",
        "https://example.com/product-side.png",
        "https://example.com/product-detail.png",
    ]
    assert "Keep the hero product perfectly consistent" in call["prompt"]
    assert '"product_name": "Aurora Serum"' in call["prompt"]
    assert "A premium countertop scene with dramatic highlights" in call["prompt"]
    assert "Slow push in with stable hero framing" in call["prompt"]
    assert call["additional_params"]["aspect_ratio"] == "16:9"
    assert call["additional_params"]["num_images"] == 1
    assert call["additional_params"]["enable_web_search"] is False
