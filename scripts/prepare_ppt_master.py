#!/usr/bin/env python3
"""Locate or sparsely fetch the PPT Master skill used for stage-one generation.

This prepares the upstream agent workflow; it does not generate a presentation.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPOSITORY = "https://github.com/hugohe3/ppt-master.git"
PINNED_COMMIT = "769547394107870a0c7b5ad8d1c0c75035123aef"
REQUIRED_FILES = (
    "SKILL.md",
    "workflows/routing.md",
    "workflows/generate-pptx.md",
    "scripts/project_manager.py",
    "scripts/svg_to_pptx.py",
)


def skill_dir(path: Path) -> Path | None:
    path = path.expanduser().resolve()
    candidates = (path, path / "skills" / "ppt-master")
    for candidate in candidates:
        if all((candidate / relative).is_file() for relative in REQUIRED_FILES):
            return candidate
    return None


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="定位或获取 PPT Master 的完整 Skill 目录，供竞赛 PPT 第一阶段使用。"
    )
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="当前 PPT 工作目录")
    parser.add_argument("--source", type=Path, help="已有 ppt-master 仓库根目录或 skills/ppt-master 目录")
    parser.add_argument("--offline", action="store_true", help="只检测本地目录，不下载")
    parser.add_argument("--install-deps", action="store_true", help="用当前 Python 安装上游全部依赖")
    args = parser.parse_args()

    workspace = args.workspace.expanduser().resolve()
    if args.source:
        found = skill_dir(args.source)
        if found is None:
            parser.error("--source 不是完整的 PPT Master Skill 目录或仓库根目录")
    else:
        target = workspace / "_dependencies" / "ppt-master"
        found = skill_dir(target) if target.exists() else None
        if target.exists() and found is None:
            parser.error(f"已有目录不完整，请检查后手工处理：{target}")
        if found is None:
            if args.offline:
                parser.error("离线模式下未找到 PPT Master；请用 --source 指向已有的完整目录")
            git = shutil.which("git")
            if git is None:
                parser.error("未找到 Git；请安装 Git 或用 --source 指向已有的 PPT Master 目录")
            parent = target.parent
            parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="ppt-master-fetch-", dir=parent) as temporary:
                checkout = Path(temporary) / "checkout"
                try:
                    run([git, "clone", "--filter=blob:none", "--no-checkout", "--sparse", REPOSITORY, os.fspath(checkout)])
                    run([git, "-C", os.fspath(checkout), "fetch", "--depth=1", "origin", PINNED_COMMIT])
                    run([git, "-C", os.fspath(checkout), "sparse-checkout", "set", "skills/ppt-master"])
                    run([git, "-C", os.fspath(checkout), "checkout", "--detach", PINNED_COMMIT])
                except subprocess.CalledProcessError as error:
                    parser.error(f"获取 PPT Master 失败（Git 退出码 {error.returncode}）；请检查网络或使用 --source")
                if skill_dir(checkout) is None:
                    parser.error("下载完成，但缺少上游工作流文件；请检查上游版本")
                checkout.replace(target)
            found = skill_dir(target)
            if found is None:
                parser.error("获取后校验失败")

    if args.install_deps:
        requirements = found / "requirements.txt"
        if not requirements.is_file():
            parser.error(f"缺少依赖清单：{requirements}")
        try:
            run([sys.executable, "-m", "pip", "install", "-r", os.fspath(requirements)])
        except subprocess.CalledProcessError as error:
            parser.error(f"安装上游依赖失败（退出码 {error.returncode}）")

    print(found / "SKILL.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
