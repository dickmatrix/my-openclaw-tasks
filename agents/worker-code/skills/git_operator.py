#!/usr/bin/env python3
"""
GitOperator Git操作工具 - 仓库管理、分支操作、版本控制
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import subprocess
import json


class GitStatus(Enum):
    """Git 状态枚举"""
    CLEAN = "clean"
    MODIFIED = "modified"
    UNTRACKED = "untracked"
    STAGED = "staged"
    CONFLICT = "conflict"


@dataclass
class CommitInfo:
    """提交信息"""
    hash: str
    message: str
    author: str
    date: str
    files_changed: int


@dataclass
class BranchInfo:
    """分支信息"""
    name: str
    is_current: bool
    upstream: Optional[str]
    ahead: int
    behind: int


class GitOperator:
    """Git 操作封装"""
    
    def __init__(self, repo_path: str = "."):
        self.name = "git_operator"
        self.description = "Git 版本控制：仓库、分支、提交管理"
        self.repo_path = repo_path
        self.git_executable = "git"
    
    def run_git_command(self, *args, capture_output: bool = True) -> tuple[int, str, str]:
        """执行 Git 命令
        
        Returns:
            (exit_code, stdout, stderr)
        """
        cmd = [self.git_executable] + list(args)
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                timeout=30
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timeout"
        except Exception as e:
            return -1, "", str(e)
    
    def init(self, bare: bool = False) -> Dict:
        """初始化仓库"""
        args = ["init"]
        if bare:
            args.append("--bare")
        
        exit_code, stdout, stderr = self.run_git_command(*args)
        return {
            "status": "success" if exit_code == 0 else "error",
            "message": stdout if exit_code == 0 else stderr
        }
    
    def clone(self, url: str, depth: int = None) -> Dict:
        """克隆仓库
        
        Args:
            url: 仓库 URL
            depth: 浅克隆深度
        """
        args = ["clone"]
        if depth:
            args.extend(["--depth", str(depth)])
        args.append(url)
        
        exit_code, stdout, stderr = self.run_git_command(*args)
        return {
            "status": "success" if exit_code == 0 else "error",
            "output": stdout,
            "error": stderr if exit_code != 0 else None
        }
    
    def status(self) -> Dict:
        """获取仓库状态"""
        exit_code, stdout, stderr = self.run_git_command("status", "--porcelain")
        if exit_code != 0:
            return {"status": "error", "message": stderr}
        
        files = []
        for line in stdout.strip().split("\n"):
            if line:
                status_code = line[:2]
                file_path = line[3:]
                files.append({
                    "status": status_code,
                    "path": file_path
                })
        
        return {
            "status": "success",
            "is_clean": len(files) == 0,
            "files": files
        }
    
    def branch_list(self) -> List[BranchInfo]:
        """获取分支列表"""
        exit_code, stdout, stderr = self.run_git_command(
            "for-each-ref", 
            "--format=%(refname:short)|%(upstream:short)|%(aheadbehind)",
            "refs/heads/"
        )
        
        if exit_code != 0:
            return []
        
        branches = []
        current_branch = self.get_current_branch()
        
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            
            parts = line.split("|")
            name = parts[0]
            upstream = parts[1] if len(parts) > 1 else None
            
            ahead, behind = 0, 0
            if len(parts) > 2 and parts[2]:
                try:
                    ahead, behind = map(int, parts[2].split(","))
                except:
                    pass
            
            branches.append(BranchInfo(
                name=name,
                is_current=name == current_branch,
                upstream=upstream,
                ahead=ahead,
                behind=behind
            ))
        
        return branches
    
    def get_current_branch(self) -> Optional[str]:
        """获取当前分支"""
        exit_code, stdout, stderr = self.run_git_command("branch", "--show-current")
        if exit_code == 0:
            return stdout.strip()
        return None
    
    def create_branch(self, branch_name: str, checkout: bool = True) -> Dict:
        """创建分支"""
        args = ["branch"]
        if checkout:
            args.append("-b")
        args.append(branch_name)
        
        exit_code, stdout, stderr = self.run_git_command(*args)
        return {
            "status": "success" if exit_code == 0 else "error",
            "message": stdout if exit_code == 0 else stderr
        }
    
    def checkout(self, ref: str, create_branch: bool = False) -> Dict:
        """切换分支/标签/提交"""
        args = ["checkout"]
        if create_branch:
            args.append("-b")
        args.append(ref)
        
        exit_code, stdout, stderr = self.run_git_command(*args)
        return {
            "status": "success" if exit_code == 0 else "error",
            "message": stdout if exit_code == 0 else stderr
        }
    
    def add(self, patterns: List[str] = None) -> Dict:
        """暂存文件"""
        args = ["add"]
        if patterns:
            args.extend(patterns)
        else:
            args.append(".")
        
        exit_code, stdout, stderr = self.run_git_command(*args)
        return {
            "status": "success" if exit_code == 0 else "error",
            "message": stderr if exit_code != 0 else f"Added {len(patterns) if patterns else 'all'} files"
        }
    
    def commit(self, message: str) -> Dict:
        """提交暂存区"""
        exit_code, stdout, stderr = self.run_git_command(
            "commit", "-m", message
        )
        return {
            "status": "success" if exit_code == 0 else "error",
            "message": stdout if exit_code == 0 else stderr
        }
    
    def push(self, remote: str = "origin", branch: str = None, 
             set_upstream: bool = False) -> Dict:
        """推送到远程"""
        args = ["push"]
        if set_upstream:
            args.append("-u")
        args.append(remote)
        if branch:
            args.append(branch)
        
        exit_code, stdout, stderr = self.run_git_command(*args)
        return {
            "status": "success" if exit_code == 0 else "error",
            "output": stdout,
            "error": stderr if exit_code != 0 else None
        }
    
    def pull(self, remote: str = "origin", branch: str = None) -> Dict:
        """拉取远程更新"""
        args = ["pull"]
        args.append(remote)
        if branch:
            args.append(branch)
        
        exit_code, stdout, stderr = self.run_git_command(*args)
        return {
            "status": "success" if exit_code == 0 else "error",
            "output": stdout,
            "error": stderr if exit_code != 0 else None
        }
    
    def log(self, max_count: int = 10) -> List[CommitInfo]:
        """获取提交历史"""
        exit_code, stdout, stderr = self.run_git_command(
            "log", f"--max-count={max_count}",
            "--format=%H|%s|%an|%ad",
            "--date=iso"
        )
        
        if exit_code != 0:
            return []
        
        commits = []
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            
            parts = line.split("|")
            if len(parts) >= 4:
                commits.append(CommitInfo(
                    hash=parts[0][:8],
                    message=parts[1],
                    author=parts[2],
                    date=parts[3],
                    files_changed=0  # TODO: 统计变更文件数
                ))
        
        return commits
    
    def diff(self, ref1: str = None, ref2: str = None) -> str:
        """查看差异"""
        args = ["diff"]
        if ref1:
            args.append(ref1)
        if ref2:
            args.append(ref2)
        
        exit_code, stdout, stderr = self.run_git_command(*args)
        return stdout


def main(action: str, **kwargs) -> Dict:
    """主入口函数"""
    repo_path = kwargs.get("repo_path", ".")
    operator = GitOperator(repo_path)
    
    handlers = {
        "status": operator.status,
        "branch_list": lambda: {"branches": [
            {"name": b.name, "is_current": b.is_current, "upstream": b.upstream}
            for b in operator.branch_list()
        ]},
        "current_branch": lambda: {"branch": operator.get_current_branch()},
        "create_branch": lambda: operator.create_branch(kwargs.get("branch_name"), kwargs.get("checkout", True)),
        "checkout": lambda: operator.checkout(kwargs.get("ref"), kwargs.get("create_branch", False)),
        "add": lambda: operator.add(kwargs.get("patterns")),
        "commit": lambda: operator.commit(kwargs.get("message")),
        "push": lambda: operator.push(kwargs.get("remote", "origin"), kwargs.get("branch"), kwargs.get("set_upstream", False)),
        "pull": lambda: operator.pull(kwargs.get("remote", "origin"), kwargs.get("branch")),
        "log": lambda: {"commits": [
            {"hash": c.hash, "message": c.message, "author": c.author, "date": c.date}
            for c in operator.log(kwargs.get("max_count", 10))
        ]},
    }
    
    if action not in handlers:
        return {"status": "error", "message": f"Unknown action: {action}"}
    
    return handlers[action]()


if __name__ == "__main__":
    # 测试代码
    result = main("current_branch")
    print(json.dumps(result, ensure_ascii=False, indent=2))
