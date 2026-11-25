# Tripo Generator

## Purpose and capabilities

Tripo Generator creates textured static items and rigged, animated humanoid characters as self-contained GLB files from text prompts through the Tripo API v3. Static items and animated characters can also be generated from a PNG or JPEG reference image. It offers a `cartoon` profile with a cozy, cute casual-game look, Ultra geometry and HD textures, and a `realistic` profile with detailed geometry, PBR surfaces and 8K textures. Characters get a rig check, a Mixamo-compatible biped rig and up to five retargeted, renamed animation clips.

## Architecture and repository map

- `tripo.py` holds the whole shared functional API: HTTP requests, image upload, task polling, payload building, the item and character pipelines, GLB reading and writing, clip renaming and structural validation. It uses only the Python standard library.
- `examples/` holds one runnable script per example. Each script defines its prompt or reference image and calls `generate_item`, `generate_item_from_image`, `generate_character` or `generate_character_from_image`. The Makefile runs them with `PYTHONPATH=.` so they import `tripo` from the root.
- `examples/images/` holds reference images for the image-to-3D examples.
- `tests/test_tripo.py` holds offline tests with mocked API calls and synthetic GLB fixtures.
- `assets/` receives generated models and recovery files. Only `assets/.gitkeep` is tracked.
- `extras/images/` holds the README logo.
- `.github/` holds funding, issue and pull request templates and the test workflow.

The only external integration is the Tripo HTTP API at `https://openapi.tripo3d.ai/v3`, authenticated with `TRIPO_API_KEY` from `.env`.

## Development commands

```bash
make install                  # uv sync --locked --all-groups and create .env from .env.example
make lint                     # ruff check and ruff format --check
make format                   # ruff check --fix and ruff format
make test                     # offline unittest suite
make balance                  # live account balance request
make character-cartoon        # paid generation
make character-realistic      # paid generation
make item-cartoon             # paid generation
make item-realistic           # paid generation
make item-image-cartoon       # paid generation from examples/images/cartoon-chest.png
make character-image-cartoon  # paid generation from examples/images/cartoon-knight.png
```

## Code standards

- Use uv and Python 3.12+. Keep Python identifiers, code comments and project documentation in English.
- Ruff is configured in `pyproject.toml` with `line-length = 320`, `skip-magic-trailing-comma = true` and `split-on-trailing-comma = false`. Keep each function call, signature and string literal on one line. Name long argument expressions first instead of wrapping calls.
- Separate validation, computation, I/O and return steps with blank lines. Prefer early returns.
- Keep the shared functional API in `tripo.py` and runnable examples in `examples/` with hyphenated filenames.
- Comments are rare, in complete English sentences, and explain intent.
- Preserve embedded binary data when renaming GLB clips. Never guess the order of unidentified multi-clip animations. Keep `attack` as the public name for `preset:slash`.
- Keep static items free of animation and animated characters rigged. Preserve original downloads on failure.
- Keep each combined prompt (prompt, character pose, profile style and asset suffix) at most 1024 characters.

## Validation and delivery

- Run `make lint` and `make test` before finishing changes. Tests must be offline and must not consume API credits.
- Do not run paid generation without explicit approval. Do not automatically retry paid POST requests.
- Check official Tripo documentation before changing endpoints, versions, payloads or pricing.
- Never commit `.env`, API keys, generated assets or recovery files. Never print authorization headers.
- Document limitations and distinguish mock tests from real API tests.
- Keep a single commit on GitHub: amend the existing commit and push with an explicit lease.
