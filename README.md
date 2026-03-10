# 产品广告视频自动化工作流 Agent

这是一个基于多 Agent 协作的产品广告视频生成项目：输入产品图片与需求，自动完成分析、创意、场景、视频生成、评估、编辑与品牌合成，输出成片视频。

## 核心能力

- 多阶段流水线编排（`WorkflowOrchestrator`）
- 多视频模型并行生成（Kling / Sora2 / Seedance / Veo3，经 fal.ai）
- 自动质量评估并选择最佳结果
- 可选 AI 视频编辑与品牌元素叠加（Logo / CTA / 背景音乐）
- 工作流状态持久化（支持 `--list` / `--status`）

## 项目结构

```text
video_agent/
├── main.py                    # CLI 入口
├── orchestrator/              # 工作流编排与状态管理
├── agents/                    # 各子 Agent
├── tools/                     # 外部模型/API与媒体处理封装
├── models/                    # 数据模型
├── config/                    # 配置、提示词、密钥加载
├── utils/                     # 日志、重试、上下文管理
├── tests/                     # 单元测试
├── system_prompt_video_gen.md # PromptGenerator系统提示词
└── state/ output/ temp/ logs/ cache/  # 运行时目录（按需生成）
```

## 环境准备

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

至少需要配置：

- `OPENAI_API_KEY`（产品分析、创意、提示词生成、质量评估）
- `FAL_API_KEY`（视频生成与视频编辑）
- `FLUX_API_KEY` + `FLUX_API_URL`（场景图生成）

## 快速开始

```bash
python3 main.py -i samples/product.jpg -r "高端科技风格" --cta "立即购买"
```

常用命令：

```bash
python3 main.py --help
python3 main.py --list
python3 main.py --status <workflow_id>
```

## 工作流调用链

主流程在 `orchestrator/workflow.py` 中按顺序调用：

1. `ProductAnalyzer.execute(product_images)`
2. `CreativePlanner.execute(product_info, user_requirements)`
3. `SceneGenerator.execute(creative_plan, product_images)`
4. `PromptGenerator.execute(scene_image, product_image, creative_plan)`
5. `VideoGenerator.execute(prompts, reference_image, duration)`
6. `QualityEvaluator.execute(videos, product_image)`
7. `VideoEditor.execute(selected_video)`
8. `BrandComposer.execute(edited_video_path, brand_assets)`

## 每个子 Agent 如何调用

下面示例均为异步调用（`await`）。

### 1) ProductAnalyzer

作用：分析产品图片并提取结构化产品信息。  
输入：`List[str] product_images`  
输出：`ProductInfo`

```python
from agents.product_analyzer import ProductAnalyzer

agent = ProductAnalyzer()
product_info = await agent.execute(["./samples/product.jpg"])
```

### 2) CreativePlanner

作用：根据产品信息和用户需求生成创意方案。  
输入：`ProductInfo`, `Optional[str] user_requirements`  
输出：`CreativePlan`

```python
from agents.creative_planner import CreativePlanner

agent = CreativePlanner()
creative_plan = await agent.execute(product_info, "高端科技风格")
```

### 3) SceneGenerator

作用：基于创意方案生成场景图（可选产品抠图合成）。  
输入：`CreativePlan`, `List[str] product_images`, `compose_product=False`  
输出：`List[str]`（场景图片路径）

```python
from agents.scene_generator import SceneGenerator

agent = SceneGenerator()
scene_images = await agent.execute(creative_plan, ["./samples/product.jpg"])
```

### 4) PromptGenerator

作用：根据场景图 + 产品图，生成各视频模型专用 Prompt。  
输入：`scene_image`, `product_image`, `CreativePlan`  
输出：`Dict[str, Any]`（含 `kling/sora2/seedance/veo3`）

```python
from agents.prompt_generator import PromptGenerator

agent = PromptGenerator()
prompts = await agent.execute(
    scene_image=scene_images[0],
    product_image="./samples/product.jpg",
    creative_plan=creative_plan,
)
```

### 5) VideoGenerator

作用：并行调用多模型生成视频。  
输入：`prompts`, `reference_image`, `duration=4`  
输出：`List[VideoResult]`

```python
from agents.video_generator import VideoGenerator

agent = VideoGenerator()
video_results = await agent.execute(
    prompts=prompts,
    reference_image=scene_images[0],
    duration=4,
)
```

单独调用 Kling（可选）：

```python
kling_result = await agent.generate_kling(
    reference_image=scene_images[0],
    prompt_config=prompts["kling"],
)
```

### 6) QualityEvaluator

作用：提取关键帧并评估质量，返回最佳结果。  
输入：`List[VideoResult]`, `product_image`  
输出：`EvaluationResult`（`is_best=True`）

```python
from agents.quality_evaluator import QualityEvaluator

agent = QualityEvaluator()
best_eval = await agent.execute(video_results, "./samples/product.jpg")
```

### 7) VideoEditor

作用：对选中视频做 AI 视频编辑（Kling video-to-video）。  
输入：`VideoResult`, `Optional[EditConfig]`  
输出：`str`（编辑后视频路径）

```python
from agents.video_editor import VideoEditor, EditConfig

agent = VideoEditor()
edited_path = await agent.execute(
    video=video_results[0],
    config=EditConfig(
        prompt="增强高级感，保持产品真实比例与材质",
        keep_audio=True,
        shot_type="customize",
    ),
)
```

### 8) BrandComposer

作用：给视频叠加 Logo / CTA / 背景音乐。  
输入：`video_path`, `Optional[BrandAssets]`  
输出：`str`（品牌合成后视频路径）

```python
from agents.brand_composer import BrandComposer, BrandAssets

agent = BrandComposer()
final_path = await agent.execute(
    video_path=edited_path,
    brand_assets=BrandAssets(
        logo_path="./assets/logo.png",
        cta_text="立即购买",
        background_music="./assets/bgm.mp3",
    ),
)
```

## 直接调用总编排器（推荐）

如果不想手动串联每个子 Agent，直接调用：

```python
from orchestrator.workflow import WorkflowOrchestrator
from agents.brand_composer import BrandAssets

orchestrator = WorkflowOrchestrator()
final_video = await orchestrator.run(
    product_images=["./samples/product.jpg"],
    user_requirements="高端科技风格",
    brand_assets=BrandAssets(cta_text="立即购买"),
)
print(final_video)
```

## 状态与输出

- 工作流状态：`./state/<workflow_id>.json`
- 生成视频/编辑输出：`./temp/videos`、`./output/edited_videos`、`./output`
- 日志：`./logs/video_agent.log`

## 测试与校验

```bash
# 语法检查
PYTHONPYCACHEPREFIX=/tmp/video_agent_pycache python3 -m compileall agents config models orchestrator tools utils main.py

# 运行测试
pytest -q
```

