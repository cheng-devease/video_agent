"""提示词模板配置 - 用户需要配置这些提示词"""
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Prompts:
    """所有Agent的提示词模板"""

    # ==================== 产品分析Agent提示词 ====================
    product_analyzer_system: str = ""
    product_analyzer_user: str = ""

    # ==================== 创意策划Agent提示词 ====================
    creative_planner_system: str = ""
    creative_planner_user: str = ""

    # ==================== 场景生成Agent提示词 ====================
    scene_generator_system: str = ""
    scene_generator_user: str = ""

    # ==================== Prompt生成Agent提示词 ====================
    prompt_generator_system: str = ""
    prompt_generator_user: str = ""

    # ==================== 质量评估Agent提示词 ====================
    quality_evaluator_system: str = ""
    quality_evaluator_user: str = ""

    # ==================== 视频编辑Agent提示词 ====================
    video_editor_system: str = ""
    video_editor_user: str = ""

    # ==================== 品牌合成Agent提示词 ====================
    brand_composer_system: str = ""
    brand_composer_user: str = ""

    # ==================== 上下文压缩提示词 ====================
    context_compressor_system: str = ""
    context_compressor_user: str = ""

    # ==================== 默认提示词模板 ====================
    # 这些是示例模板，用户可以根据需要修改

    _default_product_analyzer_system: str = """
你是一位经验丰富的产品分析师，擅长从图片中识别产品特征、材质、颜色等关键信息。
请仔细分析产品图片，提取以下信息并以JSON格式返回。
"""

    _default_product_analyzer_user: str = """
分析以下产品图片，提取以下信息并以JSON格式返回:
{
    "product_type": "产品类型",
    "product_name": "产品名称(如果可见)",
    "key_features": ["特征1", "特征2", ...],
    "material": "材质",
    "color_palette": ["主要颜色", "辅助颜色"],
    "shape_description": "形状描述",
    "brand_elements": ["Logo位置", "品牌色"],
    "target_audience": "目标受众",
    "selling_points": ["卖点1", "卖点2"]
}
"""

    _default_creative_planner_system: str = """
你是一位创意总监，擅长为产品设计引人注目的广告创意。
基于产品信息，设计一个完整的广告创意方案。
"""

    _default_creative_planner_user: str = """
基于以下产品信息，设计一个产品广告创意方案:

产品信息: {product_info}
用户需求: {user_requirements}

请提供:
1. 广告风格 (高端/亲民/科技/自然/奢华等)
2. 场景概念描述
3. 视觉风格参考
4. 配色方案
5. 情绪基调
6. Hook策略 (如何在前3秒抓住注意力)
7. 2-3个场景的图片生成prompt

以JSON格式返回。
"""

    _default_prompt_generator_system: str = """
你是一位Prompt工程专家，精通Kling、Sora2、Seedance、Veo3的Prompt规范。
根据场景图片和产品图片，生成各模型的专用视频生成Prompt。
"""

    _default_prompt_generator_user: str = """
请分析以上图片，为4秒Hook广告生成各模型的视频Prompt。
输出JSON格式，包含以下模型:
- kling: {prompt, negative_prompt}
- sora2: {prompt}
- seedance: {full_prompt}
- veo3: {prompt}
"""

    _default_quality_evaluator_system: str = """
你是一位视频质量评估专家，擅长评估AI生成视频的质量。
请根据产品一致性、视觉质量、创意契合度、广告效果四个维度评估视频。
"""

    _default_quality_evaluator_user: str = """
评估以下视频帧与原始产品图片的一致性:

评估维度(每项0-25分):
1. 产品一致性: 视频中产品是否与原始图片一致
2. 视觉质量: 清晰度、流畅度
3. 创意契合度: 是否符合产品广告的预期效果
4. 广告效果: 吸引力、专业度

以JSON格式返回总分和各维度得分。
"""

    _default_context_compressor_system: str = """
你是一个文本摘要专家。请将以下对话历史压缩为简洁的摘要，保留关键信息。
"""

    _default_context_compressor_user: str = """
请将以下对话历史压缩为简洁的摘要，保留所有关键决策、结论和重要信息:

{conversation_history}

摘要:
"""

    def get_product_analyzer_prompts(self) -> tuple:
        """获取产品分析提示词"""
        system = self.product_analyzer_system or self._default_product_analyzer_system
        user = self.product_analyzer_user or self._default_product_analyzer_user
        return system, user

    def get_creative_planner_prompts(self) -> tuple:
        """获取创意策划提示词"""
        system = self.creative_planner_system or self._default_creative_planner_system
        user = self.creative_planner_user or self._default_creative_planner_user
        return system, user

    def get_prompt_generator_prompts(self) -> tuple:
        """获取Prompt生成提示词"""
        system = self.prompt_generator_system or self._default_prompt_generator_system
        user = self.prompt_generator_user or self._default_prompt_generator_user
        return system, user

    def get_quality_evaluator_prompts(self) -> tuple:
        """获取质量评估提示词"""
        system = self.quality_evaluator_system or self._default_quality_evaluator_system
        user = self.quality_evaluator_user or self._default_quality_evaluator_user
        return system, user

    def get_context_compressor_prompts(self) -> tuple:
        """获取上下文压缩提示词"""
        system = self.context_compressor_system or self._default_context_compressor_system
        user = self.context_compressor_user or self._default_context_compressor_user
        return system, user


# 全局提示词实例
prompts = Prompts()
