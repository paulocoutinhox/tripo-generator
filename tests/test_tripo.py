import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import tripo


class Tests(unittest.TestCase):
    def fixture(self, path, names=()):
        doc = {"asset": {"version": "2.0"}, "meshes": [{}], "materials": [{}], "textures": [{}], "images": [{"bufferView": 0}], "buffers": [{"byteLength": 4}]}
        if names:
            doc.update(skins=[{}], animations=[{"name": name} for name in names])
        tripo.write_glb(path, doc, [(0x004E4942, b"abcd")])

    def test_profiles(self):
        self.assertEqual(tripo.model_payload("chest", "realistic")["texture_quality"], "extreme")
        cartoon = tripo.model_payload("chest", "cartoon")
        self.assertEqual(cartoon["texture_quality"], "detailed")
        self.assertEqual(cartoon["geometry_quality"], "detailed")
        self.assertFalse(cartoon["delight"])
        self.assertTrue(tripo.model_payload("chest", "realistic")["delight"])
        self.assertLessEqual(len(cartoon["negative_prompt"]), 255)
        with self.assertRaises(ValueError):
            tripo.model_payload("chest", "unknown")

    def test_rename(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.glb"
            self.fixture(path, ["Slash", "Walk", "Idle", "Run", "Jump"])
            tripo.rename_animations(path, tripo.DEFAULT_ANIMATIONS)
            self.assertEqual(tripo.validate_model(path, tripo.DEFAULT_ANIMATIONS)["animations"], list(tripo.DEFAULT_ANIMATIONS))
            self.assertEqual(tripo.read_glb(path)[1][0][1], b"abcd")

    def test_ambiguous(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.glb"
            self.fixture(path, ["unknown", "walk"])
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                tripo.rename_animations(path, {"attack": "preset:slash", "walk": "preset:walk"})
            self.assertEqual(path.read_bytes(), before)

    def test_character_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "character.glb"

            def task(endpoint, payload):
                return {"task_id": endpoint, "output": {"riggable": True, "rig_type": "biped"}}

            with patch.object(tripo, "execute_task", side_effect=task) as api, patch.object(tripo, "download_model", side_effect=lambda task, dest: self.fixture(dest, ["idle", "walk", "run", "jump", "slash"])):
                result = tripo.generate_character("knight", path)
            self.assertEqual(api.call_count, 4)
            self.assertEqual(result["animations"][-1], "attack")
            self.assertTrue(path.exists())

    def test_item_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "item.glb"
            with patch.object(tripo, "execute_task", return_value={"task_id": "item"}) as api, patch.object(tripo, "download_model", side_effect=lambda task, dest: self.fixture(dest)):
                result = tripo.generate_item("chest", path)
            self.assertEqual(api.call_count, 1)
            self.assertEqual(result["animations"], [])

    def test_image_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "chest.png"
            image.write_bytes(b"png")
            path = Path(tmp) / "item.glb"
            with patch.object(tripo, "upload_image", return_value="file_token") as upload, patch.object(tripo, "execute_task", return_value={"task_id": "item"}) as api, patch.object(tripo, "download_model", side_effect=lambda task, dest: self.fixture(dest)):
                result = tripo.generate_item_from_image(image, path)
            upload.assert_called_once_with(image)
            endpoint, payload = api.call_args.args
            self.assertEqual(endpoint, "/generation/image-to-model")
            self.assertEqual(payload["input"], "file_token")
            self.assertNotIn("prompt", payload)
            self.assertEqual(result["estimated_usd"], 0.6)

    def test_character_image_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "knight.png"
            image.write_bytes(b"png")
            path = Path(tmp) / "character.glb"

            def task(endpoint, payload):
                return {"task_id": endpoint, "output": {"riggable": True, "rig_type": "biped"}}

            with patch.object(tripo, "upload_image", return_value="file_token"), patch.object(tripo, "execute_task", side_effect=task) as api, patch.object(tripo, "download_model", side_effect=lambda task, dest: self.fixture(dest, ["idle", "walk", "run", "jump", "slash"])):
                result = tripo.generate_character_from_image(image, path)
            endpoints = [call.args[0] for call in api.call_args_list]
            self.assertEqual(endpoints, ["/generation/image-to-model", "/animations/rig-check", "/animations/rig", "/animations/retarget"])
            self.assertEqual(api.call_args_list[0].args[1]["input"], "file_token")
            self.assertEqual(result["animations"], list(tripo.DEFAULT_ANIMATIONS))
            self.assertEqual(result["estimated_usd"], 1.35)

    def test_image_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "item.glb"
            with patch.object(tripo, "execute_task") as api:
                with self.assertRaises(FileNotFoundError):
                    tripo.generate_item_from_image(Path(tmp) / "missing.png", path)
                unsupported = Path(tmp) / "chest.gif"
                unsupported.write_bytes(b"gif")
                with self.assertRaises(ValueError):
                    tripo.generate_item_from_image(unsupported, path)
            api.assert_not_called()

    def test_upload_body(self):
        with tempfile.TemporaryDirectory() as tmp:
            image = Path(tmp) / "chest.png"
            image.write_bytes(b"\x89PNG-bytes")
            with patch.object(tripo, "send", return_value={"file_token": "file_abc"}) as send:
                token = tripo.upload_image(image)
            method, endpoint, body, content_type = send.call_args.args
            self.assertEqual(token, "file_abc")
            self.assertEqual((method, endpoint), ("POST", "/files"))
            self.assertTrue(content_type.startswith("multipart/form-data; boundary="))
            self.assertIn(b'name="file"; filename="image.png"', body)
            self.assertIn(b"Content-Type: image/png", body)
            self.assertIn(b"\x89PNG-bytes", body)

    def test_overwrite_declined(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "item.glb"
            path.write_bytes(b"original")
            with patch.object(tripo.sys, "stdin") as stdin, patch("builtins.input", return_value="n"), patch.object(tripo, "execute_task") as api:
                stdin.isatty.return_value = True
                result = tripo.generate_item("chest", path)
            self.assertIsNone(result)
            api.assert_not_called()
            self.assertEqual(path.read_bytes(), b"original")

    def test_overwrite_confirmed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "item.glb"
            path.write_bytes(b"original")
            with patch.object(tripo.sys, "stdin") as stdin, patch("builtins.input", return_value="y"), patch.object(tripo, "execute_task", return_value={"task_id": "item"}), patch.object(tripo, "download_model", side_effect=lambda task, dest: self.fixture(dest)):
                stdin.isatty.return_value = True
                tripo.generate_item("chest", path)
            self.assertEqual(tripo.validate_model(path)["animations"], [])

    def test_overwrite_non_interactive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "item.glb"
            path.write_bytes(b"original")
            with patch.object(tripo.sys, "stdin") as stdin, patch.object(tripo, "execute_task") as api:
                stdin.isatty.return_value = False
                with self.assertRaises(FileExistsError):
                    tripo.generate_item("chest", path)
            api.assert_not_called()

    def test_invalid_glb(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.glb"
            path.write_bytes(b"bad")
            with self.assertRaises(ValueError):
                tripo.read_glb(path)


if __name__ == "__main__":
    unittest.main()
