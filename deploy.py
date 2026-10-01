#!/usr/bin/env python3
"""
配置文件部署工具 - 通过软链接方式部署配置文件
"""

import os
import shutil
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class ItemStatus(Enum):
    UP_TO_DATE = "已正确链接"
    NEED_LINK = "待新建链接"
    CONFLICT_FILE = "冲突(普通文件)"
    CONFLICT_DIR = "冲突(目录)"
    CONFLICT_LINK = "冲突(软链接指向其他位置)"
    MISSING_SOURCE = "源文件缺失"


@dataclass
class DeployTarget:
    """部署目标配置"""
    name: str
    source_dir: Path
    deploy_map: dict[str, str]  # 相对源路径 -> 目标路径


@dataclass
class DeployItem:
    """单个待部署项的检查状态"""
    target_name: str
    src_rel: str
    source_path: Path
    target_path: Path
    status: ItemStatus
    detail: str = ""


def format_path(path: Path) -> str:
    """将绝对路径转换为友好的格式 (如使用 ~ 替代主目录)"""
    home = str(Path.home())
    path_str = str(path)
    if path_str == home:
        return "~"
    if path_str.startswith(home + "/"):
        return "~" + path_str[len(home):]
    return path_str


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
        DeployTarget(
            name="gdb",
            source_dir=project_root / "gdb",
            deploy_map={
                ".gdbinit": str(home / ".gdbinit"),
            }
        ),
    ]
    return targets


def inspect_item(target_name: str, src_rel: str, source_path: Path, target_path: Path) -> DeployItem:
    """检查单个配置项的当前状态"""
    if not source_path.exists():
        return DeployItem(
            target_name=target_name,
            src_rel=src_rel,
            source_path=source_path,
            target_path=target_path,
            status=ItemStatus.MISSING_SOURCE,
            detail=f"仓库源文件不存在: {source_path}"
        )

    if not target_path.exists() and not target_path.is_symlink():
        return DeployItem(
            target_name=target_name,
            src_rel=src_rel,
            source_path=source_path,
            target_path=target_path,
            status=ItemStatus.NEED_LINK,
            detail="目标不存在，将创建软链接"
        )

    if target_path.is_symlink():
        try:
            link_target = os.readlink(target_path)
            # 对比真实物理路径
            if target_path.resolve() == source_path.resolve():
                return DeployItem(
                    target_name=target_name,
                    src_rel=src_rel,
                    source_path=source_path,
                    target_path=target_path,
                    status=ItemStatus.UP_TO_DATE,
                    detail=f"已正确链接 -> {link_target}"
                )
            else:
                return DeployItem(
                    target_name=target_name,
                    src_rel=src_rel,
                    source_path=source_path,
                    target_path=target_path,
                    status=ItemStatus.CONFLICT_LINK,
                    detail=f"指向其他位置 -> {link_target}"
                )
        except Exception as e:
            return DeployItem(
                target_name=target_name,
                src_rel=src_rel,
                source_path=source_path,
                target_path=target_path,
                status=ItemStatus.CONFLICT_LINK,
                detail=f"软链接异常 -> {e}"
            )

    if target_path.is_file():
        return DeployItem(
            target_name=target_name,
            src_rel=src_rel,
            source_path=source_path,
            target_path=target_path,
            status=ItemStatus.CONFLICT_FILE,
            detail="已存在普通文件"
        )

    if target_path.is_dir():
        return DeployItem(
            target_name=target_name,
            src_rel=src_rel,
            source_path=source_path,
            target_path=target_path,
            status=ItemStatus.CONFLICT_DIR,
            detail="已存在目录"
        )

    return DeployItem(
        target_name=target_name,
        src_rel=src_rel,
        source_path=source_path,
        target_path=target_path,
        status=ItemStatus.CONFLICT_FILE,
        detail="已存在未知类型文件"
    )


def display_plan(items_by_target: dict[str, list[DeployItem]]) -> tuple[int, int, int, int]:
    """
    展示部署计划与当前状态
    返回: (待创建数, 冲突数, 已就绪数, 源缺失数)
    """
    print("\n📋 部署计划与当前状态:")
    print("-" * 60)

    count_need_link = 0
    count_conflict = 0
    count_up_to_date = 0
    count_missing = 0

    for target_name, items in items_by_target.items():
        print(f"\n[{target_name}]")
        for item in items:
            dst_disp = format_path(item.target_path)

            if item.status == ItemStatus.UP_TO_DATE:
                icon = "✓"
                tag = "[已就绪]"
                count_up_to_date += 1
                desc = f"{item.src_rel} -> {dst_disp}"
            elif item.status == ItemStatus.NEED_LINK:
                icon = "+"
                tag = "[待创建]"
                count_need_link += 1
                desc = f"{item.src_rel} -> {dst_disp}"
            elif item.status in (ItemStatus.CONFLICT_FILE, ItemStatus.CONFLICT_DIR, ItemStatus.CONFLICT_LINK):
                icon = "!"
                tag = "[有冲突]"
                count_conflict += 1
                desc = f"{item.src_rel} -> {dst_disp} ({item.detail})"
            else:  # MISSING_SOURCE
                icon = "✗"
                tag = "[源缺失]"
                count_missing += 1
                desc = f"{item.src_rel} ({item.detail})"

            print(f"  {icon} {tag:<8} {desc}")

    total = count_need_link + count_conflict + count_up_to_date + count_missing
    print("\n" + "-" * 60)
    print(f"统计: 共 {total} 项 (待创建: {count_need_link}, 冲突需覆盖: {count_conflict}, 已是最新: {count_up_to_date}, 异常缺失: {count_missing})")
    print("=" * 60)

    return count_need_link, count_conflict, count_up_to_date, count_missing


