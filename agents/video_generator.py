"""视频生成Agent"""
import asyncio
from typing import Dict, List
from agents.base import BaseAgent
from models.video_result import VideoResult
from tools.video_gen import KlingAPI, SoraAPI, SeedanceAPI, Veo3API
from config.api_keys import api_keys
from config.settings import settings
from utils.logger import get_logger


class VideoGenerator(BaseAgent):
    """视频生成Agent - 并行调用多个视频模型生成视频"""

    def __init__(self):
        super().__init__("VideoGenerator")
        self._init_apis()

    def _init_apis(self):
        """初始化各视频生成API"""
        self.apis = {}

        if api_keys.kling_api_key:
            self.apis["kling"] = KlingAPI()
        if api_keys.sora_api_key or api_keys.openai_api_key:
            self.apis["sora2"] = SoraAPI()
        if api_keys.seedance_api_key:
            self.apis["seedance"] = SeedanceAPI()
        if api_keys.veo3_api_key:
            self.apis["veo3"] = Veo3API()

    async def execute(
        self,
        prompts: Dict[str, Dict],
        reference_image: str,
        duration: int = 4,
    ) -> List[VideoResult]:
        """
        并行生成视频

        Args:
            prompts: 各模型的Prompt配置
            reference_image: 参考图片路径
            duration: 视频时长

        Returns:
            List[VideoResult]: 视频结果列表
        """
        self.log_start(f"Generating videos with {len(self.apis)} models")

        if not self.apis:
            self.logger.warning("No video generation APIs configured")
            return []

        # 创建并行任务
        tasks = []
        for model_name, api in self.apis.items():
            if model_name in prompts:
                task = self._generate_single(model_name, api, prompts[model_name], reference_image, duration)
                tasks.append(task)

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        video_results = []
        for model_name, result in zip(self.apis.keys(), results):
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

            video_path = await api.generate(
                image_path=reference_image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                duration=duration,
            )

            generation_time = time.time() - start_time

            return VideoResult(
                model_name=model_name,
                video_path=video_path,
                prompt_used=prompt,
                duration=duration,
                success=True,
                generation_time=generation_time,
            )

        except Exception as e:
            return VideoResult(
                model_name=model_name,
                video_path="",
                success=False,
                error_message=str(e),
                generation_time=time.time() - start_time,
            )
