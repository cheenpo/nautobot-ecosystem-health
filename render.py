"""Generates status pages for the Nautobot Ecosystem."""

import os
from datetime import datetime, timedelta, timezone

import requests_cache
from jinja2 import Environment, FileSystemLoader, select_autoescape

from utils import (
    generate_page,
    get_github_latest_release,
    get_github_upstream_testing_results,
    get_pypi_data,
    get_yaml_data,
    log,
)

# GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

DATA = get_yaml_data("data.yaml")
JINJA_ENV = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())
OUTPUT_PATH = "output"
# Add filesystem based caching of requests API calls (mostly for development)
REQUESTS_CACHE_PATH = "./.cache/requests.sqlite"
DEFAULT_EXPIRE_AFTER = timedelta(hours=2)
URLS_EXPIRE_AFTER = {
    "https://api.github.com/repos/nautobot/pynautobot/actions/runs/*/jobs": timedelta(days=90)
}
requests_cache.install_cache(
    REQUESTS_CACHE_PATH,
    backend="sqlite",
    expire_after=DEFAULT_EXPIRE_AFTER,
    urls_expire_after=URLS_EXPIRE_AFTER,
)


if __name__ == "__main__":
    build_start = datetime.now(timezone.utc)
    build_timestamp = build_start.strftime("%Y-%m-%d %H:%M:%S %Z")

    github_upstream_data = {}
    github_release_data = {}
    pypi_data = {}
    for name, data in DATA["metadata"].items():
        log.info(f"Fetching API data for {data['repo']} ...")
        if name in DATA["pages"]["upstream"]:
            github_upstream_data[data["repo"]] = get_github_upstream_testing_results(data)
        if data.get("pypi"):
            pypi_data[data["repo"]] = get_pypi_data(data)
        if name in DATA["pages"]["status.nautobot"]:
            github_release_data[data["repo"]] = get_github_latest_release(data)

    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    log.info("Generating index.html ...")
    generate_page(
        "index.html",
        JINJA_ENV,
        OUTPUT_PATH,
        pypi=pypi_data,
        build_timestamp=build_timestamp,
        gh_releases=github_release_data,
        **DATA,
    )

    log.info("Generating badges-nautobot.html ...")
    generate_page("badges-nautobot.html", JINJA_ENV, OUTPUT_PATH, **DATA)

    log.info("Generating badges-ntc.html ...")
    generate_page("badges-ntc.html", JINJA_ENV, OUTPUT_PATH, **DATA)

    log.info("Generating upstream.html ...")
    generate_page(
        "upstream.html",
        JINJA_ENV,
        OUTPUT_PATH,
        upstream=github_upstream_data,
        build_timestamp=build_timestamp,
        **DATA,
    )

    log.info(f"Build finished in: {datetime.now(timezone.utc) - build_start}")
