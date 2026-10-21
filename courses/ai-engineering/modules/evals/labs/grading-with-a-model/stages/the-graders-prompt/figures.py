import json

LIKELIEST = 20


def figures():
    with open("data/tokenizer_config.json", encoding="utf-8") as file:
        template = json.load(file)["chat_template"]
    return {
        "likeliest": str(LIKELIEST),
        "template_lines": str(len(template.splitlines())),
    }
