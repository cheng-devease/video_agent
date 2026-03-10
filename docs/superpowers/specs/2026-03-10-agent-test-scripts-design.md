# Agent Test Scripts Design

## Goal

为 `PromptGenerator`、`VideoGenerator`、`VideoEditor` 三个 agent 提供可独立运行的脚本入口，便于后续本地测试、单独调用和端到端排障。

## Scope

- 新增 `scripts/test_prompt_generator.py`
- 新增 `scripts/test_video_generator.py`
- 新增 `scripts/test_video_editor.py`
- 每个脚本都直接调用对应 agent，不依赖 `WorkflowOrchestrator`
- 输出统一为 JSON，便于人工查看和脚本串联

## Design

### PromptGenerator Script

- 输入：
  - `--scene-image`
  - `--product-image`
  - 可选创意字段：`--ad-style`、`--visual-style-reference`、`--scene-concept`、`--emotional-tone`、`--hook-strategy`、`--user-requirements`
- 行为：
  - 构造 `CreativePlan`
  - 调用 `PromptGenerator.execute(...)`
- 输出：
  - 模型提示词 JSON

### VideoGenerator Script

- 输入：
  - `--reference-image`
  - `--product-image` / `--product-images`
  - `--prompt` 或 `--prompt-json`
  - `--model`，默认 `kling`
  - Kling 相关参数：`--negative-prompt`、`--aspect-ratio`、`--duration`、`--generate-audio`、`--cfg-scale`、`--shot-type`
- 行为：
  - 构造 `prompt_config`
  - 直接调用 `VideoGenerator.generate_kling(...)` 或 `execute(...)`
- 输出：
  - 结果 JSON

### VideoEditor Script

- 输入：
  - `--video-path`
  - `--prompt`
  - `--image-url`
  - `--keep-audio`
  - `--shot-type`
  - `--elements-json`
- 行为：
  - 构造 `EditConfig`
  - 调用 `VideoEditor.edit_video(...)`
- 输出：
  - 编辑结果 JSON

## Testing

- 为每个脚本写一个最小 smoke 测试，验证：
  - CLI 参数能解析
  - 对应 agent 被调用
  - 返回结果被序列化成 JSON
