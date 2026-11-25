<p align="center">
    <a href="https://github.com/paulocoutinhox/tripo-generator" target="_blank" rel="noopener noreferrer">
        <img width="420" src="extras/images/logo.svg" alt="Tripo Generator">
    </a>
</p>

<p align="center">
  <a href="https://github.com/paulocoutinhox/tripo-generator/actions/workflows/test.yml"><img src="https://github.com/paulocoutinhox/tripo-generator/actions/workflows/test.yml/badge.svg" alt="Tripo Generator - Test"></a>
  <a href="https://github.com/paulocoutinhox/tripo-generator/blob/main/LICENSE.md"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.12%20|%203.13%20|%203.14-blue.svg" alt="Python versions"></a>
  <a href="https://developers.tripo3d.ai/"><img src="https://img.shields.io/badge/Tripo%20API-v3-6854ed.svg" alt="Tripo API v3"></a>
</p>

<p align="center">
Generate textured static items and rigged, animated humanoid characters as GLB files from text prompts using the Tripo API v3.
</p>

<br>

## 🚀 Project

Tripo Generator turns a text prompt into a self-contained **GLB** model, ready for game engines and 3D tools. Static items come out textured and free of animation. Humanoid characters come out rigged as Mixamo-compatible bipeds with named animation clips.

Everything lives in one functional Python module, [tripo.py](tripo.py), built only on the standard library. No Blender or MCP is required. The Tripo API v3 documentation was checked on 2026-11-25.

## ✨ Features

- [x] Text-to-3D generation of static items and humanoid characters
- [x] Image-to-3D generation of static items and rigged, animated characters from a PNG or JPEG reference image
- [x] `cartoon` profile with a cozy, cute casual-game look: chunky rounded shapes, soft bevels, warm cheerful colors, soft painted highlights, Ultra geometry and HD textures
- [x] `realistic` profile with detailed geometry, PBR surfaces and 8K textures
- [x] Free rig check, Mixamo-compatible biped rig and up to five retargeted clips
- [x] Default clips `idle`, `walk`, `run`, `jump` and `attack` (`preset:slash`), requested in place
- [x] Clip renaming that preserves embedded binary data and never guesses the order of unidentified clips
- [x] Structural GLB validation of meshes, materials, embedded textures and buffers, skins and clip names
- [x] Estimated USD cost printed before every paid operation, plus the raw `credits_consumed` from the API
- [x] Safe recovery: task IDs printed immediately, no overwritten outputs and original downloads kept on failure
- [x] Zero runtime dependencies
- [x] Offline test suite that never consumes API credits

## 📦 Install

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and GNU Make. Python 3.12 is selected by `.python-version`, and Python 3.12+ is supported.

```bash
git clone https://github.com/paulocoutinhox/tripo-generator.git
cd tripo-generator
make install
```

