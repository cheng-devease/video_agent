"""Standalone VideoEditor runner."""
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

from agents.video_editor import VideoEditor


def _load_json_input(raw_value: Optional[str], default: Any) -> Any:
    if not raw_value:
        return default

    candidate = Path(raw_value)
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))

    return json.loads(raw_value)


async def run(
    video_path: str,
    prompt: str = "",
    source_prompt: str = "",
    additional_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    editor = VideoEditor()
    edited_video_path = await editor.edit_video(
        video_path=video_path,
        prompt=prompt,
        additional_params=dict(additional_params or {}),
        source_prompt=source_prompt,
    )
    return {
        "source_video_path": video_path,
        "edited_video_path": edited_video_path,
        "prompt": prompt,
        "source_prompt": source_prompt,
        "additional_params": dict(additional_params or {}),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test VideoEditor directly.")
    parser.add_argument("--video-path", required=True, help="Source video path or URL.")
    parser.add_argument("--prompt", default="", help="Edit prompt.")
    parser.add_argument("--source-prompt", default="", help="Original generation prompt.")
    parser.add_argument(
        "--image-url",
        action="append",
        default=[],
        help="Reference style image path or URL. Repeat for multiple inputs.",
    )
    parser.add_argument("--params-json", help="Inline JSON or JSON file path for extra edit params.")
    parser.add_argument("--elements-json", help="Inline JSON or JSON file path for elements.")
    parser.add_argument("--shot-type", default="customize", help="Edit shot_type.")
    parser.add_argument(
        "--keep-audio",
        dest="keep_audio",
        action="store_true",
        default=True,
        help="Keep source audio.",
    )
    parser.add_argument(
        "--no-keep-audio",
        dest="keep_audio",
        action="store_false",
        help="Remove source audio.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    additional_params = dict(_load_json_input(args.params_json, default={}))
    if args.image_url:
        additional_params["image_urls"] = args.image_url
    if args.elements_json:
        additional_params["elements"] = _load_json_input(args.elements_json, default=[])
    additional_params["keep_audio"] = args.keep_audio
    additional_params["shot_type"] = args.shot_type

    result = asyncio.run(
        run(
            video_path=args.video_path,
            prompt=args.prompt,
            source_prompt=args.source_prompt,
            additional_params=additional_params,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
