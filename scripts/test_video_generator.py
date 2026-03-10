"""Standalone VideoGenerator runner."""
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

from agents.video_generator import VideoGenerator


def _load_json_input(raw_value: Optional[str], default: Any) -> Any:
    if not raw_value:
        return default

    candidate = Path(raw_value)
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))

    return json.loads(raw_value)


async def run(
    model: str,
    reference_image: str,
    prompt: str,
    negative_prompt: str = "",
    duration: int = 5,
    product_images: Optional[list[str]] = None,
    additional_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    generator = VideoGenerator()

    if model != "kling":
        raise ValueError(f"Unsupported standalone model: {model}")

    prompt_config = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "additional_params": dict(additional_params or {}),
    }
    result = await generator.generate_kling(
        reference_image=reference_image,
        prompt_config=prompt_config,
        duration=duration,
        reference_images=list(product_images or []),
    )
    return result.to_dict()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test VideoGenerator directly.")
    parser.add_argument("--model", default="kling", help="Video model to run. Currently only kling is supported.")
    parser.add_argument("--reference-image", required=True, help="Start frame image path or URL.")
    parser.add_argument("--prompt", required=True, help="Video generation prompt.")
    parser.add_argument("--negative-prompt", default="", help="Negative prompt.")
    parser.add_argument("--duration", type=int, default=5, help="Target duration in seconds.")
    parser.add_argument(
        "--product-image",
        action="append",
        default=[],
        help="Reference product image path or URL. Repeat for multiple inputs.",
    )
    parser.add_argument("--params-json", help="Inline JSON or JSON file path for additional model params.")
    parser.add_argument("--elements-json", help="Inline JSON or JSON file path for kling elements.")
    parser.add_argument("--aspect-ratio", help="Aspect ratio, for example 9:16.")
    parser.add_argument("--cfg-scale", type=float, help="Kling cfg_scale.")
    parser.add_argument("--shot-type", help="Kling shot_type.")
    parser.add_argument("--end-image", help="Optional ending image path or URL.")
    parser.add_argument(
        "--generate-audio",
        dest="generate_audio",
        action="store_true",
        default=None,
        help="Enable audio generation.",
    )
    parser.add_argument(
        "--no-generate-audio",
        dest="generate_audio",
        action="store_false",
        help="Disable audio generation.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    additional_params = dict(_load_json_input(args.params_json, default={}))
    if args.elements_json:
        additional_params["elements"] = _load_json_input(args.elements_json, default=[])
    if args.aspect_ratio:
        additional_params["aspect_ratio"] = args.aspect_ratio
    if args.cfg_scale is not None:
        additional_params["cfg_scale"] = args.cfg_scale
    if args.shot_type:
        additional_params["shot_type"] = args.shot_type
    if args.end_image:
        additional_params["end_image"] = args.end_image
    if args.generate_audio is not None:
        additional_params["generate_audio"] = args.generate_audio
    additional_params.setdefault("duration", str(args.duration))

    result = asyncio.run(
        run(
            model=args.model,
            reference_image=args.reference_image,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            duration=args.duration,
            product_images=args.product_image,
            additional_params=additional_params,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