`make install` syncs the environment and creates `.env` from `.env.example`. Edit `.env` and set `TRIPO_API_KEY` to your developer API key from the [Tripo developer platform](https://developers.tripo3d.ai/).

## 💡 How to use

Run any example. Each one is a **paid** operation:

```bash
make character-cartoon
make character-realistic
make item-cartoon
make item-realistic
make item-image-cartoon
make character-image-cartoon
```

| Example | Script | Output | USD |
|---|---|---|---:|
| Character cartoon HD | [examples/character-cartoon.py](examples/character-cartoon.py) | `assets/cartoon-knight.glb` | 1.25 |
| Character realistic 8K | [examples/character-realistic.py](examples/character-realistic.py) | `assets/realistic-knight.glb` | 1.35 |
| Item cartoon HD | [examples/item-cartoon.py](examples/item-cartoon.py) | `assets/cartoon-chest.glb` | 0.50 |
| Item realistic 8K | [examples/item-realistic.py](examples/item-realistic.py) | `assets/realistic-chest.glb` | 0.60 |
| Item from image cartoon HD | [examples/item-image-cartoon.py](examples/item-image-cartoon.py) | `assets/image-cartoon-chest.glb` | 0.60 |
| Character from image cartoon HD | [examples/character-image-cartoon.py](examples/character-image-cartoon.py) | `assets/image-cartoon-knight.glb` | 1.35 |

The total is $5.65 at the documented November 2026 prices, excluding taxes, retries and other operations. The API changes its billing display to USD on December 1, 2026. Check your usage history for authoritative billing.

The example prompts describe shapes, colors and materials explicitly. Cartoon prompts favor cute chunky proportions, warm wood and golden-yellow painted trim, and the cartoon profile adds a cozy casual-game look and a negative prompt against metallic, chrome, lumpy and noisy results. Realistic prompts describe worn materials, metals and surface details.

The image examples use [examples/images/cartoon-chest.png](examples/images/cartoon-chest.png) and [examples/images/cartoon-knight.png](examples/images/cartoon-knight.png) as references. Image-to-3D takes its shapes and colors from the reference instead of a prompt, which helps when you already have concept art for the look you want. Use a clean image of one object on a plain background, and a front-facing T-pose for characters.

Use the API from your own code:

```python
from tripo import generate_character, generate_item

generate_item("Bright red wooden barrel with glossy gold bands and a lime-green painted lid", "assets/barrel.glb", profile="cartoon")

generate_character("Fantasy knight in polished steel armor with a dark blue surcoat", "assets/knight.glb", profile="realistic", animations={"idle": "preset:idle", "attack": "preset:slash"})
```

| Function | Purpose |
|---|---|
| `generate_item(prompt, output, profile="cartoon", face_limit=None)` | Static textured model, no rig or animation. |
| `generate_item_from_image(image, output, profile="cartoon", face_limit=None)` | Static textured model from a PNG or JPEG reference image, up to 20 MB. |
| `generate_character_from_image(image, output, profile="cartoon", animations=None, face_limit=None)` | Rigged biped with up to five named clips from a PNG or JPEG reference image. |
| `generate_character(prompt, output, profile="cartoon", animations=None, face_limit=None)` | Rigged biped with up to five named clips. |
| `get_balance()` | Account balance. |
| `wait_task(task_id)` | Polls an existing task, useful for recovery. |

Available biped presets: `idle`, `walk`, `run`, `dive`, `climb`, `jump`, `slash`, `shoot`, `hurt`, `fall` and `turn`, each written as `preset:<name>`. Each combined prompt, including the profile style and character pose, must stay at most 1024 characters.

## 🧬 Profiles and pipelines

| Profile | Style | Geometry | Texture | Default faces |
|---|---|---|---|---:|
| `cartoon` | Cozy cute casual-game look, chunky rounded shapes, soft bevels, warm colors, soft painted highlights, matte painted materials | detailed (Ultra) | detailed (HD) | 100,000 |
| `realistic` | Photorealistic proportions, detailed PBR surfaces | detailed | extreme (8K) | 150,000 |

- **Item pipeline**: generate a textured model, download it and validate it. Rigging and animation are skipped.
- **Image item pipeline**: upload the reference image, generate a textured model from it with the same profile quality settings, then download and validate it. Image-to-model takes no prompt or negative prompt, so the image defines the look. The model is aligned with the image view.
- **Image character pipeline**: upload the reference image, generate the model from it, then run the same rig check, rigging, retargeting, renaming and validation as the character pipeline. The image should show one full-body humanoid in a T-pose with visible hands and feet. Capes, loose cloth and held props can make rigging fail or deform badly.
- **Character pipeline**: generate a textured model, run a free rig check, rig it as a Mixamo-compatible biped, retarget the requested clips, then download, rename and validate.

Both profiles send a negative prompt. Cartoon keeps soft painted lighting in its textures for a warm hand-crafted look and steers away from metallic and chrome surfaces. Realistic requests delighted textures so lighting comes from your engine. Outputs use embedded textures and buffers. Actual texture resolution, topology, PBR map coverage, rigging and visual quality are not guaranteed by the local structural checks.

## ⚙️ Commands

```bash
make install               # sync the environment and create .env
make test                  # run the offline test suite
make lint                  # check the code with Ruff
make format                # format and fix the code with Ruff
make balance               # show the Tripo account balance
```

Without Make, run `uv sync --locked --all-groups`, copy `.env.example` to `.env`, then `PYTHONPATH=. uv run --env-file .env python examples/item-cartoon.py` (or any other example).

## 🛟 Recovery and limitations

- Task IDs are printed immediately. Do not blindly repeat a paid POST after a timeout. Query the existing task with `wait_task(task_id)` first.
- If the output already exists, you are asked to confirm before any paid request. Declining cancels the run without generating anything, and the function returns `None`. The existing file is only replaced after the new download passes validation. Non-interactive runs refuse to overwrite it.
- Downloads remain as `.glb.part` on validation failure, and edited copies may remain as `.glb.edited.part`. Inspect recovered files before deleting them or retrying.
- The original download is preserved if clip names cannot be matched.
- Multi-clip exports must have identifiable names. The project deliberately does not guess clip order. A single requested clip can safely be named directly.
- The standard-library GLB editor reads the whole file into memory. Make sure you have enough RAM for 8K assets.
- No generated models are bundled in this repository.

## 🧪 Testing

```bash
make test
```

Tests run offline against mock API responses and synthetic GLB fixtures, and never consume API credits. Actual paid generation requires your API key and is not covered by live tests.

## 📚 Documentation

- [Text to model](https://developers.tripo3d.ai/en/docs/generation-text-to-model/standard)
- [Rig check](https://developers.tripo3d.ai/en/docs/animations-rig-check)
- [Rig](https://developers.tripo3d.ai/en/docs/animations-rig)
- [Retarget](https://developers.tripo3d.ai/en/docs/animations-retarget)
- [Pricing](https://developers.tripo3d.ai/en/pricing)
- [Agent contract](AGENTS.md)

## 🤝 Contributing

Read [AGENTS.md](AGENTS.md). Keep tests offline, never commit `.env`, API keys or generated assets, and document which behavior was tested with mocks and which against the live API.

## ☕ Buy me a coffee

Support the continuous development of this project.

<a href="https://ko-fi.com/A0A412XEV" target="_blank" rel="noopener noreferrer"><img height="36" style="border:0;height:36px;" src="https://storage.ko-fi.com/cdn/kofi2.png?v=6" alt="Buy Me a Coffee at ko-fi.com"></a>

## 📄 License

[MIT](LICENSE.md). Copyright © 2026 Paulo Coutinho.

Tripo Generator is an independent project and is not affiliated with Tripo. Tripo is a trademark of its respective owner.
