# 产品广告视频自动化工作流Agent - 详细设计规划

## 一、项目概述

### 1.1 项目目标
构建一个全自动化工作流Agent，实现从几张产品图片到高质量产品广告视频的端到端生成。

### 1.2 核心能力
- **输入**: 1-5张产品图片 + 用户需求描述(可选)
- **输出**: 高质量4-15秒产品广告视频
- **全流程自动化**: 图片分析 → 场景生成 → 视频生成 → 视频编辑 → 成品输出

### 1.3 工作流程概览
```
产品图片 → 产品分析 → 创意策划 → 场景生成 → Prompt生成 → 
视频生成(多模型) → 质量评估 → 视频编辑 → 品牌合成 → 成品输出
```

---

## 二、技术可行性验证

### 2.1 各阶段可行性评估

| 阶段 | 可行性 | 技术成熟度 | 风险等级 | 关键依赖 |
|------|--------|-----------|---------|---------|
| 阶段1: 图片分析+场景生成 | ⭐⭐⭐⭐⭐ | 高 | 低 | GPT-4V, FLUX API |
| 阶段2: 图生视频 | ⭐⭐⭐⭐ | 中高 | 中 | Kling/Seedance API |
| 阶段3: 视频编辑 | ⭐⭐⭐⭐ | 中高 | 中 | OpusClip/MoviePy |
| 阶段4: 输出发布 | ⭐⭐⭐⭐⭐ | 高 | 低 | 云存储API |

### 2.2 技术风险与缓解策略

| 风险 | 影响 | 缓解策略 |
|------|------|---------|
| AI视频生成质量不稳定 | 高 | 多模型并行生成 + 质量评估选择最佳 |
| API调用失败/超时 | 中 | 指数退避重试 + 降级到备用方案 |
| 产品一致性保持困难 | 中 | 使用Seedance @语法 + 质量评估 |
| 生成成本过高 | 中 | 智能模型选择 + 缓存机制 |

---

## 三、系统架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     产品广告视频生成Agent                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ 编排层      │  │ Agent层     │  │ 工具层      │             │
│  │ (Workflow)  │  │ (8 Agents)  │  │ (APIs)      │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心组件

#### 3.2.1 编排层 (Orchestrator)
- **职责**: 协调各Agent执行顺序，管理状态和数据流转
- **实现**: 使用CrewAI / AutoGen / 自定义工作流引擎
- **状态管理**: IDLE → ANALYZING → PLANNING → GENERATING → EDITING → COMPLETED

#### 3.2.2 Agent层 (8个专用Agent)

| Agent名称 | 职责 | 输入 | 输出 |
|-----------|------|------|------|
| ProductAnalyzer | 产品图片分析 | 产品图片 | 产品信息JSON |
| CreativePlanner | 创意方案设计 | 产品信息 | 创意方案JSON |
| SceneGenerator | 场景图片生成 | 创意方案 | 场景图片 |
| PromptGenerator | Prompt生成 | 场景图片+产品 | 各模型Prompt |
| VideoGenerator | 视频生成 | Prompt | 多个视频 |
| QualityEvaluator | 质量评估 | 多个视频 | 最佳视频+评分 |
| VideoEditor | 视频编辑 | 最佳视频 | 编辑后视频 |
| BrandComposer | 品牌合成 | 视频+品牌素材 | 成品视频 |

#### 3.2.3 工具层 (APIs & Libraries)

| 类别 | 工具 | 用途 |
|------|------|------|
| 视觉分析 | GPT-4V, Claude 3.5 Sonnet | 产品图片分析 |
| 图像生成 | FLUX.1, Midjourney, SDXL | 场景图片生成 |
| 视频生成 | Kling, Sora2, Seedance, Veo3 | 图生视频 |
| 视频编辑 | OpusClip, VEED, MoviePy | 后期编辑 |
| 图像处理 | PIL, OpenCV, rembg | 抠图/合成 |

---

## 四、详细实现方案

### 4.1 阶段1: 产品分析 + 场景生成

#### 4.1.1 产品分析Agent实现

```python
class ProductAnalyzer:
    """产品分析Agent"""
    
    def analyze(self, product_images: List[str]) -> ProductInfo:
        """
        分析产品图片，提取关键信息
        
        Args:
            product_images: 产品图片路径列表 (1-5张)
        
        Returns:
            ProductInfo: 产品信息对象
        """
        # 1. 使用GPT-4V分析图片
        analysis_prompt = """
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
        
        # 2. 调用GPT-4V API
        response = self.gpt4v.analyze_images(product_images, analysis_prompt)
        
        # 3. 解析并返回结构化数据
        return ProductInfo.parse(response)
```

