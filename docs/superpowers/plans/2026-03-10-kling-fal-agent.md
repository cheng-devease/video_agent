# Kling fal.ai Agent Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Switch the Kling image-to-video path to `fal-ai/kling-video/v3/pro/image-to-video`, make the request payload fully configurable, and keep the video generation agent usable both inside the workflow and as a standalone entrypoint.

**Architecture:** Replace the existing direct Kling REST wrapper with a fal.ai queue client implemented in `tools/video_gen.py`. Expand the `VideoGenerator` agent so it can pass through Kling-specific parameters from prompt configs, and add a small standalone helper around that agent without changing the broader orchestrator contract.

**Tech Stack:** Python, aiohttp, asyncio, pytest-style tests, fal.ai HTTP queue API

---

## Chunk 1: Test Coverage

### Task 1: Lock the Kling tool contract

**Files:**
- Create: `tests/test_video_gen.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Write the failing test**

```python
async def test_kling_builds_fal_payload_from_prompt_and_additional_params():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_video_gen.py -v`
Expected: FAIL because the existing Kling wrapper does not build a fal.ai payload.

- [ ] **Step 3: Write minimal implementation**

```python
class KlingAPI(VideoGenTool):
    model_id = "fal-ai/kling-video/v3/pro/image-to-video"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_video_gen.py -v`
Expected: PASS

## Chunk 2: Agent Integration

### Task 2: Lock parameter pass-through and standalone execution

**Files:**
- Create: `tests/test_video_generator_agent.py`
- Modify: `agents/video_generator.py`
- Modify: `models/video_result.py`

- [ ] **Step 1: Write the failing tests**

```python
async def test_video_generator_passes_kling_additional_params():
    ...

async def test_video_generator_can_run_standalone_for_kling_only():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_video_generator_agent.py -v`
Expected: FAIL because the agent only forwards a small fixed argument set and has no standalone helper.

- [ ] **Step 3: Write minimal implementation**

```python
class VideoGenerator(BaseAgent):
    async def generate_kling(...):
        ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_video_generator_agent.py -v`
Expected: PASS

## Chunk 3: Verification

### Task 3: Verify syntax and smoke behavior

**Files:**
- Modify: `.env.example`
- Modify: `config/api_keys.py`
- Modify: `tools/__init__.py`

- [ ] **Step 1: Run focused tests**

Run: `python3 -m pytest tests/test_video_gen.py tests/test_video_generator_agent.py -v`
Expected: PASS

- [ ] **Step 2: Run syntax check**

Run: `PYTHONPYCACHEPREFIX=/tmp/video_agent_pycache python3 -m compileall agents config models orchestrator tools utils main.py`
Expected: exit 0

- [ ] **Step 3: Run CLI smoke check**

Run: `python3 main.py --help`
Expected: exit 0 and CLI help text printed
