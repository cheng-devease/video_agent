# Repository Guidelines

## Project Structure & Module Organization
`main.py` is the CLI entrypoint for the end-to-end video workflow. Core orchestration lives in `orchestrator/`, which coordinates agent stages and persists workflow state. Stage-specific logic is split across `agents/` (analysis, planning, scene generation, video generation, evaluation, composition). External provider wrappers and media utilities live in `tools/`. Shared schemas are in `models/`, cross-cutting helpers in `utils/`, and runtime/config defaults in `config/`. Root-level prompt files such as `system_prompt_video_gen.md` support generation behavior. Runtime folders like `state/`, `output/`, `temp/`, `logs/`, and `cache/` are created on demand.

## Build, Test, and Development Commands
Set up a local environment before changing code:

- `python3 -m venv .venv && source .venv/bin/activate` creates an isolated Python environment.
- `pip install -r requirements.txt` installs runtime dependencies.
- `cp .env.example .env` seeds required API configuration.
- `python3 main.py --help` shows CLI options.
- `python3 main.py -i samples/product.jpg -r "高端科技风格" --cta "立即购买"` runs a local smoke test with your own assets.
- `python3 main.py --list` lists saved workflow runs from `./state`.
- `PYTHONPYCACHEPREFIX=/tmp/video_agent_pycache python3 -m compileall agents config models orchestrator tools utils main.py` performs a fast syntax check.

## Coding Style & Naming Conventions
Follow existing Python conventions: 4-space indentation, snake_case for modules/functions, PascalCase for classes, and explicit type hints on public functions. Keep async workflow boundaries in `main.py`, `orchestrator/`, and `agents/`. Put provider-specific API calls in `tools/`, not directly in orchestration code. Reuse `config/settings.py` and `config/api_keys.py` for new configuration instead of hardcoding values.

## Testing Guidelines
There is no committed `tests/` suite yet. Add new tests under `tests/test_<module>.py` and prefer `pytest` style assertions. Mock external LLM, image, and video providers at the `tools/` layer. Before opening a PR, run the syntax check above and at minimum smoke-test `python3 main.py --help` or `python3 main.py --list`.

## Commit & Pull Request Guidelines
Git history is currently minimal and uses a short subject (`video agent`). Keep commit subjects concise and imperative, for example `add retry handling for video generation`. PRs should explain workflow impact, note any new environment variables, and list manual verification steps. Include screenshots, logs, or sample output paths when a change affects generated media or CLI behavior.

## Security & Configuration Tips
Keep secrets only in `.env`; never commit live API keys. If you add a provider, update both `.env.example` and `config/api_keys.py`. Avoid committing generated videos, logs, caches, or state files unless they are deliberate fixtures.