#### 4.1.2 创意策划Agent实现

```python
class CreativePlanner:
    """创意策划Agent"""
    
    def plan(self, product_info: ProductInfo, user_requirements: Optional[str] = None) -> CreativePlan:
        """
        根据产品信息设计广告创意方案
        
        Args:
            product_info: 产品分析结果
            user_requirements: 用户额外需求(可选)
        
        Returns:
            CreativePlan: 创意方案
        """
        planning_prompt = f"""
        基于以下产品信息，设计一个产品广告创意方案:
        
        产品信息: {product_info.to_json()}
        用户需求: {user_requirements or "无特殊要求"}
        
        请提供:
        1. 广告风格 (高端/亲民/科技/自然/奢华等)
        2. 场景概念描述
        3. 视觉风格参考 (如: Apple风格、电影感、极简等)
        4. 配色方案
        5. 情绪基调
        6. Hook策略 (如何在前3秒抓住注意力)
        7. 2-3个场景的图片生成prompt
        
        以JSON格式返回。
        """
        
        response = self.llm.generate(planning_prompt)
        return CreativePlan.parse(response)
```

#### 4.1.3 场景生成Agent实现

```python
class SceneGenerator:
    """场景生成Agent"""
    
    def generate_scenes(self, creative_plan: CreativePlan, product_images: List[str]) -> List[str]:
        """
        生成广告场景图片
        
        Args:
            creative_plan: 创意方案
            product_images: 产品图片路径
        
        Returns:
            List[str]: 生成的场景图片路径列表
        """
        scene_images = []
        
        for scene in creative_plan.scene_prompts:
            # 1. 生成场景背景
            scene_image = self.flux.generate(
                prompt=scene.image_prompt,
                aspect_ratio="16:9",
                quality="high"
            )
            
            # 2. (可选) 产品抠图并合成到场景
            if self.config.product_composition:
                product_cutout = self.remove_bg(product_images[0])
                composed_image = self.compose(scene_image, product_cutout)
                scene_images.append(composed_image)
            else:
                scene_images.append(scene_image)
        
        return scene_images
```

### 4.2 阶段2: 视频生成

#### 4.2.1 Prompt生成Agent实现

```python
class PromptGenerator:
    """Prompt生成Agent - 使用我们已开发的系统提示词"""
    
    def __init__(self):
        self.system_prompt = load_system_prompt("system_prompt.md")
    
    def generate_prompts(self, scene_image: str, product_image: str, creative_plan: CreativePlan) -> Dict:
        """
        生成各视频模型的专用Prompt
        
        使用我们已开发的系统提示词，输入场景图片和产品图片，
        输出各模型的专用Prompt
        """
        # 调用GPT-4，使用系统提示词
        response = self.gpt4.generate_with_vision(
            system_prompt=self.system_prompt,
            images=[scene_image, product_image],
            user_message="请分析以上图片，为4秒Hook广告生成各模型的视频Prompt"
        )
        
        # 解析JSON输出
        return json.loads(response)
```

#### 4.2.2 视频生成Agent实现

```python
class VideoGenerator:
    """视频生成Agent"""
    
    def __init__(self):
        self.kling = KlingAPI()
        self.sora2 = SoraAPI()
        self.seedance = SeedanceAPI()
        self.veo3 = Veo3API()
    
    async def generate_all(self, prompts: Dict, reference_image: str) -> Dict[str, str]:
        """
        并行调用各AI视频模型生成视频
        
        Args:
            prompts: 各模型的Prompt
            reference_image: 参考图片路径
        
        Returns:
            Dict[str, str]: 各模型生成的视频路径
        """
        tasks = {
            "kling": self.kling.generate_video(
                image=reference_image,
                prompt=prompts["kling"]["prompt"],
                negative_prompt=prompts["kling"]["negative_prompt"],
                duration=4
            ),
            "sora2": self.sora2.generate_video(
                image=reference_image,
                prompt=prompts["sora2"]["prompt"],
                duration=4
            ),
            "seedance": self.seedance.generate_video(
                image=reference_image,
                prompt=prompts["seedance"]["full_prompt"],
                duration=4
            ),
            "veo3": self.veo3.generate_video(
                image=reference_image,
                prompt=prompts["veo3"]["prompt"],
                duration=4
            )
        }
        
        # 并行执行，等待所有结果
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # 处理结果
        videos = {}
        for (model, task), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                logger.warning(f"{model} 生成失败: {result}")
                videos[model] = None
            else:
                videos[model] = result
        
        return videos
```

