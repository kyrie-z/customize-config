#!/usr/bin/env python3
"""
配置文件部署工具 - 通过软链接方式部署配置文件
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeployTarget:
    """部署目标配置"""
    name: str
    source_dir: Path
    deploy_map: dict[str, str]  # 相对源路径 -> 目标路径


def get_targets(project_root: Path) -> list[DeployTarget]:
    """获取所有部署目标配置"""
    home = Path.home()

    targets = [
        DeployTarget(
            name="claude",
            source_dir=project_root / "claude",
            deploy_map={
                "CLAUDE.md": str(home / ".claude" / "CLAUDE.md"),
            }
        ),
        DeployTarget(
            name="tmux",
            source_dir=project_root / "tmux",
            deploy_map={
                ".tmux.conf": str(home / ".tmux.conf"),
                "script": str(home / ".config" / "tmux" / "script"),
            }
        ),
    ]
    return targets


def check_conflict(target_path: Path) -> tuple[bool, str]:
    """
    检查目标路径是否存在冲突
    返回: (是否有冲突, 冲突描述)
    """
    if not target_path.exists():
        return False, ""

    if target_path.is_symlink():
        link_target = target_path.resolve()
        return True, f"已存在软链接 -> {link_target}"
    elif target_path.is_file():
        return True, "已存在普通文件"
    elif target_path.is_dir():
        return True, "已存在目录"
    else:
        return True, "已存在未知类型文件"


def prompt_overwrite(target_path: Path, conflict_desc: str) -> Optional[bool]:
    """
    提示用户是否覆盖冲突
    返回: True=覆盖, False=跳过, None=取消操作
    """
    print(f"\n  冲突: {target_path}")
    print(f"  状态: {conflict_desc}")

    while True:
        response = input("  是否覆盖? [y/n/a/q] (y=覆盖, n=跳过, a=全部覆盖, q=取消): ").strip().lower()

        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        elif response in ('a', 'all'):
            return True  # 返回True，调用者需要处理"全部"逻辑
        elif response in ('q', 'quit'):
            return None
        else:
            print("  无效输入，请重试")


def deploy_single(source: Path, target: Path, force: bool = False) -> tuple[bool, str]:
    """
    部署单个文件/目录
    返回: (是否成功, 操作描述)
    """
    if not source.exists():
        return False, f"源文件不存在: {source}"

    # 确保目标父目录存在
    target.parent.mkdir(parents=True, exist_ok=True)

    # 检查冲突
    has_conflict, conflict_desc = check_conflict(target)

    if has_conflict:
        if not force:
            return False, f"需要确认: {conflict_desc}"

        # 删除现有文件/链接
        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            import shutil
            shutil.rmtree(target)

    # 创建软链接
    target.symlink_to(source)
    return True, f"已链接 -> {source}"


def deploy_target(target: DeployTarget, force: bool = False) -> tuple[int, int]:
    """
    部署单个目标的所有配置
    返回: (成功数, 失败数)
    """
    print(f"\n[{target.name}]")

    success, fail = 0, 0
    overwrite_all = force

    for src_rel, dst_str in target.deploy_map.items():
        source = target.source_dir / src_rel
        target_path = Path(dst_str)

        # 检查冲突
        has_conflict, conflict_desc = check_conflict(target_path)

        if has_conflict and not overwrite_all:
            result = prompt_overwrite(target_path, conflict_desc)
            if result is None:
                print("  操作已取消")
                return success, fail + 1
            elif result is False:
                print(f"  跳过: {target_path}")
                continue
            # 如果用户输入 'a'，设置全局覆盖（这里简化处理，实际需要额外状态）

        ok, msg = deploy_single(source, target_path, force=overwrite_all or has_conflict)

        if ok:
            print(f"  ✓ {dst_str}: {msg}")
            success += 1
        else:
            print(f"  ✗ {dst_str}: {msg}")
            fail += 1

    return success, fail


def main():
    import argparse

    parser = argparse.ArgumentParser(description="配置文件部署工具")
    parser.add_argument("-f", "--force", action="store_true",
                        help="强制覆盖，不询问")
    parser.add_argument("-l", "--list", action="store_true",
                        help="仅列出部署目标，不执行")
    args = parser.parse_args()

    project_root = Path(__file__).parent.resolve()

    print("=" * 50)
    print("配置文件部署工具")
    print("=" * 50)
    print(f"项目根目录: {project_root}")

    targets = get_targets(project_root)

    if args.list:
        print("\n部署目标:")
        for target in targets:
            print(f"\n[{target.name}]")
            for src_rel, dst_str in target.deploy_map.items():
                source = target.source_dir / src_rel
                exists = "✓" if source.exists() else "✗"
                print(f"  {exists} {src_rel} -> {dst_str}")
        return 0

    total_success, total_fail = 0, 0

    for target in targets:
        s, f = deploy_target(target, force=args.force)
        total_success += s
        total_fail += f

    print("\n" + "=" * 50)
    print(f"完成: 成功 {total_success}, 失败 {total_fail}")
    print("=" * 50)

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
