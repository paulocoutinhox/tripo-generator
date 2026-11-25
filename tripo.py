"""Tripo API v3 asset generation using only the Python standard library."""

import json
import os
import re
import shutil
import struct
import sys
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API_URL = "https://openapi.tripo3d.ai/v3"
MODEL_VERSION = "v3.1-20260211"
TEXTURE_VERSION = "v3.5-20260815"
RIG_VERSION = "v3.0-20260909"
CARTOON_STYLE = "Cozy cute stylized 3D game asset in a polished casual mobile game style, soft toy-like look, chunky rounded proportions, smooth clean surfaces, thick soft rounded bevels on every edge, simple bold readable shapes, warm bright cheerful colors, clean color zones with soft painted highlights and gentle warm gradients, matte and satin painted materials"
CARTOON_NEGATIVE_PROMPT = "metallic, chrome, mirror reflections, photorealistic, dark muddy colors, lumpy, blobby, melted, dents, hammered metal, wrinkles, uneven surfaces, noisy texture, rough brush strokes, grime, scratches, sharp edges, floating fragments, mesh artifacts"
REALISTIC_STYLE = "Photorealistic, realistic proportions, detailed PBR surfaces, 8K textures"
REALISTIC_NEGATIVE_PROMPT = "cartoon, stylized, toy-like, blobby or melted shapes, wobbly surfaces, floating fragments, holes, mesh artifacts, jagged edges, blurry or low-resolution texture, baked shadows"
ASSET_SUFFIX = "Single complete isolated asset made of solid closed shapes, no background or ground plane."
PROFILES = {
    "cartoon": {"style": CARTOON_STYLE, "negative_prompt": CARTOON_NEGATIVE_PROMPT, "geometry_quality": "detailed", "texture_quality": "detailed", "face_limit": 100000, "delight": False, "estimated_cents": 50},
    "realistic": {"style": REALISTIC_STYLE, "negative_prompt": REALISTIC_NEGATIVE_PROMPT, "geometry_quality": "detailed", "texture_quality": "extreme", "face_limit": 150000, "delight": True, "estimated_cents": 60},
}
DEFAULT_ANIMATIONS = {name: f"preset:{name}" for name in ("idle", "walk", "run", "jump")}
DEFAULT_ANIMATIONS["attack"] = "preset:slash"
PRESETS = {f"preset:{name}" for name in "idle walk run dive climb jump slash shoot hurt fall turn".split()}
CHARACTER_POSE = "Full-body humanoid, symmetrical T-pose, arms horizontal, legs apart, visible hands and feet"
JSON_CHUNK = 0x4E4F534A
TASK_LABELS = {"/generation/text-to-model": "Model generation", "/generation/image-to-model": "Model generation from image", "/animations/rig-check": "Rig check", "/animations/rig": "Rigging", "/animations/retarget": "Animation retargeting"}
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
MAX_IMAGE_BYTES = 20 * 1024 * 1024
IMAGE_SOURCE_CENTS = 10


