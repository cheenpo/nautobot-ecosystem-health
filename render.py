from jinja2 import Environment, FileSystemLoader, select_autoescape
from ruamel.yaml import YAML
from rich import print

import os

yaml = YAML(typ="safe")
with open("data.yaml") as data_file:
    data = yaml.load(data_file.read())

print(data)

env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())

template = env.get_template("index.html.j2")

output_path = "output"

if not os.path.exists(output_path):
    os.makedirs(output_path)

with open(
    os.path.join(
        output_path,
        "index.html",
    ),
    "w",
) as output_file:
    output_file.write(template.render(data))
