#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/6/18 
@Author : wzy
@File   : __init__.py
"""
from flask import Flask

from .account_cli import account_cli


def register_cli(app: Flask) -> None:
    """注册项目内部CLI命令。"""
    app.cli.add_command(account_cli)
