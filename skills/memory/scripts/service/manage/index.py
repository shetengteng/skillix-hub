#!/usr/bin/env python3
"""
Memory Skill 统一管理工具

子命令: list / stats / delete / restore / edit / export / cleanup / rebuild-index / doctor / config
所有输出为 JSON（stdout），错误到 stderr。
"""
import sys
import os
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_SCRIPT_DIR, "..", ".."))
sys.path.insert(0, _SCRIPT_DIR)

from service.config import get_config

from commands._helpers import _json_out
from commands.cmd_list import cmd_list, cmd_stats
from commands.cmd_delete import cmd_delete, cmd_restore
from commands.cmd_edit import cmd_edit, cmd_export, cmd_cleanup
from commands.cmd_index import cmd_rebuild_index, cmd_doctor
from commands.cmd_config import (
    cmd_config_show,
    cmd_config_get,
    cmd_config_set,
    cmd_config_reset,
    cmd_config_validate,
)


def main():
    parser = argparse.ArgumentParser(prog="manage_memory.py", description="Memory Skill 管理工具")
    parser.add_argument("--project-path", default=os.getcwd())
    sub = parser.add_subparsers(dest="command")

    # list
    p = sub.add_parser("list")
    p.add_argument("--days", type=int)
    p.add_argument("--keyword")
    p.add_argument("--id")
    p.add_argument("--type")
    p.add_argument("--from", dest="from_date")
    p.add_argument("--to")
    p.add_argument("--before")
    p.add_argument("--scope", choices=["daily", "sessions", "all"])
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--include-deleted", action="store_true")

    # stats
    sub.add_parser("stats")

    # delete
    p = sub.add_parser("delete")
    p.add_argument("--keyword")
    p.add_argument("--id")
    p.add_argument("--type")
    p.add_argument("--from", dest="from_date")
    p.add_argument("--to")
    p.add_argument("--before")
    p.add_argument("--scope", choices=["daily", "sessions", "all"])
    p.add_argument("--all", dest="all_flag", action="store_true")
    p.add_argument("--purge", action="store_true")
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--no-sync", action="store_true")

    # restore
    p = sub.add_parser("restore")
    p.add_argument("--id")
    p.add_argument("--from", dest="from_date")
    p.add_argument("--from-backup")
    p.add_argument("--no-sync", action="store_true")

    # edit
    p = sub.add_parser("edit")
    p.add_argument("--id")
    p.add_argument("--content")
    p.add_argument("--memory-type")
    p.add_argument("--confidence", type=float)
    p.add_argument("--entities")
    p.add_argument("--no-sync", action="store_true")

    # export
    p = sub.add_parser("export")
    p.add_argument("--output")
    p.add_argument("--scope", choices=["daily", "sessions", "all"])
    p.add_argument("--type")

    # cleanup
    p = sub.add_parser("cleanup")
    p.add_argument("--older-than", type=int)
    p.add_argument("--system-events", action="store_true")
    p.add_argument("--purge-deleted", action="store_true")
    p.add_argument("--scope", choices=["daily", "sessions", "all"])
    p.add_argument("--confirm", action="store_true")
    p.add_argument("--no-sync", action="store_true")

    # rebuild-index
    p = sub.add_parser("rebuild-index")
    p.add_argument("--full", action="store_true")

    # doctor
    sub.add_parser("doctor")

    # config
    cp = sub.add_parser("config")
    cs = cp.add_subparsers(dest="action")
    cs.add_parser("show")
    g = cs.add_parser("get")
    g.add_argument("key")
    s = cs.add_parser("set")
    s.add_argument("key")
    s.add_argument("value")
    s.add_argument("--global", dest="scope_global", action="store_true")
    r = cs.add_parser("reset")
    r.add_argument("key")
    r.add_argument("--global", dest="scope_global", action="store_true")
    cs.add_parser("validate")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(2)

    handlers = {
        "list": cmd_list,
        "stats": cmd_stats,
        "delete": cmd_delete,
        "restore": cmd_restore,
        "edit": cmd_edit,
        "export": cmd_export,
        "cleanup": cmd_cleanup,
        "rebuild-index": cmd_rebuild_index,
        "doctor": cmd_doctor,
    }

    if args.command == "config":
        cfg = get_config(args.project_path)
        config_handlers = {
            "show": cmd_config_show,
            "get": cmd_config_get,
            "set": cmd_config_set,
            "reset": cmd_config_reset,
            "validate": cmd_config_validate,
        }
        if not args.action or args.action not in config_handlers:
            cp.print_help()
            sys.exit(2)
        config_handlers[args.action](cfg, args)
    elif args.command in handlers:
        handlers[args.command](args)
    else:
        _json_out("error", args.command, error={"code": "NOT_IMPLEMENTED", "message": f"未实现: {args.command}"})
        sys.exit(2)


if __name__ == "__main__":
    main()
