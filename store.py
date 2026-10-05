import json
import os
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
RUNS_FILE = PROJECT_ROOT / "data" / "runs.json"


def load_runs(path: Path = RUNS_FILE) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not read saved research data at {path}: {error}") from error
    if not isinstance(data, list) or any(not isinstance(run, dict) for run in data):
        raise RuntimeError(f"Saved research data at {path} must contain a JSON list of run objects.")
    return data


def save_run(run: dict[str, Any], path: Path = RUNS_FILE) -> None:
    runs = load_runs(path)
    run_id = run.get("id")
    if not run_id:
        raise ValueError("A saved research run must have an id.")
    runs = [existing for existing in runs if existing.get("id") != run_id]
    runs.insert(0, run)
    _write_runs(runs, path)


def delete_run(run_id: str, path: Path = RUNS_FILE) -> bool:
    runs = load_runs(path)
    remaining = [run for run in runs if run.get("id") != run_id]
    if len(remaining) == len(runs):
        return False
    _write_runs(remaining, path)
    return True


def _write_runs(runs: list[dict[str, Any]], path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.tmp")
        temporary.write_text(
            json.dumps(runs, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, path)
    except (OSError, TypeError, ValueError) as error:
        raise RuntimeError(f"Could not save research data at {path}: {error}") from error
