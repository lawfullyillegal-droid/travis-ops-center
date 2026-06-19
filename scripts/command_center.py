#!/usr/bin/env python3
"""Simple curses-based command center prototype.

Loads allowed commands from config/commands.yml (copy from commands.sample.yml).
Executes selected command after confirmation and logs via audit_logger.
"""
import curses
import subprocess
import sys
import yaml
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
import scripts.audit_logger as audit

CONFIG_PATH = REPO_ROOT / "config" / "commands.yml"

def load_commands():
    if not CONFIG_PATH.exists():
        return []
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg.get("commands", []) if cfg else []

def run_command(cmd):
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    audit.log_entry(cmd, proc.returncode, proc.stdout, proc.stderr)
    return proc

def main(stdscr):
    curses.curs_set(0)
    cmds = load_commands()
    if not cmds:
        stdscr.addstr(0,0,"No commands configured. Copy config/commands.sample.yml -> config/commands.yml and edit.")
        stdscr.getch()
        return
    sel = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0,0,"Command Center - select a command and press Enter. q to quit")
        for i,c in enumerate(cmds):
            prefix = "> " if i==sel else "  "
            stdscr.addstr(i+2, 0, prefix + c.get('label','') )
        ch = stdscr.getch()
        if ch in (ord('q'), ord('Q')):
            break
        elif ch == curses.KEY_UP:
            sel = max(0, sel-1)
        elif ch == curses.KEY_DOWN:
            sel = min(len(cmds)-1, sel+1)
        elif ch in (curses.KEY_ENTER, 10, 13):
            cmd = cmds[sel]['cmd']
            stdscr.clear()
            stdscr.addstr(0,0,f"Run: {cmd}\nConfirm? (y/n)")
            c = stdscr.getch()
            if c in (ord('y'), ord('Y')):
                stdscr.addstr(2,0, "Running... (press any key to return)")
                stdscr.refresh()
                proc = run_command(cmd)
                out = proc.stdout or proc.stderr or "(no output)"
                # truncate output to fit
                for idx, line in enumerate(out.splitlines()[:curses.LINES-4]):
                    stdscr.addstr(4+idx, 0, line[:curses.COLS-1])
                stdscr.getch()

if __name__ == '__main__':
    curses.wrapper(main)