def request(method, endpoint, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    return send(method, endpoint, body, "application/json")


def upload_image(image_path):
    boundary = uuid.uuid4().hex
    content_type = IMAGE_TYPES[image_path.suffix.lower()]
    header = f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="image{image_path.suffix.lower()}"\r\nContent-Type: {content_type}\r\n\r\n'
    footer = f"\r\n--{boundary}--\r\n"
    body = header.encode() + image_path.read_bytes() + footer.encode()

    print("Uploading the reference image.", flush=True)
    return send("POST", "/files", body, f"multipart/form-data; boundary={boundary}")["file_token"]


def send(method, endpoint, body, content_type):
    key = os.environ.get("TRIPO_API_KEY")
    if not key:
        raise RuntimeError("Set TRIPO_API_KEY before generating assets")

    headers = {"Authorization": f"Bearer {key}", "Content-Type": content_type}
    req = Request(API_URL + endpoint, method=method, data=body, headers=headers)

    try:
        with urlopen(req, timeout=60) as response:
            result = json.load(response)
    except HTTPError as exc:
        details = exc.read(4096).decode(errors="replace")
        raise RuntimeError(f"Tripo HTTP {exc.code}: {details}") from None

    if result.get("code") != 0:
        raise RuntimeError(f"Tripo API error: {result}")

    return result["data"]


def get_balance():
    return request("GET", "/account/balance")


def wait_task(task_id, label="Task", timeout=1800):
    deadline = time.monotonic() + timeout
    last_report = None

    while time.monotonic() < deadline:
        task = request("GET", f"/tasks/{task_id}")
        status = task["status"]
        progress = task.get("progress", 0)

        report = (status, progress)
        if report != last_report:
            print(f"{label}: {status} ({progress}%)", flush=True)
            last_report = report

        if status == "success":
            return {**task, "task_id": task_id}

        if status not in {"queued", "running", "pending"}:
            raise RuntimeError(f"{label} task {task_id} ended with status {status}: {task}")

        time.sleep(5)

    raise TimeoutError(f"{label} task {task_id} timed out. Query the existing task before submitting it again.")


def execute_task(endpoint, payload):
    label = TASK_LABELS[endpoint]
    task_id = request("POST", endpoint, payload)["task_id"]
    print(f"{label} started (task {task_id}).", flush=True)
    return wait_task(task_id, label)


def quality_payload(profile, face_limit=None):
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")

    settings = PROFILES[profile]
    faces = settings["face_limit"] if face_limit is None else face_limit
    max_faces = 2000000 if settings["geometry_quality"] == "detailed" else 1500000
    if type(faces) is not int or not 1 <= faces <= max_faces:
        raise ValueError("Invalid face limit")

    return dict(model=MODEL_VERSION, texture_version=TEXTURE_VERSION, texture=True, pbr=True, geometry_quality=settings["geometry_quality"], texture_quality=settings["texture_quality"], face_limit=faces, auto_size=True, quad=False, delight=settings["delight"])


def model_payload(prompt, profile, face_limit=None):
    quality = quality_payload(profile, face_limit)
    settings = PROFILES[profile]

    full_prompt = f"{prompt}. {settings['style']}. {ASSET_SUFFIX}"
    if not prompt.strip() or len(full_prompt) > 1024:
        raise ValueError("Prompt must be nonempty and combined prompt at most 1024 characters")

    if len(settings["negative_prompt"]) > 255:
        raise ValueError("Negative prompt must be at most 255 characters")

    return dict(prompt=full_prompt, negative_prompt=settings["negative_prompt"], **quality)


def image_model_payload(profile, face_limit=None):
    quality = quality_payload(profile, face_limit)
    return dict(orientation="align_image", **quality)


def validate_image(image):
    image_path = Path(image)
    if not image_path.is_file():
        raise FileNotFoundError(f"The image {image_path} does not exist.")

    if image_path.suffix.lower() not in IMAGE_TYPES:
        raise ValueError(f"The image {image_path} must be a PNG or JPEG file.")

    if image_path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError(f"The image {image_path} is larger than 20 MB.")

    return image_path


def read_glb(path):
    data = Path(path).read_bytes()
    if len(data) < 20 or struct.unpack_from("<4sII", data) != (b"glTF", 2, len(data)):
        raise ValueError("Invalid GLB header")

    chunks = []
    offset = 12
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError("Truncated chunk header")

        size, kind = struct.unpack_from("<II", data, offset)
        offset += 8
        if size % 4 or offset + size > len(data):
            raise ValueError("Invalid GLB chunk size")

        chunks.append((kind, data[offset : offset + size]))
        offset += size

    if chunks[0][0] != JSON_CHUNK:
        raise ValueError("Missing JSON chunk")

    return json.loads(chunks[0][1]), chunks[1:]


def write_glb(path, document, chunks):
    raw = json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode()
    raw += b" " * (-len(raw) % 4)
    all_chunks = [(JSON_CHUNK, raw), *chunks]
    total_length = 12 + sum(8 + len(blob) for _, blob in all_chunks)

    with Path(path).open("wb") as file:
        file.write(struct.pack("<4sII", b"glTF", 2, total_length))
        for kind, blob in all_chunks:
            file.write(struct.pack("<II", len(blob), kind))
            file.write(blob)


def rename_animations(path, animations):
    doc, chunks = read_glb(path)
    clips = doc.get("animations", [])
    if len(clips) != len(animations):
        raise ValueError(f"Expected {len(animations)} clips, got {len(clips)}")

    mapped = {}
    for clip in clips:
        name = clip.get("name", "") or ""
        tokens = set(re.findall(r"[a-z]+", name.lower()))
        matches = [target for target, preset in animations.items() if target.lower() in tokens or preset.split(":")[-1] in tokens]

        # A single-preset export is unambiguous even if the exporter omits its name.
        if len(animations) == 1:
            matches = list(animations)

        if len(matches) != 1 or matches[0] in mapped:
            raise ValueError(f"Animation clip {name!r} is ambiguous. The original download was preserved.")

        clip["name"] = matches[0]
        mapped[matches[0]] = clip

    doc["animations"] = [mapped[name] for name in animations]
    write_glb(path, doc, chunks)


def validate_model(path, animations=None):
    doc, _ = read_glb(path)

    fields = ["meshes", "materials", "textures", "images"]
    if animations is not None:
        fields += ["skins", "animations"]

    for field in fields:
        if not doc.get(field):
            raise ValueError(f"Missing GLB field: {field}")

    for image in doc["images"]:
        if "bufferView" not in image and not (image.get("uri") or "").startswith("data:"):
            raise ValueError("External or missing texture")

    for buffer in doc.get("buffers", []):
        if buffer.get("uri") and not buffer["uri"].startswith("data:"):
            raise ValueError("External buffer")

    names = [clip.get("name") for clip in doc.get("animations", [])]
    if names != list(animations or {}):
        raise ValueError(f"Unexpected animation names: {names}")

    return {"meshes": len(doc["meshes"]), "textures": len(doc["textures"]), "animations": names}


def download_model(task, output):
    url = task["output"]["model_url"]
    if not url.startswith("https://"):
        raise ValueError("Expected HTTPS download URL")

    with urlopen(url, timeout=300) as response, Path(output).open("wb") as file:
        shutil.copyfileobj(response, file, 1024 * 1024)


def validate_animations(animations):
    if not 1 <= len(animations) <= 5 or len(set(animations.values())) != len(animations):
        raise ValueError("Specify 1–5 unique presets")

    for name, preset in animations.items():
        if not isinstance(name, str) or not name.strip() or preset not in PRESETS:
            raise ValueError("Invalid animation name or biped preset")


def confirm_overwrite(path):
    if not sys.stdin.isatty():
        raise FileExistsError(f"The file {path} already exists. Run the command in a terminal to confirm replacing it.")

    answer = input(f"The file {path} already exists. Replace it once the new model is ready? [y/N] ")
    return answer.strip().lower() in {"y", "yes"}


def generate(output, profile, face_limit, prompt=None, image=None, animations=None):
    path = Path(output)
    if path.suffix.lower() != ".glb":
        raise ValueError("Output must use .glb")

    if image is None:
        endpoint = "/generation/text-to-model"
        payload = model_payload(prompt, profile, face_limit)
        source_cents = 0
    else:
        endpoint = "/generation/image-to-model"
        image_path = validate_image(image)
        payload = image_model_payload(profile, face_limit)
        source_cents = IMAGE_SOURCE_CENTS

    if animations is not None:
        validate_animations(animations)

    if path.exists() and not confirm_overwrite(path):
        print(f"Generation canceled. The existing file {path} was kept.")
        return None

    path.parent.mkdir(parents=True, exist_ok=True)
    raw = path.with_suffix(".glb.part")
    edited = path.with_suffix(".glb.edited.part")
    if raw.exists() or edited.exists():
        raise FileExistsError(f"A recovery file from an earlier run exists next to {path}. Inspect it before running again.")

    animation_cents = 25 + 10 * len(animations) if animations is not None else 0
    estimated = PROFILES[profile]["estimated_cents"] + source_cents + animation_cents
    print(f"Estimated cost: ${estimated / 100:.2f} USD.", flush=True)

    if image is not None:
        payload["input"] = upload_image(image_path)

    tasks = [execute_task(endpoint, payload)]
    if animations is not None:
        model_id = tasks[0]["task_id"]

        check = execute_task("/animations/rig-check", {"input": model_id})
        tasks.append(check)
        if not check["output"].get("riggable") or check["output"].get("rig_type") != "biped":
            raise RuntimeError(f"The model from task {model_id} is not a riggable biped.")

        rig_payload = dict(input=model_id, model=RIG_VERSION, rig_type="biped", spec="mixamo", out_format="glb")
        rig = execute_task("/animations/rig", rig_payload)
        tasks.append(rig)

        retarget_payload = dict(input=rig["task_id"], animations=list(animations.values()), out_format="glb", export_with_geometry=True, animate_in_place=True)
        tasks.append(execute_task("/animations/retarget", retarget_payload))

    print("Downloading the model.", flush=True)
    download_model(tasks[-1], raw)
    candidate = raw
    if animations is not None:
        shutil.copyfile(raw, edited)
        rename_animations(edited, animations)
        candidate = edited

    metadata = validate_model(candidate, animations)
    candidate.replace(path)
    raw.unlink(missing_ok=True)

    costs = [task.get("credits_consumed") for task in tasks]
    credits_consumed = sum(map(float, costs)) if all(cost is not None for cost in costs) else None
    task_ids = [task["task_id"] for task in tasks]
    result = dict(file=str(path), profile=profile, estimated_usd=estimated / 100, credits_consumed=credits_consumed, task_ids=task_ids, **metadata)
    print(f"Saved {path}.", flush=True)
    print(json.dumps(result, indent=2))
    return result


def generate_item(prompt, output, profile="cartoon", face_limit=None):
    return generate(output, profile, face_limit, prompt=prompt)


def generate_item_from_image(image, output, profile="cartoon", face_limit=None):
    return generate(output, profile, face_limit, image=image)


def generate_character(prompt, output, profile="cartoon", animations=None, face_limit=None):
    character_prompt = f"{prompt}. {CHARACTER_POSE}"
    selected_animations = dict(DEFAULT_ANIMATIONS if animations is None else animations)
    return generate(output, profile, face_limit, prompt=character_prompt, animations=selected_animations)


def generate_character_from_image(image, output, profile="cartoon", animations=None, face_limit=None):
    selected_animations = dict(DEFAULT_ANIMATIONS if animations is None else animations)
    return generate(output, profile, face_limit, image=image, animations=selected_animations)
