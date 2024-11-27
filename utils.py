"""Utility functions for usage in fetching data and rendering pages."""

import os
import re
from datetime import datetime, timedelta

import requests
from ruamel.yaml import YAML


def generate_page(page, jinja_env, output_path, **kwargs):
    """Generates a new file in memory from a Jinja template."""
    with open(
        os.path.join(
            output_path,
            page,
        ),
        "w",
    ) as output_file:
        template = jinja_env.get_template(f"{page}.jinja")
        output_file.write(template.render(**kwargs))


def get_yaml_data(filename):
    """Load YAML data from a file."""
    yaml = YAML(typ="safe")
    with open(filename) as data_file:
        return yaml.load(data_file.read())


#
# Functions for getting data from the GitHub API.
#


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


def get_github_upstream_testing_results(project):
    """Fetch and parse upstream testing workflow results."""
    url = f"https://api.github.com/repos/{project['org']}/{project['repo']}/actions/workflows/upstream_testing.yml/runs"
    runs_data = _get_github_api_response(url)

    if runs_data is not None:
        latest_run_jobs = _get_github_api_response(runs_data["workflow_runs"][0]["jobs_url"])

    return {
        "runs": runs_data["workflow_runs"] if runs_data else None,
        "latest_run_jobs": latest_run_jobs["jobs"] if runs_data else None,
    }


#
# Functions for getting data from the PyPI API.
#
def _get_pypi_api_response(project):
    """Return data from PyPI JSON API."""
    url = f"https://pypi.python.org/pypi/{project}/json"
    headers = {"Accept": "application/json"}
    resp = requests.get(url, headers=headers, timeout=10)

    if resp.ok:
        return resp.json()
    else:
        return None


def get_pypi_data(project):
    """Fetch and parse package data from PyPI."""
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


# TODO: Might remove it since having visual history is enough.
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
