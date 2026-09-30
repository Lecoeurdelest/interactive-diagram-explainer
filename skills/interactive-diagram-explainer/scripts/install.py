#!/usr/bin/env python3
import argparse
import os
import shutil
import sys
from pathlib import Path

NAME = "interactive-diagram-explainer"
SKILL_DIR = Path(__file__).resolve().parent.parent


def targets():
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return {
        "claude": Path.home() / ".claude" / "skills",
        "codex": codex_home / "skills",
        "agents": Path.home() / ".agents" / "skills",
    }


def main():
    known = targets()
    parser = argparse.ArgumentParser(description="Install the skill for one or more agent platforms.")
    parser.add_argument("platform", nargs="+", choices=[*known, "all"])
    parser.add_argument("--project", metavar="DIR", help="install under DIR/.<platform> instead of the home directory")
    parser.add_argument("--dest", metavar="DIR", help="install into this skills directory")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    names = list(known) if "all" in args.platform else args.platform
    for name in names:
        if args.dest:
            base = Path(args.dest)
        elif args.project:
            base = Path(args.project) / ("." + name) / "skills"
        else:
            base = known[name]
        target = base / NAME
        if target.exists():
            if not args.force:
                print(f"skip {name}: {target} exists (use --force)", file=sys.stderr)
                continue
            shutil.rmtree(target)
        base.mkdir(parents=True, exist_ok=True)
        shutil.copytree(SKILL_DIR, target, ignore=shutil.ignore_patterns("__pycache__"))
        print(f"installed {name}: {target}")


if __name__ == "__main__":
    main()