#### 4.2.3 质量评估Agent实现

```python
class QualityEvaluator:
    """质量评估Agent"""
    
    def evaluate(self, videos: Dict[str, str], product_image: str) -> EvaluationResult:
        """
        评估各模型生成的视频质量
        
        Args:
            videos: 各模型的视频路径
            product_image: 原始产品图片
        
        Returns:
            EvaluationResult: 评估结果
        """
        scores = {}
        
        for model, video_path in videos.items():
            if video_path is None:
                scores[model] = 0
                continue
            
            # 提取视频关键帧
            frames = self.extract_keyframes(video_path)
            
            # 使用GPT-4V评估
            eval_prompt = """
            评估以下视频帧与原始产品图片的一致性:
            
            评估维度(每项0-25分):
            1. 产品一致性: 视频中产品是否与原始图片一致
            2. 视觉质量: 清晰度、流畅度
            3. 创意契合度: 是否符合产品广告的预期效果
            4. 广告效果: 吸引力、专业度
            
            以JSON格式返回总分和各维度得分。
            """
            
            response = self.gpt4v.analyze_images(
                images=[product_image] + frames,
                prompt=eval_prompt
            )
            
            scores[model] = self.parse_score(response)
        
        # 排序并返回最佳
        sorted_models = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_model = sorted_models[0][0]
        
        return EvaluationResult(
            ranking=[m for m, _ in sorted_models],
            best_video=videos[best_model],
            best_model=best_model,
            scores=scores
        )
```

### 4.3 阶段3: 视频编辑

#### 4.3.1 视频编辑Agent实现

```python
class VideoEditor:
    """视频编辑Agent"""
    
    def __init__(self):
        self.opusclip = OpusClipAPI()
        self.moviepy = MoviePyEditor()
    
    def edit(self, video_path: str, edit_config: EditConfig) -> str:
        """
        对视频进行后期编辑
        
        Args:
            video_path: 输入视频路径
            edit_config: 编辑配置
        
        Returns:
            str: 编辑后的视频路径
        """
        # 方案A: 使用OpusClip API (推荐)
        if self.config.use_ai_editor:
            return self.opusclip.edit(
                video=video_path,
                add_captions=edit_config.add_captions,
                trim_silence=edit_config.trim_silence,
                enhance_quality=edit_config.enhance_quality
            )
        
        # 方案B: 使用MoviePy (程序化)
        else:
            clip = self.moviepy.load(video_path)
            
            # 裁剪
            if edit_config.trim:
                clip = clip.subclip(edit_config.start, edit_config.end)
            
            # 调整速度
            if edit_config.speed != 1.0:
                clip = clip.fx(vfx.speedx, edit_config.speed)
            
            # 导出
            output_path = self.generate_output_path()
            clip.write_videofile(output_path, codec='libx264')
            
            return output_path
```

#### 4.3.2 品牌合成Agent实现

```python
class BrandComposer:
    """品牌合成Agent"""
    
    def compose(self, video_path: str, brand_assets: BrandAssets) -> str:
        """
        添加品牌元素到视频中
        
        Args:
            video_path: 输入视频路径
            brand_assets: 品牌素材(Logo, 字体, 颜色等)
        
        Returns:
            str: 成品视频路径
        """
        clip = VideoFileClip(video_path)
        
        # 1. 添加Logo
        if brand_assets.logo:
            logo = ImageClip(brand_assets.logo).set_duration(clip.duration)
            logo = logo.resize(height=50).set_position(("right", "top"))
            clip = CompositeVideoClip([clip, logo])
        
        # 2. 添加CTA文字
        if brand_assets.cta_text:
            txt_clip = TextClip(
                brand_assets.cta_text,
                fontsize=30,
                color=brand_assets.primary_color,
                font=brand_assets.font
            ).set_duration(clip.duration).set_position(("center", "bottom"))
            clip = CompositeVideoClip([clip, txt_clip])
        
        # 3. 添加背景音乐
        if brand_assets.background_music:
            audio = AudioFileClip(brand_assets.background_music)
            audio = audio.volumex(0.3)  # 降低音量
            clip = clip.set_audio(audio)
        
        # 导出
        output_path = self.generate_output_path("final")
        clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        return output_path
```

