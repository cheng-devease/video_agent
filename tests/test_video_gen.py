from tools.video_gen import KlingAPI, SeedanceAPI, SoraAPI, Veo3API


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


def test_other_fal_video_models_use_expected_model_ids_and_payloads(tmp_path):
    image = tmp_path / "start.png"
    image.write_bytes(b"start-image")

    sora_payload = SoraAPI()._build_payload(
        image_path=str(image),
        prompt="A polished studio demo",
        duration=5,
        additional_params={"aspect_ratio": "16:9", "generate_audio": False},
    )
    seedance_payload = SeedanceAPI()._build_payload(
        image_path=str(image),
        prompt="A dynamic product shot",
        duration=5,
        additional_params={"camera_fixed": True},
    )
    veo_payload = Veo3API()._build_payload(
        image_path=str(image),
        prompt="A cinematic premium reveal",
        duration=5,
        additional_params={"resolution": "1080p"},
    )

    assert SoraAPI.model_id == "fal-ai/sora-2/image-to-video"
    assert SeedanceAPI.model_id == "fal-ai/bytedance/seedance/v1.5/pro/image-to-video"
    assert Veo3API.model_id == "fal-ai/veo3.1/image-to-video"

    assert sora_payload["image_url"].startswith("data:image/png;base64,")
    assert sora_payload["prompt"] == "A polished studio demo"
    assert sora_payload["aspect_ratio"] == "16:9"
    assert sora_payload["generate_audio"] is False

    assert seedance_payload["image_url"].startswith("data:image/png;base64,")
    assert seedance_payload["prompt"] == "A dynamic product shot"
    assert seedance_payload["camera_fixed"] is True

    assert veo_payload["image_url"].startswith("data:image/png;base64,")
    assert veo_payload["prompt"] == "A cinematic premium reveal"
    assert veo_payload["resolution"] == "1080p"


def test_kling_prefers_submit_returned_queue_urls():
    api = KlingAPI()
    submit_result = {
        "request_id": "req_123",
        "status_url": "https://queue.fal.run/fal-ai/kling-video/requests/req_123/status",
        "response_url": "https://queue.fal.run/fal-ai/kling-video/requests/req_123",
    }

    urls = api._resolve_queue_urls(submit_result)

    assert urls["request_id"] == "req_123"
    assert urls["status_url"] == "https://queue.fal.run/fal-ai/kling-video/requests/req_123/status"
    assert urls["response_url"] == "https://queue.fal.run/fal-ai/kling-video/requests/req_123"
