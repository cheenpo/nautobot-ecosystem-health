from jinja2 import Environment, FileSystemLoader, select_autoescape
from ruamel.yaml import YAML
from rich import print

import os


def render_pages():
    yaml = YAML(typ="safe")
    with open("data.yaml") as data_file:
        data = yaml.load(data_file.read())

    # print(data)

    env = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())

    output_path = "output"
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    pages = {"index.html": {}, "badges.html": {}}

    for page in pages:
        with open(
            os.path.join(
                output_path,
                page,
            ),
            "w",
        ) as output_file:
            template = env.get_template(f"{page}.j2")
            output_file.write(template.render(data))


if __name__ == "__main__":
    render_pages()
