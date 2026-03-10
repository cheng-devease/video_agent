"""视频生成Agent"""
import asyncio
from typing import Dict, List, Optional
from agents.base import BaseAgent
from models.video_result import VideoResult
from tools.video_gen import KlingAPI, SoraAPI, SeedanceAPI, Veo3API
from config.api_keys import api_keys
from config.settings import settings


class VideoGenerator(BaseAgent):
    """视频生成Agent - 并行调用多个视频模型生成视频"""

    def __init__(self):
        super().__init__("VideoGenerator")
        self._init_apis()

    def _init_apis(self):
        """初始化各视频生成API"""
        self.apis = {}

        if api_keys.fal_api_key:
            self.apis["kling"] = KlingAPI()
            self.apis["sora2"] = SoraAPI()
            self.apis["seedance"] = SeedanceAPI()
            self.apis["veo3"] = Veo3API()

    async def execute(
        self,
        prompts: Dict[str, Dict],
        reference_image: str,
        duration: int = 4,
        reference_images: Optional[List[str]] = None,
    ) -> List[VideoResult]:
        """
        并行生成视频

        Args:
            prompts: 各模型的Prompt配置
            reference_image: 参考图片路径
            duration: 视频时长
            reference_images: 附加参考图片列表，用于增强产品一致性

        Returns:
            List[VideoResult]: 视频结果列表
        """
        self.log_start(f"Generating videos with {len(self.apis)} models")

        if not self.apis:
            self.logger.warning("No video generation APIs configured")
            return []

        # 创建并行任务
        task_specs = []
        for model_name, api in self.apis.items():
            if model_name in prompts:
                prompt_config = self._prepare_prompt_config(
                    model_name=model_name,
                    prompt_config=prompts[model_name],
                    reference_images=reference_images,
                )
                task_specs.append((
                    model_name,
                    self._generate_single(model_name, api, prompt_config, reference_image, duration),
                ))

        if not task_specs:
            self.logger.warning("No matching prompt configs for configured video APIs")
            return []

        # 并行执行
        results = await asyncio.gather(*(task for _, task in task_specs), return_exceptions=True)

        # 处理结果
        video_results = []
        for (model_name, _), result in zip(task_specs, results):
            if isinstance(result, Exception):
                self.logger.error(f"{model_name} generation failed: {result}")
                video_results.append(VideoResult(
                    model_name=model_name,
                    video_path="",
                    success=False,
                    error_message=str(result),
                ))
            else:
                video_results.append(result)

        successful = sum(1 for v in video_results if v.success)
        self.log_complete("Video generation", f"{successful}/{len(video_results)} successful")

        return video_results

    async def generate_kling(
        self,
        reference_image: str,
        prompt_config: Dict,
        duration: Optional[int] = None,
        reference_images: Optional[List[str]] = None,
    ) -> VideoResult:
        """独立调用 Kling 生成视频。"""
        api = self.apis.get("kling")
        if api is None:
            return VideoResult(
                model_name="kling",
                video_path="",
                success=False,
                error_message="Kling fal.ai API is not configured",
            )

        effective_duration = duration if duration is not None else int(
            prompt_config.get("additional_params", {}).get("duration", settings.video_default_duration)
        )
        prepared_prompt_config = self._prepare_prompt_config(
            model_name="kling",
            prompt_config=prompt_config,
            reference_images=reference_images,
        )
        return await self._generate_single("kling", api, prepared_prompt_config, reference_image, effective_duration)

    async def _generate_single(
        self,
        model_name: str,
        api,
        prompt_config: Dict,
        reference_image: str,
        duration: int,
    ) -> VideoResult:
        """生成单个视频"""
        import time

        start_time = time.time()

        try:
            prompt = prompt_config.get("prompt", "") or prompt_config.get("full_prompt", "")
            negative_prompt = prompt_config.get("negative_prompt", "")
            additional_params = dict(prompt_config.get("additional_params", {}))
            effective_duration = int(additional_params.get("duration", duration))

            generate_kwargs = dict(
                image_path=reference_image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                duration=effective_duration,
            )
            if additional_params:
                generate_kwargs["additional_params"] = additional_params

            video_path = await api.generate(**generate_kwargs)

            generation_time = time.time() - start_time

            return VideoResult(
                model_name=model_name,
                video_path=video_path,
                prompt_used=prompt,
                duration=effective_duration,
                success=True,
                generation_time=generation_time,
                metadata={"additional_params": additional_params} if additional_params else {},
            )

        except Exception as e:
            return VideoResult(
                model_name=model_name,
                video_path="",
                success=False,
                error_message=str(e),
                generation_time=time.time() - start_time,
            )

    def _prepare_prompt_config(
        self,
        model_name: str,
        prompt_config: Dict,
        reference_images: Optional[List[str]] = None,
    ) -> Dict:
        prepared = dict(prompt_config)
        prompt = prepared.get("prompt", "") or prepared.get("full_prompt", "")
        additional_params = dict(prepared.get("additional_params", {}))

        if model_name == "kling" and reference_images:
            additional_params = self._inject_kling_product_references(additional_params, reference_images)
            if additional_params.get("elements") and "@Element1" not in prompt:
                prompt = (
                    f"{prompt.rstrip()} Preserve the product identity and appearance of @Element1."
                    if prompt.strip()
                    else "Preserve the product identity and appearance of @Element1."
                )

        if prompt:
            prepared["prompt"] = prompt
        prepared["additional_params"] = additional_params
        return prepared

    def _inject_kling_product_references(
        self,
        additional_params: Dict,
        reference_images: List[str],
    ) -> Dict:
        prepared_params = dict(additional_params)
        elements = [dict(element) for element in prepared_params.get("elements", [])]

        legacy_reference_images = (
            prepared_params.pop("reference_image_urls", None)
            or prepared_params.pop("reference_images", None)
            or []
        )
        merged_images: List[str] = []
        for image in list(legacy_reference_images) + list(reference_images):
            if image and image not in merged_images:
                merged_images.append(image)

        if not merged_images:
            prepared_params["elements"] = elements
            return prepared_params

        if elements:
            first_element = dict(elements[0])
            frontal_image = (
                first_element.get("frontal_image_url")
                or first_element.get("frontal_image")
                or first_element.get("frontal_image_path")
            )
            existing_refs = (
                first_element.get("reference_image_urls")
                or first_element.get("reference_images")
                or []
            )

            if not frontal_image:
                frontal_image = merged_images[0]

            merged_refs: List[str] = []
            for image in list(existing_refs) + merged_images:
                if image and image != frontal_image and image not in merged_refs:
                    merged_refs.append(image)

            first_element["frontal_image_url"] = frontal_image
            first_element["reference_image_urls"] = merged_refs
            first_element.pop("frontal_image", None)
            first_element.pop("frontal_image_path", None)
            first_element.pop("reference_images", None)
            elements[0] = first_element
        else:
            frontal_image = merged_images[0]
            ref_images = [image for image in merged_images[1:] if image != frontal_image]
            elements = [{
                "frontal_image_url": frontal_image,
                "reference_image_urls": ref_images,
            }]

        prepared_params["elements"] = elements
        return prepared_params
