# 项目运行流程与 Agent 使用说明

## 1. 项目目标

本项目用于将产品图片自动生成广告视频。  
核心思路是：通过 `WorkflowOrchestrator` 串联多个子 Agent，逐步完成从“产品理解”到“成片输出”的全流程。

---

## 2. 整体运行流程

### 2.1 入口

- CLI 入口：`main.py`
- 主调用函数：`generate_video(...)`
- 核心编排器：`orchestrator/workflow.py` 的 `WorkflowOrchestrator.run(...)`

### 2.2 流程阶段（按执行顺序）

1. `ProductAnalyzer`：分析产品图片，提取产品结构化信息 `ProductInfo`
2. `CreativePlanner`：生成创意策略与场景规划 `CreativePlan`
3. `SceneGenerator`：根据创意生成场景图（可选产品抠图合成）
4. `PromptGenerator`：基于场景图与产品图，为各视频模型生成 Prompt
5. `VideoGenerator`：并行调用视频模型生成候选视频
6. `QualityEvaluator`：抽帧打分并选出最佳视频
7. `VideoEditor`：对最佳视频做 AI 二次编辑（可选）
8. `BrandComposer`：叠加 Logo/CTA/背景音乐，输出成片（可选）

### 2.3 状态管理

- 状态文件：`state/<workflow_id>.json`
- 查询命令：
  - `python3 main.py --list`
  - `python3 main.py --status <workflow_id>`

---

## 3. 快速运行（端到端）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

示例：

```bash
python3 main.py -i samples/product.jpg -r "高端科技风格" --cta "立即购买"
```

关键环境变量：

- `OPENAI_API_KEY`：用于图像理解/文本生成（产品分析、创意策划、Prompt 生成、质量评估）
- `FAL_API_KEY`：用于视频生成与视频编辑
- `FLUX_API_KEY` + `FLUX_API_URL`：用于场景图生成

---

## 4. 每个 Agent 的单独使用方式

以下示例默认在异步函数中执行，均需 `await`。

### 4.1 ProductAnalyzer

文件：`agents/product_analyzer.py`  
作用：从产品图片提取结构化产品信息  
输入：`List[str] product_images`  
输出：`ProductInfo`

```python
from agents.product_analyzer import ProductAnalyzer

agent = ProductAnalyzer()
product_info = await agent.execute(["./samples/product.jpg"])
print(product_info.to_dict())
```

### 4.2 CreativePlanner

文件：`agents/creative_planner.py`  
作用：根据产品信息生成创意方案  
输入：`ProductInfo`, `Optional[str] user_requirements`  
输出：`CreativePlan`

```python
from agents.creative_planner import CreativePlanner

agent = CreativePlanner()
creative_plan = await agent.execute(product_info, "高端科技风格，强调金属质感")
print(creative_plan.to_dict())
```

### 4.3 SceneGenerator

文件：`agents/scene_generator.py`  
作用：生成场景图片，可选把产品抠图后合成到场景  
输入：`CreativePlan`, `List[str] product_images`, `compose_product=False`  
输出：`List[str]`（场景图路径）

```python
from agents.scene_generator import SceneGenerator

agent = SceneGenerator()
scene_images = await agent.execute(
    creative_plan=creative_plan,
    product_images=["./samples/product.jpg"],
    compose_product=False,
)
print(scene_images)
```

### 4.4 PromptGenerator

文件：`agents/prompt_generator.py`  
作用：为 Kling/Sora2/Seedance/Veo3 生成模型专用 Prompt  
输入：`scene_image`, `product_image`, `creative_plan`  
输出：`Dict[str, Dict]`（每个模型对应 prompt + params）

```python
from agents.prompt_generator import PromptGenerator

agent = PromptGenerator()
prompts = await agent.execute(
    scene_image=scene_images[0],
    product_image="./samples/product.jpg",
    creative_plan=creative_plan,
)
print(prompts.keys())  # kling / sora2 / seedance / veo3
```

### 4.5 VideoGenerator

文件：`agents/video_generator.py`  
作用：并行调用视频模型生成候选视频  
输入：`prompts`, `reference_image`, `duration`  
输出：`List[VideoResult]`

```python
from agents.video_generator import VideoGenerator

agent = VideoGenerator()
video_results = await agent.execute(
    prompts=prompts,
    reference_image=scene_images[0],
    duration=4,
)
for item in video_results:
    print(item.model_name, item.success, item.video_path)
```

可单独调用 Kling：

```python
kling_result = await agent.generate_kling(
    reference_image=scene_images[0],
    prompt_config=prompts["kling"],
)
print(kling_result.video_path)
```

### 4.6 QualityEvaluator

文件：`agents/quality_evaluator.py`  
作用：对视频抽帧并多维评分，选择最佳结果  
输入：`videos`, `product_image`  
输出：`EvaluationResult`

```python
from agents.quality_evaluator import QualityEvaluator

agent = QualityEvaluator()
best_eval = await agent.execute(video_results, "./samples/product.jpg")
print(best_eval.model_name, best_eval.score.total_score, best_eval.video_path)
```

### 4.7 VideoEditor

文件：`agents/video_editor.py`  
作用：调用 Kling 视频编辑模型做二次优化  
输入：`VideoResult`, `Optional[EditConfig]`  
输出：`str`（编辑后视频路径）

```python
from agents.video_editor import VideoEditor, EditConfig

agent = VideoEditor()
edited_path = await agent.execute(
    video=video_results[0],
    config=EditConfig(
        prompt="提升高级感，保持产品真实结构与品牌识别",
        keep_audio=True,
        shot_type="customize",
    ),
)
print(edited_path)
```

### 4.8 BrandComposer

文件：`agents/brand_composer.py`  
作用：给视频叠加品牌素材（Logo/CTA/BGM）  
输入：`video_path`, `Optional[BrandAssets]`  
输出：`str`（最终成片路径）

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
print(final_path)
```

---

## 5. 推荐调用方式：直接使用编排器

如果你不需要手工串联每个 Agent，推荐直接使用编排器：

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

---

## 6. 常见问题与排查

- 报错 `Missing required API keys`：
  - 检查 `.env` 是否配置 `OPENAI_API_KEY`
- 场景图生成失败：
  - 检查 `FLUX_API_KEY` 与 `FLUX_API_URL`
- 视频生成为空：
  - 检查 `FAL_API_KEY`，以及 fal.ai 账户额度/模型权限
- 无法抽帧评估：
  - 检查系统是否可用 `ffmpeg`

