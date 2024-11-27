"""Generates status pages for the Nautobot Ecosystem."""

import os
from datetime import datetime, timezone

import requests_cache
from jinja2 import Environment, FileSystemLoader, select_autoescape

import utils

PROJECTS = utils.get_yaml_data("data.yaml")
JINJA_ENV = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())
OUTPUT_PATH = "output"
# Add filesystem based caching of requests API calls (mostly for development)
REQUESTS_CACHE_PATH = "./.cache"
requests_cache.install_cache(REQUESTS_CACHE_PATH, backend="filesystem", expire_after=3600)


if __name__ == "__main__":
    upstream_data = {}
    pypi_data = {}
    for project in PROJECTS["nautobot"]:
        upstream_data[project["repo"]] = utils.get_github_upstream_testing_results(project)
        pypi_data[project["repo"]] = utils.get_pypi_data(project)

    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    build_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")

    utils.generate_page(
        "index.html",
        JINJA_ENV,
        OUTPUT_PATH,
        projects=PROJECTS,
        pypi=pypi_data,
        build_timestamp=build_timestamp,
    )
    utils.generate_page("badges.html", JINJA_ENV, OUTPUT_PATH, projects=PROJECTS)
    utils.generate_page(
        "upstream.html",
        JINJA_ENV,
        OUTPUT_PATH,
        projects=PROJECTS,
        upstream=upstream_data,
        build_timestamp=build_timestamp,
    )
