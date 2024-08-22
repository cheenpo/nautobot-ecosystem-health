"""Generates status pages for the Nautobot Ecosystem."""

import os
from datetime import datetime

import requests
import requests_cache
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rich.pretty import pprint as print
from ruamel.yaml import YAML


def _get_yaml_data(filename):
    """Load YAML data from a file."""
    yaml = YAML(typ="safe")
    with open(filename) as data_file:
        return yaml.load(data_file.read())


def _get_github_api_response(url, token=None):
    """Return data from GitHub JSON API."""
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=10)

    if resp.ok:
        return resp.json()
    else:
        return None


def get_github_upstream_testing_results(project):  # noqa: PLR0912 too-many-branches
    """Fetch and parse upstream testing workflow results."""
    url = f"https://api.github.com/repos/{project['org']}/{project['repo']}/actions/workflows/upstream_testing.yml/runs"
    runs_data = _get_github_api_response(url)

    print("-" * 20 + project["repo"])
    for run in runs_data["workflow_runs"]:
        run_started = datetime.fromisoformat(run["run_started_at"])
        run_ended = datetime.fromisoformat(run["updated_at"])

        # print(f"{run['run_started_at']}/{run['conclusion']}/{run['id']}/{run_ended-run_started}")

    # Find the latest successful streak
    success_streak = {"length": 0, "first_run": None, "last_run": None}
    for run in runs_data["workflow_runs"]:
        if run["conclusion"] == "success":
            if success_streak["last_run"] is None:
                success_streak["last_run"] = success_streak["first_run"] = run
                success_streak["length"] = 1
            else:
                success_streak["first_run"] = run
                success_streak["length"] += 1
        if run["conclusion"] == "failure" and success_streak["last_run"] is not None:
            break

    # Find the latest failure streak
    fail_streak = {"length": 0, "first_run": None, "last_run": None}
    for run in runs_data["workflow_runs"]:
        if run["conclusion"] == "failure":
            if fail_streak["last_run"] is None:
                fail_streak["last_run"] = fail_streak["first_run"] = run
                fail_streak["length"] = 1
            else:
                fail_streak["first_run"] = run
                fail_streak["length"] += 1
        if run["conclusion"] == "success" and fail_streak["last_run"] is not None:
            break

    if success_streak["length"]:
        print(
            f"successful streak: {success_streak['length']} from {success_streak['first_run']['id']} to {success_streak['last_run']['id']}"
        )
    if fail_streak["length"]:
        print(
            f"failed streak: {fail_streak['length']} from {fail_streak['first_run']['id']} to {fail_streak['last_run']['id']}"
        )


def render_pages():
    """Render all pages to be served."""
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
            output_file.write(template.render(projects=PROJECTS))


PROJECTS = _get_yaml_data("data.yaml")
REQUESTS_CACHE_PATH = "./.cache"
requests_cache.install_cache(REQUESTS_CACHE_PATH, backend="filesystem", expire_after=1800)


if __name__ == "__main__":
    for project in PROJECTS["nautobot"]:
        get_github_upstream_testing_results(project)
        # break
    render_pages()
