import asyncio

from agents.video_editor import EditConfig, VideoEditor
from models.video_result import VideoResult
from tools.video_edit import KlingVideoEditAPI


class DummyKlingVideoEditAPI:
    def __init__(self):
        self.calls = []

    async def edit(self, **kwargs):
        self.calls.append(kwargs)
        return "/tmp/edited-video.mp4"


def test_kling_video_edit_builds_payload_with_all_supported_inputs(tmp_path):
    video = tmp_path / "input.mp4"
    style = tmp_path / "style.png"
    front = tmp_path / "front.png"
    ref = tmp_path / "ref.png"

    video.write_bytes(b"video-bytes")
    style.write_bytes(b"style-bytes")
    front.write_bytes(b"front-bytes")
    ref.write_bytes(b"ref-bytes")

    api = KlingVideoEditAPI()
    payload = api._build_payload(
        video_path=str(video),
        prompt="Restyle @Video1 with the luxury lighting of @Image1 and replace the object with @Element1",
        additional_params={
            "image_urls": [str(style)],
            "keep_audio": False,
            "shot_type": "customize",
            "elements": [
                {
                    "frontal_image": str(front),
                    "reference_images": [str(ref)],
                }
            ],
        },
    )

    assert payload["prompt"].startswith("Restyle @Video1")
    assert payload["video_url"].startswith("data:video/mp4;base64,")
    assert payload["image_urls"][0].startswith("data:image/png;base64,")
    assert payload["keep_audio"] is False
    assert payload["shot_type"] == "customize"
    assert payload["elements"][0]["frontal_image_url"].startswith("data:image/png;base64,")
    assert payload["elements"][0]["reference_image_urls"][0].startswith("data:image/png;base64,")


def test_video_editor_passes_all_ai_edit_params():
    editor = VideoEditor()
    dummy_api = DummyKlingVideoEditAPI()
    editor.editor = dummy_api

    result = asyncio.run(
        editor.execute(
            video=VideoResult(
                model_name="kling",
                video_path="/tmp/source.mp4",
                success=True,
                prompt_used="Original i2v prompt",
            ),
            config=EditConfig(
                prompt="Turn this into a sharper premium ad cut",
                image_urls=["https://example.com/style.png"],
                keep_audio=False,
                shot_type="customize",
                elements=[
                    {
                        "frontal_image_url": "https://example.com/front.png",
                        "reference_image_urls": ["https://example.com/ref.png"],
                    }
                ],
            ),
        )
    )

    assert result == "/tmp/edited-video.mp4"
    assert dummy_api.calls[0]["video_path"] == "/tmp/source.mp4"
    assert dummy_api.calls[0]["prompt"] == "Turn this into a sharper premium ad cut"
    assert dummy_api.calls[0]["additional_params"]["keep_audio"] is False
    assert dummy_api.calls[0]["additional_params"]["shot_type"] == "customize"
    assert dummy_api.calls[0]["additional_params"]["elements"][0]["frontal_image_url"] == "https://example.com/front.png"


def test_video_editor_supports_standalone_editing_and_default_prompt():
    editor = VideoEditor()
    dummy_api = DummyKlingVideoEditAPI()
    editor.editor = dummy_api

    result = asyncio.run(
        editor.edit_video(
            video_path="/tmp/source.mp4",
            prompt="",
            additional_params={
                "image_urls": ["https://example.com/style.png"],
                "keep_audio": True,
            },
            source_prompt="Original i2v prompt about product reveal",
        )
    )

    assert result == "/tmp/edited-video.mp4"
    assert "Original i2v prompt about product reveal" in dummy_api.calls[0]["prompt"]
    assert dummy_api.calls[0]["additional_params"]["keep_audio"] is True
