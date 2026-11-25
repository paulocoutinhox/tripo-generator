from pathlib import Path

from tripo import generate_character_from_image

IMAGE = Path(__file__).parent / "images" / "cartoon-knight.png"

if __name__ == "__main__":
    generate_character_from_image(image=IMAGE, output="assets/image-cartoon-knight.glb", profile="cartoon")
