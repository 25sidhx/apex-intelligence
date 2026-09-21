"""
Worktree Manager: Manages isolated Git worktrees for concurrent development.
Inspired by max-sixty/worktrunk.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional


class WorktreeManager:
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or Path.cwd()

    def _run_git(self, args: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git"] + args,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )

    def list_worktrees(self) -> List[Dict[str, str]]:
        result = self._run_git(["worktree", "list", "--porcelain"])
        if result.returncode != 0:
            return []

        worktrees = []
        current: Dict[str, str] = {}
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                if current:
                    worktrees.append(current)
                    current = {}
                continue
            if line.startswith("worktree "):
                current["path"] = line.split(" ", 1)[1]
            elif line.startswith("HEAD "):
                current["head"] = line.split(" ", 1)[1]
            elif line.startswith("branch "):
                current["branch"] = line.split(" ", 1)[1]

        if current:
            worktrees.append(current)
        return worktrees

    def create_worktree(self, branch_name: str, target_dir: Optional[str] = None) -> bool:
        if not target_dir:
            target_dir = f"../worktrees/{branch_name}"
        result = self._run_git(["worktree", "add", "-b", branch_name, target_dir])
        return result.returncode == 0

    def remove_worktree(self, target_dir: str) -> bool:
        result = self._run_git(["worktree", "remove", target_dir, "--force"])
        return result.returncode == 0
