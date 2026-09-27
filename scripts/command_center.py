#!/usr/bin/env python3
"""Curses command center for explicitly allow-listed operator commands."""

import curses
import shlex
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import scripts.audit_logger as audit  # noqa: E402

CONFIG_PATH = REPO_ROOT / "config" / "commands.yml"


def load_commands():
    if not CONFIG_PATH.exists():
        return []
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle) or {}
    return cfg.get("commands", [])


def render_command(template, target):
    if "{target}" not in template:
        return template
    if not target:
        raise ValueError("This command requires a target.")
    if any(ch in target for ch in ("\n", "\r", "\x00")):
        raise ValueError("Target contains invalid control characters.")
    return template.replace("{target}", shlex.quote(target))


def run_command(cmd, timeout):
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + f"\nCommand timed out after {timeout} seconds."
        audit.log_entry(cmd, 124, stdout, stderr)
        return subprocess.CompletedProcess(cmd, 124, stdout, stderr)

    audit.log_entry(cmd, proc.returncode, proc.stdout, proc.stderr)
    return proc


def prompt_text(stdscr, prompt):
    curses.echo()
    curses.curs_set(1)
    try:
        stdscr.clear()
        stdscr.addstr(0, 0, prompt)
        stdscr.addstr(2, 0, "> ")
        stdscr.refresh()
        raw = stdscr.getstr(2, 2, 512)
        return raw.decode("utf-8", errors="replace").strip()
    finally:
        curses.noecho()
        curses.curs_set(0)


def main(stdscr):
    curses.curs_set(0)
    cmds = load_commands()

    if not cmds:
        stdscr.addstr(
            0,
            0,
            "No commands configured. Copy config/commands.sample.yml "
            "to config/commands.yml and review it.",
        )
        stdscr.getch()
        return

    selected = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Command Center — Enter=run, q=quit")
        for index, spec in enumerate(cmds):
            prefix = "> " if index == selected else "  "
            stdscr.addstr(index + 2, 0, prefix + spec.get("label", spec.get("id", "command")))

        key = stdscr.getch()
        if key in (ord("q"), ord("Q")):
            break
        if key == curses.KEY_UP:
            selected = max(0, selected - 1)
            continue
        if key == curses.KEY_DOWN:
            selected = min(len(cmds) - 1, selected + 1)
            continue
        if key not in (curses.KEY_ENTER, 10, 13):
            continue

        spec = cmds[selected]
        template = spec.get("cmd", "")
        target = None
        if "{target}" in template:
            target = prompt_text(
                stdscr,
                "Enter an authorized target (host, URL, username, or path as appropriate):",
            )
            if not target:
                continue

        try:
            cmd = render_command(template, target)
        except ValueError as exc:
            stdscr.clear()
            stdscr.addstr(0, 0, f"Cannot run command: {exc}")
            stdscr.getch()
            continue

        timeout = int(spec.get("timeout", 300))
        stdscr.clear()
        stdscr.addstr(0, 0, f"Run: {cmd}")
        stdscr.addstr(2, 0, "Confirm authorized execution? (y/n)")
        confirm = stdscr.getch()
        if confirm not in (ord("y"), ord("Y")):
            continue

        stdscr.clear()
        stdscr.addstr(0, 0, "Running...")
        stdscr.refresh()

        proc = run_command(cmd, timeout)
        output = proc.stdout or proc.stderr or "(no output)"
        stdscr.addstr(2, 0, f"Exit code: {proc.returncode}")

        max_lines = max(0, curses.LINES - 5)
        for idx, line in enumerate(output.splitlines()[:max_lines]):
            try:
                stdscr.addstr(4 + idx, 0, line[: max(1, curses.COLS - 1)])
            except curses.error:
                break
        stdscr.getch()


if __name__ == "__main__":
    curses.wrapper(main)
