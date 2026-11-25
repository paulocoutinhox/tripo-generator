from tripo import generate_character

PROMPT = "Battle-worn medieval knight in full steel plate armor with brushed, scratched metal, deep blue enamel panels and engraved gold trim, chainmail visible at the joints, dark blue wool surcoat with embroidered gold heraldry, brown leather straps, belt and gauntlets, scuffed leather boots, weathered middle-aged face with a short beard and a focused expression"

if __name__ == "__main__":
    generate_character(prompt=PROMPT, output="assets/realistic-knight.glb", profile="realistic")