def prompt_conflict(target_path: Path, conflict_desc: str) -> tuple[Optional[bool], bool]:
    """
    提示用户是否覆盖冲突
    返回: (choice, is_all)
      choice: True=覆盖, False=跳过, None=取消
      is_all: True=全部覆盖
    """
    print(f"\n  冲突: {format_path(target_path)}")
    print(f"  状态: {conflict_desc}")

    while True:
        try:
            response = input("  是否覆盖? [y/n/a/q] (y=覆盖, n=跳过, a=全部覆盖, q=取消): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n  操作已取消")
            return None, False

        if response in ('y', 'yes'):
            return True, False
        elif response in ('n', 'no'):
            return False, False
        elif response in ('a', 'all'):
            return True, True
        elif response in ('q', 'quit'):
            return None, False
        else:
            print("  无效输入，请输入 y, n, a 或 q")


def create_link(source: Path, target: Path) -> tuple[bool, str]:
    """创建软链接"""
    try:
        target.parent.mkdir(parents=True, exist_ok=True)

        if target.is_symlink() or target.is_file():
            target.unlink()
        elif target.is_dir():
            shutil.rmtree(target)

        target.symlink_to(source)
        return True, f"已链接 -> {source}"
    except Exception as e:
        return False, f"链接失败: {e}"


def main():
    import argparse

    parser = argparse.ArgumentParser(description="配置文件部署工具 (软链接管理)")
    parser.add_argument("targets", nargs="*", metavar="TARGET",
                        help="指定部署的目标模块 (如: tmux gdb)，默认部署全部")
    parser.add_argument("-f", "--force", action="store_true",
                        help="强制重新链接并覆盖冲突，不询问")
    parser.add_argument("-l", "--list", action="store_true",
                        help="仅预览展示部署计划与当前状态，不执行变更")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="自动确认开始部署，冲突时仍提示 (除非配合 -f)")
    args = parser.parse_args()

    project_root = Path(__file__).parent.resolve()

    print("=" * 60)
    print("配置文件部署工具")
    print("=" * 60)
    print(f"项目根目录: {project_root}")

    all_targets = get_targets(project_root)

    # 目标过滤
    if args.targets:
        target_name_set = set(args.targets)
        available_names = {t.name for t in all_targets}
        unknown = target_name_set - available_names
        if unknown:
            print(f"\n错误: 未知目标模块: {', '.join(unknown)}")
            print(f"可用模块: {', '.join(sorted(available_names))}")
            return 1
        targets = [t for t in all_targets if t.name in target_name_set]
    else:
        targets = all_targets

    # 收集与检查状态
    items_by_target: dict[str, list[DeployItem]] = {}
    for target in targets:
        items = []
        for src_rel, dst_str in target.deploy_map.items():
            source = target.source_dir / src_rel
            target_path = Path(dst_str)
            item = inspect_item(target.name, src_rel, source, target_path)
            items.append(item)
        items_by_target[target.name] = items

    # 展示将要做的部署清单与状态
    n_need, n_conflict, n_up_to_date, n_missing = display_plan(items_by_target)

    # 如果仅为列表模式，直接退出
    if args.list:
        return 0

    has_changes = (n_need > 0 or n_conflict > 0)
    if not has_changes and not args.force:
        print("\n✨ 所有配置均已正确链接，无需执行变更。")
        print("   (如需强制重新创建软链接，可使用 -f / --force 参数)")
        return 0

    # 询问是否开始部署
    if not args.yes and not args.force:
        try:
            confirm = input("\n是否确认执行部署? [Y/n]: ").strip().lower()
            if confirm in ('n', 'no', 'q'):
                print("操作已取消。")
                return 0
        except (KeyboardInterrupt, EOFError):
            print("\n操作已取消。")
            return 0

    print("\n🚀 开始部署...")
    total_success, total_fail, total_skipped = 0, 0, 0
    overwrite_all = args.force

    for target_name, items in items_by_target.items():
        print(f"\n[{target_name}]")
        for item in items:
            dst_disp = format_path(item.target_path)

            if item.status == ItemStatus.MISSING_SOURCE:
                print(f"  ✗ {dst_disp}: {item.detail}")
                total_fail += 1
                continue

            # 如果已是最新且未指定 force，直接跳过处理
            if item.status == ItemStatus.UP_TO_DATE and not args.force:
                print(f"  ✓ {dst_disp}: 保持现有软链接")
                total_success += 1
                continue

            # 处理冲突
            is_conflict = item.status in (ItemStatus.CONFLICT_FILE, ItemStatus.CONFLICT_DIR, ItemStatus.CONFLICT_LINK)
            if is_conflict and not overwrite_all:
                choice, is_all = prompt_conflict(item.target_path, item.detail)
                if choice is None:
                    print("  操作已终止")
                    return 1
                elif choice is False:
                    print(f"  - {dst_disp}: 已跳过")
                    total_skipped += 1
                    continue
                if is_all:
                    overwrite_all = True

            # 创建链接
            ok, msg = create_link(item.source_path, item.target_path)
            if ok:
                print(f"  ✓ {dst_disp}: {msg}")
                total_success += 1
            else:
                print(f"  ✗ {dst_disp}: {msg}")
                total_fail += 1

    print("\n" + "=" * 60)
    print(f"完成: 成功 {total_success}, 失败 {total_fail}, 跳过 {total_skipped}")
    print("=" * 60)

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
