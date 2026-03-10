"""工作流编排器"""
import uuid
from typing import List, Optional
from datetime import datetime

from models.product_info import ProductInfo
from models.creative_plan import CreativePlan
from models.video_result import VideoResult, EvaluationResult
from models.workflow_state import WorkflowState, WorkflowStatus
from orchestrator.state_manager import StateManager
from agents import (
    ProductAnalyzer,
    CreativePlanner,
    SceneGenerator,
    PromptGenerator,
    VideoGenerator,
    QualityEvaluator,
    VideoEditor,
    BrandComposer,
)
from agents.brand_composer import BrandAssets
from utils.logger import get_logger
from utils.context_manager import ContextManager
from config.settings import settings

logger = get_logger("workflow")


class WorkflowOrchestrator:
    """工作流编排器 - 协调各Agent执行顺序"""

    def __init__(self):
        self.state_manager = StateManager()
        self.context_manager = ContextManager()

        # 初始化所有Agent
        self.product_analyzer = ProductAnalyzer()
        self.creative_planner = CreativePlanner()
        self.scene_generator = SceneGenerator()
        self.prompt_generator = PromptGenerator()
        self.video_generator = VideoGenerator()
        self.quality_evaluator = QualityEvaluator()
        self.video_editor = VideoEditor()
        self.brand_composer = BrandComposer()

    async def run(
        self,
        product_images: List[str],
        user_requirements: Optional[str] = None,
        brand_assets: Optional[BrandAssets] = None,
    ) -> str:
        """
        执行完整工作流

        Args:
            product_images: 产品图片路径列表
            user_requirements: 用户需求描述
            brand_assets: 品牌素材

        Returns:
            str: 最终视频路径
        """
        # 创建工作流ID
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # 创建状态
        state = self.state_manager.create_state(
            workflow_id=workflow_id,
            product_images=product_images,
            user_requirements=user_requirements or "",
        )

        state.mark_started()
        self.state_manager.update_state(state, status=WorkflowStatus.ANALYZING)

        try:
            # ===== 阶段1: 产品分析 =====
            logger.info(f"[{workflow_id}] Stage 1: Product Analysis")
            state.update_status(WorkflowStatus.ANALYZING, "Analyzing product images", "ProductAnalyzer")
            state.set_progress(5)

            product_info = await self.product_analyzer.execute(product_images)
            state.product_info_summary = product_info.get_summary()
            self.state_manager.save_state(state)

            # ===== 阶段2: 创意策划 =====
            logger.info(f"[{workflow_id}] Stage 2: Creative Planning")
            state.update_status(WorkflowStatus.PLANNING, "Creating creative plan", "CreativePlanner")
            state.set_progress(15)

            creative_plan = await self.creative_planner.execute(product_info, user_requirements)
            state.creative_plan_summary = f"Style: {creative_plan.ad_style}"
            self.state_manager.save_state(state)

            # ===== 阶段3: 场景生成 =====
            logger.info(f"[{workflow_id}] Stage 3: Scene Generation")
            state.update_status(WorkflowStatus.GENERATING_SCENES, "Generating scene images", "SceneGenerator")
            state.set_progress(25)

            scene_images = await self.scene_generator.execute(creative_plan, product_images)
            state.scene_images = scene_images
            self.state_manager.save_state(state)

            if not scene_images:
                raise Exception("No scene images generated")

            # ===== 阶段4: Prompt生成 =====
            logger.info(f"[{workflow_id}] Stage 4: Prompt Generation")
            state.update_status(WorkflowStatus.GENERATING_PROMPTS, "Generating video prompts", "PromptGenerator")
            state.set_progress(35)

            # 为每个场景生成Prompt
            all_prompts = []
            for scene_image in scene_images:
                prompts = await self.prompt_generator.execute(
                    scene_image=scene_image,
                    product_image=product_images[0],
                    creative_plan=creative_plan,
                )
                all_prompts.append(prompts)

            # ===== 阶段5: 视频生成 =====
            logger.info(f"[{workflow_id}] Stage 5: Video Generation")
            state.update_status(WorkflowStatus.GENERATING_VIDEOS, "Generating videos", "VideoGenerator")
            state.set_progress(45)

            # 为第一个场景生成视频（可扩展为多场景）
            all_videos = []
            for i, prompts in enumerate(all_prompts[:1]):  # 限制为第一个场景
                videos = await self.video_generator.execute(
                    prompts=prompts,
                    reference_image=scene_images[i] if i < len(scene_images) else scene_images[0],
                    duration=settings.video_default_duration,
                )
                all_videos.extend(videos)
                state.set_progress(45 + (i + 1) * 10)

            state.video_results_summary = f"Generated {len(all_videos)} videos"
            self.state_manager.save_state(state)

            if not all_videos:
                raise Exception("No videos generated")

            # ===== 阶段6: 质量评估 =====
            logger.info(f"[{workflow_id}] Stage 6: Quality Evaluation")
            state.update_status(WorkflowStatus.EVALUATING, "Evaluating video quality", "QualityEvaluator")
            state.set_progress(70)

            best_evaluation = await self.quality_evaluator.execute(all_videos, product_images[0])

            if not best_evaluation or not best_evaluation.video_path:
                # 使用第一个成功的视频
                successful = [v for v in all_videos if v.success]
                if successful:
                    best_video_path = successful[0].video_path
                else:
                    raise Exception("No successful videos to use")
            else:
                best_video_path = best_evaluation.video_path

            state.evaluation_summary = f"Best: {best_evaluation.model_name if best_evaluation else 'unknown'}"
            self.state_manager.save_state(state)

            # ===== 阶段7: 视频编辑 =====
            logger.info(f"[{workflow_id}] Stage 7: Video Editing")
            state.update_status(WorkflowStatus.EDITING, "Editing video", "VideoEditor")
            state.set_progress(80)

            # 可选的视频编辑
            edited_video_path = best_video_path  # 暂时跳过编辑

            # ===== 阶段8: 品牌合成 =====
            logger.info(f"[{workflow_id}] Stage 8: Brand Composition")
            state.update_status(WorkflowStatus.COMPOSING, "Adding brand elements", "BrandComposer")
            state.set_progress(90)

            if brand_assets:
                final_video_path = await self.brand_composer.execute(edited_video_path, brand_assets)
            else:
                final_video_path = edited_video_path

            # ===== 完成 =====
            state.mark_completed(final_video_path)
            self.state_manager.save_state(state)

            logger.info(f"[{workflow_id}] Workflow completed! Output: {final_video_path}")
            return final_video_path

        except Exception as e:
            logger.error(f"[{workflow_id}] Workflow failed: {e}")
            state.mark_failed(str(e), state.current_step)
            self.state_manager.save_state(state)
            raise

    def get_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """获取工作流状态"""
        return self.state_manager.load_state(workflow_id)

    def list_workflows(self) -> list:
        """列出所有工作流"""
        return self.state_manager.list_workflows()
