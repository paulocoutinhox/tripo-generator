from tripo import generate_item

PROMPT = "Closed antique oak treasure chest, aged dark wood planks with deep grain, small cracks and worn edges, curved barrel lid, hand-forged iron bands with light rust, hammered rivets and corner brackets, heavy iron hinges, ornate brass lock plate with a keyhole and green patina"

if __name__ == "__main__":
    generate_item(prompt=PROMPT, output="assets/realistic-chest.glb", profile="realistic", face_limit=100000)
