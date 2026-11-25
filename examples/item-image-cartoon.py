from pathlib import Path

from tripo import generate_item_from_image

IMAGE = Path(__file__).parent / "images" / "cartoon-chest.png"

if __name__ == "__main__":
    generate_item_from_image(image=IMAGE, output="assets/image-cartoon-chest.glb", profile="cartoon")
