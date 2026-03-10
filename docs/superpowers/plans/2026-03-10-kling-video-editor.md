# Kling Video Editor Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current local video editing path with fal.ai Kling O3 Pro video-to-video edit and keep the editor usable both in workflow mode and standalone.

**Architecture:** Add a dedicated `KlingVideoEditAPI` in `tools/video_edit.py`, update `VideoEditor` to build and pass AI edit configs, and call the editor from workflow stage 7 with a safe default prompt and fallback behavior.

**Tech Stack:** Python, aiohttp, asyncio, fal.ai queue API, pytest-style tests

---

## Chunk 1: Tool Contract

### Task 1: Lock Kling video edit payload behavior

**Files:**
- Create: `tests/test_video_edit.py`
- Modify: `tools/video_edit.py`

- [ ] **Step 1: Write the failing test**

```python
def test_kling_video_edit_builds_payload_with_all_supported_inputs():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_video_edit.py::test_kling_video_edit_builds_payload_with_all_supported_inputs -v`
Expected: FAIL because the current module only exposes MoviePy tools.

- [ ] **Step 3: Write minimal implementation**

```python
class KlingVideoEditAPI(VideoEditTool):
    model_id = "fal-ai/kling-video/o3/pro/video-to-video/edit"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_video_edit.py::test_kling_video_edit_builds_payload_with_all_supported_inputs -v`
Expected: PASS

## Chunk 2: Agent Integration

### Task 2: Lock agent pass-through and standalone editing

**Files:**
- Modify: `agents/video_editor.py`
- Modify: `tests/test_video_edit.py`
- Modify: `tools/__init__.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_video_editor_passes_all_ai_edit_params():
    ...

def test_video_editor_supports_standalone_editing():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_video_edit.py -v`
Expected: FAIL because the current agent is MoviePy-based and has no standalone AI editing entrypoint.

- [ ] **Step 3: Write minimal implementation**

```python
class VideoEditor(BaseAgent):
    async def edit_video(...):
        ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_video_edit.py -v`
Expected: PASS

## Chunk 3: Workflow Verification

### Task 3: Verify workflow and syntax

**Files:**
- Modify: `orchestrator/workflow.py`

- [ ] **Step 1: Run focused tests**

Run: `python3 -m pytest tests/test_video_edit.py tests/test_video_generator_agent.py tests/test_prompt_generator.py tests/test_video_gen.py -v`
Expected: PASS

- [ ] **Step 2: Run syntax check**

Run: `PYTHONPYCACHEPREFIX=/tmp/video_agent_pycache python3 -m compileall agents config models orchestrator tools utils main.py`
Expected: exit 0

- [ ] **Step 3: Run CLI smoke check**

Run: `python3 main.py --help`
Expected: exit 0 and CLI help text printed
