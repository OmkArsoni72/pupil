import os
import re
import shutil
from pathlib import Path


"""
Refactor script to migrate code folders into core/ and rewrite imports.

Usage:
  - Dry run (default): prints planned moves and rewrites
  - Apply: set APPLY=1 env var to perform changes

Behavior:
  - Moves these top-level dirs into core/ if present:
    agents, api, graphs, models, nodes, services, workers
  - Rewrites absolute imports like `from agents.x` -> `from core.agents.x`
    and `import services.ai` -> `import core.services.ai as services_ai` style
  - Skips files in tests/, docs/, archive/, scripts/
  - Leaves .backup and backup/ untouched (you can manually move to archive/)
"""


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = PROJECT_ROOT / "core"

MOVE_DIRS = [
    "agents",
    "api",
    "graphs",
    "models",
    "nodes",
    "services",
    "workers",
]

SKIP_DIRS = {"tests", "docs", "archive", "scripts", ".venv", "node_modules", ".git"}

IMPORT_PATTERNS = [
    # from <pkg> import ...  => from core.<pkg> import ...
    (re.compile(r"^(\s*from\s+)(agents|api|graphs|models|nodes|services|workers)(\b.*)$"), r"\1core.\2\3"),
    # import <pkg>.<rest> => import core.<pkg>.<rest>
    (re.compile(r"^(\s*import\s+)(agents|api|graphs|models|nodes|services|workers)(\.[\w\.]+\b.*)$"), r"\1core.\2\3"),
]


def is_apply() -> bool:
    return os.getenv("APPLY", "0") in {"1", "true", "yes", "y"}


def move_dirs():
    for name in MOVE_DIRS:
        src = PROJECT_ROOT / name
        dst = CORE_DIR / name
        if not src.exists() or not src.is_dir():
            continue
        if dst.exists():
            print(f"[SKIP] Destination exists: {dst}")
            continue
        print(f"[MOVE] {src} -> {dst}")
        if is_apply():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    return any(skip in parts for skip in SKIP_DIRS)


def rewrite_file_imports(py_file: Path) -> bool:
    try:
        original = py_file.read_text(encoding="utf-8")
    except Exception:
        return False

    lines = original.splitlines(keepends=True)
    changed = False

    for i, line in enumerate(lines):
        for pattern, repl in IMPORT_PATTERNS:
            if pattern.search(line):
                new_line = pattern.sub(repl, line)
                if new_line != line:
                    lines[i] = new_line
                    changed = True

    if changed:
        print(f"[REWRITE] {py_file}")
        if is_apply():
            py_file.write_text("".join(lines), encoding="utf-8")
    return changed


def rewrite_imports():
    changed_files = 0
    for py_file in PROJECT_ROOT.rglob("*.py"):
        if should_skip(py_file):
            continue
        if py_file.is_file():
            if rewrite_file_imports(py_file):
                changed_files += 1
    print(f"[SUMMARY] Import rewrites: {changed_files} files changed")


def main():
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Core dir:     {CORE_DIR}")
    print(f"Mode:         {'APPLY' if is_apply() else 'DRY-RUN'}")
    move_dirs()
    rewrite_imports()
    print("Done.")


if __name__ == "__main__":
    main()


