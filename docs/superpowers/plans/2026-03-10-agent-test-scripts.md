# Agent Test Scripts Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add three standalone scripts that exercise PromptGenerator, VideoGenerator, and VideoEditor independently from the main workflow.

**Architecture:** Create one script per agent under `scripts/`, keep argument parsing local to each script, and expose lightweight `run(...)` helpers so tests can invoke the script logic without spawning subprocesses.

**Tech Stack:** Python, argparse, asyncio, existing agent classes, pytest-style tests

---

## Chunk 1: Prompt Script

### Task 1: Lock PromptGenerator script behavior

**Files:**
- Create: `scripts/test_prompt_generator.py`
- Create: `tests/test_agent_scripts.py`

- [ ] **Step 1: Write the failing test**

```python
def test_prompt_script_runs_and_returns_json():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_agent_scripts.py::test_prompt_script_runs_and_returns_json -v`
Expected: FAIL because the script does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
async def run(...):
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_agent_scripts.py::test_prompt_script_runs_and_returns_json -v`
Expected: PASS

## Chunk 2: Video and Edit Scripts

### Task 2: Lock VideoGenerator and VideoEditor script behavior

**Files:**
- Create: `scripts/test_video_generator.py`
- Create: `scripts/test_video_editor.py`
- Modify: `tests/test_agent_scripts.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_video_generator_script_runs_and_returns_json():
    ...

def test_video_editor_script_runs_and_returns_json():
    ...
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_agent_scripts.py -v`
Expected: FAIL because the scripts do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
async def run(...):
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_agent_scripts.py -v`
Expected: PASS

## Chunk 3: Verification

### Task 3: Verify scripts and syntax

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run script tests**

Run: `python3 -m pytest tests/test_agent_scripts.py tests/test_video_generator_agent.py tests/test_prompt_generator.py tests/test_video_edit.py tests/test_video_gen.py -v`
Expected: PASS

- [ ] **Step 2: Run syntax check**

Run: `PYTHONPYCACHEPREFIX=/tmp/video_agent_pycache python3 -m compileall agents orchestrator scripts tools`
Expected: exit 0

- [ ] **Step 3: Run CLI help smoke checks**

Run: `python3 scripts/test_prompt_generator.py --help`
Run: `python3 scripts/test_video_generator.py --help`
Run: `python3 scripts/test_video_editor.py --help`
Expected: all exit 0
