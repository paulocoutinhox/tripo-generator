from tripo import generate_character

PROMPT = "Cute heroic young fantasy knight with chunky stylized proportions, smooth sky-blue painted armor with soft golden-yellow trim, simple rounded open-face helmet with a short red crest, royal-blue tabard with a golden-yellow lion emblem, brown leather belt with a golden-yellow buckle, orange leather gloves and boots, friendly face with big expressive eyes and a confident smile"

if __name__ == "__main__":
    generate_character(prompt=PROMPT, output="assets/cartoon-knight.glb", profile="cartoon")