---

## 五、工作流编排实现

### 5.1 使用CrewAI实现

```python
from crewai import Agent, Task, Crew, Process

class ProductVideoCrew:
    """产品视频生成Crew"""
    
    def __init__(self):
        self.create_agents()
        self.create_tasks()
    
    def create_agents(self):
        """创建各Agent"""
        self.product_analyzer = Agent(
            role="产品分析专家",
            goal="深入分析产品图片，提取关键产品信息",
            backstory="你是一位经验丰富的产品分析师，擅长从图片中识别产品特征、材质、颜色等关键信息",
            tools=[GPT4VisionTool()],
            verbose=True
        )
        
        self.creative_planner = Agent(
            role="创意策划专家",
            goal="设计吸引人的广告创意方案",
            backstory="你是一位创意总监，擅长为产品设计引人注目的广告创意",
            tools=[LLMTool()],
            verbose=True
        )
        
        self.scene_generator = Agent(
            role="场景生成专家",
            goal="生成高质量的广告场景图片",
            backstory="你是一位AI图像生成专家，擅长使用FLUX等工具生成商业级图片",
            tools=[FLUXTool(), ImageCompositionTool()],
            verbose=True
        )
        
        self.prompt_generator = Agent(
            role="Prompt工程专家",
            goal="生成各视频模型的专用Prompt",
            backstory="你是一位Prompt工程专家，精通Kling、Sora2、Seedance、Veo3的Prompt规范",
            tools=[LLMWithVisionTool()],
            verbose=True
        )
        
        self.video_generator = Agent(
            role="视频生成专家",
            goal="调用AI模型生成高质量视频",
            backstory="你是一位AI视频生成专家，精通各主流视频生成API",
            tools=[KlingTool(), SoraTool(), SeedanceTool(), Veo3Tool()],
            verbose=True
        )
        
        self.quality_evaluator = Agent(
            role="质量评估专家",
            goal="评估视频质量并选择最佳结果",
            backstory="你是一位视频质量评估专家，擅长评估AI生成视频的质量",
            tools=[GPT4VisionTool()],
            verbose=True
        )
        
        self.video_editor = Agent(
            role="视频编辑专家",
            goal="对视频进行专业后期编辑",
            backstory="你是一位视频编辑专家，擅长使用AI工具进行视频后期处理",
            tools=[OpusClipTool(), MoviePyTool()],
            verbose=True
        )
    
    def create_tasks(self):
        """创建任务链"""
        self.analyze_task = Task(
            description="分析产品图片，提取产品信息",
            agent=self.product_analyzer,
            expected_output="产品信息JSON"
        )
        
        self.plan_task = Task(
            description="设计广告创意方案",
            agent=self.creative_planner,
            expected_output="创意方案JSON",
            context=[self.analyze_task]
        )
        
        self.scene_task = Task(
            description="生成广告场景图片",
            agent=self.scene_generator,
            expected_output="场景图片路径列表",
            context=[self.plan_task]
        )
        
        self.prompt_task = Task(
            description="生成各模型专用Prompt",
            agent=self.prompt_generator,
            expected_output="各模型Prompt JSON",
            context=[self.scene_task]
        )
        
        self.video_task = Task(
            description="生成视频(多模型并行)",
            agent=self.video_generator,
            expected_output="各模型视频路径",
            context=[self.prompt_task]
        )
        
        self.evaluate_task = Task(
            description="评估视频质量并选择最佳",
            agent=self.quality_evaluator,
            expected_output="评估结果JSON",
            context=[self.video_task]
        )
        
        self.edit_task = Task(
            description="视频后期编辑",
            agent=self.video_editor,
            expected_output="成品视频路径",
            context=[self.evaluate_task]
        )
    
    def run(self, product_images: List[str], user_requirements: Optional[str] = None):
        """执行工作流"""
        crew = Crew(
            agents=[
                self.product_analyzer,
                self.creative_planner,
                self.scene_generator,
                self.prompt_generator,
                self.video_generator,
                self.quality_evaluator,
                self.video_editor
            ],
            tasks=[
                self.analyze_task,
                self.plan_task,
                self.scene_task,
                self.prompt_task,
                self.video_task,
                self.evaluate_task,
                self.edit_task
            ],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff(inputs={
            "product_images": product_images,
            "user_requirements": user_requirements
        })
        
        return result
```

