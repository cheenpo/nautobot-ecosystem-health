import os

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
