#!/usr/bin/env python3
"""Helpers for syncing a packaged LaTeX project with Overleaf via LeafLink."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_PYTHON = "python"


def playwright_env() -> dict[str, str]:
    env = os.environ.copy()
    if "PLAYWRIGHT_BROWSERS_PATH" not in env:
        for candidate in (Path("/mnt/data/.cache/ms-playwright"), Path.home() / ".cache" / "ms-playwright"):
            if candidate.exists():
                env["PLAYWRIGHT_BROWSERS_PATH"] = str(candidate)
                break
    return env


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd is not None else None,
        check=check,
        text=True,
        capture_output=False,
        env=env,
    )


def conda_env_name() -> str:
    env_name = os.environ.get("CONDA_DEFAULT_ENV", "")
    return env_name.strip()


def require_non_base_env() -> None:
    env_name = conda_env_name()
    if not env_name:
        raise SystemExit("No conda environment is active. Activate a dedicated env first.")
    if env_name == "base":
        raise SystemExit("Refuse to run in conda base. Activate a dedicated sync env first.")


def which(binary: str) -> str | None:
    return shutil.which(binary)


def ensure_leaflink() -> None:
    if which("leaflink") is None:
        raise SystemExit("leaflink is not installed in the active environment.")


def ensure_playwright() -> None:
    if which("playwright") is None:
        raise SystemExit("playwright is not installed in the active environment.")


def cmd_status(_: argparse.Namespace) -> int:
    require_non_base_env()
    ensure_leaflink()
    run(["leaflink", "status"])
    return 0


def cmd_package(args: argparse.Namespace) -> int:
    require_non_base_env()
    target = Path(args.repo).resolve()
    if not (target / "Makefile").exists():
        raise SystemExit(f"No Makefile found in {target}")
    run(["make", "overleaf-package"], cwd=target)
    return 0


def cmd_setup(args: argparse.Namespace) -> int:
    require_non_base_env()
    ensure_leaflink()
    ensure_playwright()
    if args.install_browser:
        run([sys.executable, "-m", "playwright", "install", "chromium"], env=playwright_env())
    if args.login:
        run(["leaflink", "login", "--base-url", args.base_url], env=playwright_env())
    if args.clone:
        run(["leaflink", "clone", args.project, args.sync_dir], env=playwright_env())
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    require_non_base_env()
    ensure_leaflink()
    sync_dir = Path(args.sync_dir).resolve()
    if args.package_repo:
        repo = Path(args.package_repo).resolve()
        run(["make", "overleaf-package"], cwd=repo)
        src = repo / "output" / "overleaf_src"
        if not src.exists():
            raise SystemExit(f"Packaged source directory not found: {src}")
        sync_dir.mkdir(parents=True, exist_ok=True)
        run(["rsync", "-a", "--delete", "--exclude=.leaflink/", f"{src}/", f"{sync_dir}/"])
    env = playwright_env()
    run(["leaflink", "status"], cwd=sync_dir, env=env)
    if args.dry_run:
        run(["leaflink", "push", "--dry-run"], cwd=sync_dir, env=env)
        return 0
    run(["leaflink", "push"], cwd=sync_dir, env=env)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("package", help="Run make overleaf-package in the repo")
    p.add_argument("--repo", default=os.getcwd())
    p.set_defaults(func=cmd_package)

    p = sub.add_parser("status", help="Run leaflink status in the current sync directory")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("setup", help="Install browser binaries, login, or clone the project")
    p.add_argument("--base-url", default="https://www.overleaf.com")
    p.add_argument("--login", action="store_true")
    p.add_argument("--clone", action="store_true")
    p.add_argument("--project", default="")
    p.add_argument("--sync-dir", default="")
    p.add_argument("--install-browser", action="store_true")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("sync", help="Copy packaged sources into a sync dir and push")
    p.add_argument("--package-repo", default="")
    p.add_argument("--sync-dir", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_sync)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
