"""Generates status pages for the Nautobot Ecosystem."""

import os
import re
from datetime import datetime, timedelta, timezone

import requests
import requests_cache
from jinja2 import Environment, FileSystemLoader, select_autoescape
from ruamel.yaml import YAML


def _get_yaml_data(filename):
    """Load YAML data from a file."""
    yaml = YAML(typ="safe")
    with open(filename) as data_file:
        return yaml.load(data_file.read())


def _get_pypi_api_response(project):
    """Return data from PyPI JSON API."""
    url = f"https://pypi.python.org/pypi/{project}/json"
    headers = {"Accept": "application/json"}
    resp = requests.get(url, headers=headers, timeout=10)

    if resp.ok:
        return resp.json()
    else:
        return None


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


def _generate_page(page, **kwargs):
    """Generates a new file in memory from a Jinja template."""
    with open(
        os.path.join(
            OUTPUT_PATH,
            page,
        ),
        "w",
    ) as output_file:
        template = JINJA_ENV.get_template(f"{page}.jinja")
        output_file.write(template.render(**kwargs))


def _get_run_streak(runs, target_status, opposite_status):
    streak = {"length": 0, "first_run": None, "last_run": None}
    for run in runs:
        if run["conclusion"] == target_status:
            if streak["last_run"] is None:
                streak["last_run"] = streak["first_run"] = run
                streak["length"] = 1
            else:
                streak["first_run"] = run
                streak["length"] += 1
        if run["conclusion"] == opposite_status and streak["last_run"] is not None:
            break
    return streak


def get_github_upstream_testing_results(project):  # noqa: PLR0912 too-many-branches
    """Fetch and parse upstream testing workflow results."""
    url = f"https://api.github.com/repos/{project['org']}/{project['repo']}/actions/workflows/upstream_testing.yml/runs"
    runs_data = _get_github_api_response(url)

    if runs_data is not None:
        latest_run_jobs = _get_github_api_response(runs_data["workflow_runs"][0]["jobs_url"])

    # print("-" * 20 + project["repo"])
    # for run in runs_data["workflow_runs"]:
    #     run_started = datetime.fromisoformat(run["run_started_at"])
    #     run_ended = datetime.fromisoformat(run["updated_at"])

    # print(f"{run['run_started_at']}/{run['conclusion']}/{run['id']}/{run_ended-run_started}")

    success_streak = (
        _get_run_streak(runs_data["workflow_runs"], "success", "failure") if runs_data else 0
    )
    fail_streak = (
        _get_run_streak(runs_data["workflow_runs"], "failure", "success") if runs_data else 0
    )

    return {
        "runs": runs_data["workflow_runs"] if runs_data else None,
        "success_streak": success_streak,
        "fail_streak": fail_streak,
        "latest_run_jobs": latest_run_jobs["jobs"] if runs_data else None,
    }
    # if success_streak["length"]:
    #     print(
    #         f"successful streak: {success_streak['length']} from {success_streak['first_run']['id']} to {success_streak['last_run']['id']}"
    #     )
    # if fail_streak["length"]:
    #     print(
    #         f"failed streak: {fail_streak['length']} from {fail_streak['first_run']['id']} to {fail_streak['last_run']['id']}"
    #     )


def get_pypi_data(project):
    """Fetch and parse upstream testing workflow results."""
    pypi_raw_data = _get_pypi_api_response(project["pypi"])
    pypi_data = {
        "latest": {
            "version": pypi_raw_data["info"]["version"],
            "requires_python": pypi_raw_data["info"]["requires_python"],
            "requires_nautobot": "N/A",
            "date": pypi_raw_data["urls"][0]["upload_time"].split("T")[0],
        }
    }

    release_date = datetime.fromisoformat(pypi_raw_data["urls"][0]["upload_time"])
    if datetime.now() - release_date > timedelta(weeks=16):
        pypi_data["latest"]["date_color"] = "danger"
    elif datetime.now() - release_date > timedelta(weeks=8):
        pypi_data["latest"]["date_color"] = "warning"
    else:
        pypi_data["latest"]["date_color"] = "success"

    r = re.compile("nautobot[<> ]")
    for result in filter(r.match, pypi_raw_data["info"]["requires_dist"]):
        pypi_data["latest"]["requires_nautobot"] = result

    return pypi_data


### Main Script

PROJECTS = _get_yaml_data("data.yaml")
JINJA_ENV = Environment(loader=FileSystemLoader("templates"), autoescape=select_autoescape())
OUTPUT_PATH = "output"
# Add filesystem based caching of requests API calls (mostly for development)
REQUESTS_CACHE_PATH = "./.cache"
requests_cache.install_cache(REQUESTS_CACHE_PATH, backend="filesystem", expire_after=3600)


if __name__ == "__main__":
    upstream_data = {}
    pypi_data = {}
    for project in PROJECTS["nautobot"]:
        upstream_data[project["repo"]] = get_github_upstream_testing_results(project)
        pypi_data[project["repo"]] = get_pypi_data(project)

    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    build_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")

    _generate_page("index.html", projects=PROJECTS, pypi=pypi_data, build_timestamp=build_timestamp)
    _generate_page("badges.html", projects=PROJECTS)
    _generate_page(
        "upstream.html", projects=PROJECTS, upstream=upstream_data, build_timestamp=build_timestamp
    )
