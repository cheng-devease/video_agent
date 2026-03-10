# Kling Video Editor Design

## Goal

将仓库中的 `VideoEditor` 从本地 MoviePy 后处理切换为基于 fal.ai `fal-ai/kling-video/o3/pro/video-to-video/edit` 的 AI 视频编辑能力，并保证该 agent 既可被工作流调用，也可单独调用。

## Scope

- 使用 fal 队列接口接入 Kling O3 Pro Video-to-Video Edit
- 暴露并透传模型支持的关键输入参数：
  - `prompt`
  - `video_url`
  - `image_urls`
  - `keep_audio`
  - `shot_type`
  - `elements[].frontal_image_url`
  - `elements[].reference_image_urls`
- 为 `VideoEditor` 增加可单独使用的编辑入口
- 让 orchestrator 的第 7 阶段可以调用新的 AI 编辑 agent

## Non-Goals

- 不保留旧的裁剪、加字、加音乐作为 `VideoEditor` 主路径
- 不新增单独的编辑提示词生成 agent
- 不接入除 Kling O3 Edit 之外的 v2v 编辑模型

## Architecture

### Tool Layer

`tools/video_edit.py` 改为 fal.ai 编辑工具模块：

- `VideoEditTool`
  - 提供输出目录和通用媒体输入归一化能力
- `KlingVideoEditAPI`
  - 封装 `fal-ai/kling-video/o3/pro/video-to-video/edit`
  - 负责 payload 组装、任务提交、状态轮询、结果获取与下载
  - 支持本地文件路径、URL、data URI 三种媒体输入

### Agent Layer

`agents/video_editor.py` 变为 AI 编辑 agent：

- `EditConfig`
  - 变更为模型参数配置对象
- `VideoEditor.execute(video, config)`
  - 接收 `VideoResult`
  - 生成或使用显式编辑 prompt
  - 调用 `KlingVideoEditAPI`
- `VideoEditor.edit_video(...)`
  - 支持独立调用，不依赖 `WorkflowOrchestrator`

### Workflow Integration

`orchestrator/workflow.py` 的 Stage 7 改为真正调用 `VideoEditor`。

- 若没有显式编辑参数，则使用最小默认 AI 编辑 prompt：
  - 保持主体身份和镜头连续性
  - 强化广告质感和功能表达
- 若编辑失败，则回退原视频路径，避免整个工作流中断

## Data Flow

1. 上游视频生成阶段产出 `VideoResult`
2. `VideoEditor` 从 `VideoResult.video_path` 读取参考视频
3. `EditConfig` 中的可选图片和元素图一并进入 fal payload
4. fal 返回编辑后视频 URL
5. 工具层下载到本地 `output` 或 `temp` 目录
6. `VideoEditor` 返回新的本地视频路径

## Error Handling

- 缺失 `FAL_API_KEY` 时抛出清晰错误
- 缺失输入视频或编辑 prompt 时返回可解释错误
- fal 队列失败、超时、下载失败时记录错误
- orchestrator 级别对编辑失败做回退，不阻断最终成片链路

## Testing

- 测试 `KlingVideoEditAPI` 的 payload 组装
- 测试 `VideoEditor` 对配置项的透传
- 测试 `VideoEditor` 的独立调用入口
- 测试无显式 prompt 时的默认编辑 prompt 行为
