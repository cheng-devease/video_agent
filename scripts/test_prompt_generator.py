"""Standalone PromptGenerator runner."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.prompt_generator import PromptGenerator
from models.creative_plan import CreativePlan


def _load_json_input(raw_value: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw_value:
        return None

    candidate = Path(raw_value)
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))

    return json.loads(raw_value)


def _build_creative_plan(
    creative_plan_data: Optional[Dict[str, Any]],
    ad_style: str,
    visual_style_reference: str,
    scene_concept: str,
    emotional_tone: str,
    hook_strategy: str,
    user_requirements: str,
    background_music_style: str,
) -> CreativePlan:
    if creative_plan_data:
        return CreativePlan.from_dict(creative_plan_data)

    return CreativePlan(
        ad_style=ad_style,
        visual_style_reference=visual_style_reference,
        scene_concept=scene_concept,
        emotional_tone=emotional_tone,
        hook_strategy=hook_strategy,
        user_requirements=user_requirements or None,
        background_music_style=background_music_style,
    )


async def run(
    scene_image: str,
    product_image: str,
    creative_plan_data: Optional[Dict[str, Any]] = None,
    ad_style: str = "",
    visual_style_reference: str = "",
    scene_concept: str = "",
    emotional_tone: str = "",
    hook_strategy: str = "",
    user_requirements: str = "",
    background_music_style: str = "",
) -> Dict[str, Any]:
    generator = PromptGenerator()
    creative_plan = _build_creative_plan(
        creative_plan_data=creative_plan_data,
        ad_style=ad_style,
        visual_style_reference=visual_style_reference,
        scene_concept=scene_concept,
        emotional_tone=emotional_tone,
        hook_strategy=hook_strategy,
        user_requirements=user_requirements,
        background_music_style=background_music_style,
    )
    return await generator.execute(
        scene_image=scene_image,
        product_image=product_image,
        creative_plan=creative_plan,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test PromptGenerator directly.")
    parser.add_argument("--scene-image", required=True, help="Scene image path or URL.")
    parser.add_argument("--product-image", required=True, help="Product image path or URL.")
    parser.add_argument(
        "--creative-plan-json",
        help="Inline creative plan JSON or a path to a JSON file.",
    )
    parser.add_argument("--ad-style", default="", help="Creative plan ad style.")
    parser.add_argument("--visual-style-reference", default="", help="Visual style reference.")
    parser.add_argument("--scene-concept", default="", help="Scene concept.")
    parser.add_argument("--emotional-tone", default="", help="Emotional tone.")
    parser.add_argument("--hook-strategy", default="", help="Hook strategy.")
    parser.add_argument("--user-requirements", default="", help="Extra user requirements.")
    parser.add_argument("--background-music-style", default="", help="Background music style.")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    creative_plan_data = _load_json_input(args.creative_plan_json)
    result = asyncio.run(
        run(
            scene_image=args.scene_image,
            product_image=args.product_image,
            creative_plan_data=creative_plan_data,
            ad_style=args.ad_style,
            visual_style_reference=args.visual_style_reference,
            scene_concept=args.scene_concept,
            emotional_tone=args.emotional_tone,
            hook_strategy=args.hook_strategy,
            user_requirements=args.user_requirements,
            background_music_style=args.background_music_style,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