### 5.2 使用n8n实现

n8n工作流设计:

```
[Form Trigger] ──▶ [Product Analyzer (HTTP)] ──▶ [Creative Planner (HTTP)]
                                                          │
                                                          ▼
[Scene Generator (HTTP)] ◀── [Image Gen (FLUX API)] ◀──┘
       │
       ▼
[Prompt Generator (HTTP)] ──▶ [Parallel Video Gen]
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              [Kling API]     [Seedance API]    [Veo3 API]
                    │               │               │
                    └───────────────┴───────────────┘
                                    │
                                    ▼
[Quality Evaluator (HTTP)] ──▶ [Video Editor (OpusClip)]
                                          │
                                          ▼
[Brand Composer (MoviePy)] ──▶ [Save to Drive] ──▶ [Output]
```

---

## 六、API配置与成本估算

### 6.1 所需API及配置

| API | 用途 | 获取方式 |
|-----|------|---------|
| OpenAI API | GPT-4V分析, Sora2视频生成 | https://platform.openai.com |
| Anthropic API | Claude 3.5 Sonnet分析 | https://console.anthropic.com |
| Kling API | 图生视频 | https://klingai.com |
| Seedance API | 图生视频 | 即梦平台 |
| Google Veo3 API | 图生视频 | Google Cloud |
| FLUX API | 场景图片生成 | fal.ai / Replicate |
| OpusClip API | 视频编辑 | https://opus.pro |

### 6.2 单次生成成本估算

| 项目 | 成本估算 | 备注 |
|------|---------|------|
| GPT-4V分析 | $0.01-0.02 | 按图片数量 |
| 场景图片生成 (FLUX) | $0.03-0.05 | 2-3张场景图 |
| Prompt生成 | $0.01 | 单次调用 |
| 视频生成 (4模型并行) | $0.5-2.0 | Kling最便宜，Sora最贵 |
| 质量评估 | $0.01-0.02 | 按视频数量 |
| 视频编辑 | $0.05-0.1 | OpusClip/MoviePy |
| **总计** | **$0.6-2.2** | 单次完整流程 |

---

## 七、项目里程碑

### 阶段1: MVP (2-3周)
- [ ] 实现产品分析Agent
- [ ] 实现Prompt生成Agent (复用已有系统提示词)
- [ ] 集成Kling API进行视频生成
- [ ] 基础视频编辑 (MoviePy)
- [ ] 命令行界面

### 阶段2: 完整功能 (3-4周)
- [ ] 实现创意策划Agent
- [ ] 实现场景生成Agent
- [ ] 集成多视频模型 (Kling, Seedance, Veo3)
- [ ] 实现质量评估Agent
- [ ] 集成AI视频编辑 (OpusClip)
- [ ] Web界面

### 阶段3: 优化与扩展 (2-3周)
- [ ] 错误处理与重试机制
- [ ] 性能优化 (缓存、并行)
- [ ] 批量处理功能
- [ ] 多平台发布集成
- [ ] 用户反馈循环

---

## 八、风险与缓解

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|---------|
| API不稳定 | 中 | 高 | 多模型备选、指数退避重试 |
| 生成质量不达标 | 中 | 高 | 质量评估Agent、人工审核节点 |
| 成本超预算 | 低 | 中 | 智能模型选择、缓存机制 |
| 产品一致性差 | 中 | 高 | Seedance @语法、质量评估 |
| 处理时间过长 | 中 | 中 | 并行处理、异步架构 |

---

## 九、总结

本方案设计了一个完整的**产品广告视频自动化生成工作流Agent**，具备以下特点:

1. **技术可行**: 所有阶段都有成熟的技术方案
2. **模块化设计**: 8个专用Agent，职责清晰
3. **多模型策略**: 4个视频模型并行，质量评估选择最佳
4. **容错机制**: 错误处理、降级策略、重试机制
5. **成本可控**: 单次生成成本$0.6-2.2

**推荐实现路径**:
1. 先实现MVP版本 (Kling单模型 + 基础功能)
2. 逐步添加多模型支持和高级功能
3. 集成到n8n或CrewAI工作流平台
