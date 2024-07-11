from jinja2 import Environment, FileSystemLoader, select_autoescape
from ruamel.yaml import YAML
from rich import print

yaml = YAML(typ="safe")
with open("data.yaml") as data_file:
    data = yaml.load(data_file.read())

print(data)

env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())

template = env.get_template("index.html.j2")

print(template.render(data))
