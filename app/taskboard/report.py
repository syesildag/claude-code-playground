from .models import Task


def export_html(tasks, title="Taskboard"):
    rows = "\n".join(f'    <li class="{t.status}">#{t.id} {t.title}</li>' for t in tasks)
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body>
  <h1>{title}</h1>
  <ul>
{rows}
  </ul>
</body>
</html>
"""


def count_by_status(tasks: list[Task]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for task in tasks:
        counts[task.status] = counts.get(task.status, 0) + 1
    return counts
