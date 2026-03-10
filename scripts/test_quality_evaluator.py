"""Standalone QualityEvaluator runner."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.quality_evaluator import QualityEvaluator
from models.video_result import VideoResult


def _load_json_input(raw_value: Optional[str], default: Any) -> Any:
    if not raw_value:
        return default

    candidate = Path(raw_value)
    if candidate.exists():
        return json.loads(candidate.read_text(encoding="utf-8"))

    return json.loads(raw_value)


def _build_video_results(
    video_paths: Optional[List[str]] = None,
    model_names: Optional[List[str]] = None,
    video_results_data: Optional[List[Dict[str, Any]]] = None,
) -> List[VideoResult]:
    if video_results_data:
        return [
            VideoResult(
                model_name=str(item.get("model_name") or Path(str(item.get("video_path", ""))).stem or f"video_{index + 1}"),
                video_path=str(item.get("video_path", "")),
                prompt_used=str(item.get("prompt_used", "")),
                duration=float(item.get("duration", 0.0) or 0.0),
                resolution=str(item.get("resolution", "")),
                file_size=int(item.get("file_size", 0) or 0),
                generation_time=float(item.get("generation_time", 0.0) or 0.0),
                success=bool(item.get("success", True)),
                error_message=str(item.get("error_message", "")),
                metadata=dict(item.get("metadata", {})),
            )
            for index, item in enumerate(video_results_data)
        ]

    paths = list(video_paths or [])
    names = list(model_names or [])
    if names and len(names) != len(paths):
        raise ValueError("The number of --model-name values must match --video-path values")

    results = []
    for index, video_path in enumerate(paths):
        model_name = names[index] if names else Path(video_path).stem or f"video_{index + 1}"
        results.append(VideoResult(
            model_name=model_name,
            video_path=video_path,
            success=True,
        ))
    return results


async def run(
    product_image: str,
    video_paths: Optional[List[str]] = None,
    model_names: Optional[List[str]] = None,
    video_results_data: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    evaluator = QualityEvaluator()
    video_results = _build_video_results(
        video_paths=video_paths,
        model_names=model_names,
        video_results_data=video_results_data,
    )
    result = await evaluator.execute(
        videos=video_results,
        product_image=product_image,
    )
    return result.to_dict()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test QualityEvaluator directly.")
    parser.add_argument("--product-image", required=True, help="Reference product image path or URL.")
    parser.add_argument(
        "--video-path",
        action="append",
        default=[],
        help="Generated video path or URL. Repeat for multiple inputs.",
    )
    parser.add_argument(
        "--model-name",
        action="append",
        default=[],
        help="Optional model name for each --video-path. Repeat in matching order.",
    )
    parser.add_argument(
        "--video-results-json",
        help="Inline JSON or JSON file path containing a list of serialized VideoResult-like objects.",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args(argv)

    video_results_data = _load_json_input(args.video_results_json, default=None)
    if not args.video_path and not video_results_data:
        parser.error("Provide at least one --video-path or --video-results-json")

    try:
        result = asyncio.run(
            run(
                product_image=args.product_image,
                video_paths=args.video_path,
                model_names=args.model_name,
                video_results_data=video_results_data,
            )
        )
    except ValueError as exc:
        parser.error(str(exc))

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
