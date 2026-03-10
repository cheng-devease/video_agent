from tools.video_gen import KlingAPI


def test_kling_builds_fal_payload_from_prompt_and_additional_params(tmp_path):
    start_image = tmp_path / "start.png"
    end_image = tmp_path / "end.png"
    element_image = tmp_path / "element.png"

    start_image.write_bytes(b"start-image")
    end_image.write_bytes(b"end-image")
    element_image.write_bytes(b"element-image")

    api = KlingAPI()
    payload = api._build_payload(
        image_path=str(start_image),
        prompt="A premium product reveal",
        negative_prompt="blurry, low quality",
        duration=10,
        additional_params={
            "aspect_ratio": "9:16",
            "generate_audio": True,
            "cfg_scale": 0.7,
            "voice_ids": ["voice_1"],
            "shot_type": "close_up",
            "end_image": str(end_image),
            "elements": [
                {
                    "type": "subject",
                    "image": str(element_image),
                }
            ],
        },
    )

    assert payload["prompt"] == "A premium product reveal"
    assert payload["negative_prompt"] == "blurry, low quality"
    assert payload["duration"] == "10"
    assert payload["aspect_ratio"] == "9:16"
    assert payload["generate_audio"] is True
    assert payload["cfg_scale"] == 0.7
    assert payload["voice_ids"] == ["voice_1"]
    assert payload["shot_type"] == "close_up"
    assert payload["start_image_url"].startswith("data:image/png;base64,")
    assert payload["end_image_url"].startswith("data:image/png;base64,")
    assert payload["elements"][0]["type"] == "subject"
    assert payload["elements"][0]["image_url"].startswith("data:image/png;base64,")
