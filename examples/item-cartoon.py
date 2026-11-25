from tripo import generate_item

PROMPT = "Cute closed treasure chest with a big rounded golden-yellow lock plate and keyhole centered on the front, rounded barrel lid, chunky compact proportions, warm medium-brown wooden planks with light honey-brown highlights and simple straight grooves, thick rounded warm golden-yellow painted trim bands over the lid and around the base, rounded golden-yellow corner caps with small round studs"

if __name__ == "__main__":
    generate_item(prompt=PROMPT, output="assets/cartoon-chest.glb", profile="cartoon")
