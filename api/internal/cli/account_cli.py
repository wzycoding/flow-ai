#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2026/6/18 
@Author : wzy
@File   : account_cli
"""
import base64
import secrets

import click
from flask.cli import with_appcontext

from internal.extension.database_extension import db
from internal.model import Account
from pkg.password import hash_password, validate_password


@click.group(name="account")
def account_cli() -> None:
    """账号维护命令。"""


@account_cli.command("seed-default")
@click.option("--email", envvar="DEFAULT_ACCOUNT_EMAIL", required=True)
@click.option("--password", envvar="DEFAULT_ACCOUNT_PASSWORD", required=True)
@with_appcontext
def seed_default_account(email: str, password: str) -> None:
    """幂等创建默认账号并同步密码。"""
    validate_password(password)

    account = db.session.query(Account).filter(Account.email == email).one_or_none()
    with db.auto_commit():
        if account is None:
            account = Account(
                email=email,
                name=email.split("@", 1)[0],
                avatar="",
            )
            db.session.add(account)
            db.session.flush()

        salt = secrets.token_bytes(16)
        account.password_salt = base64.b64encode(salt).decode()
        account.password = base64.b64encode(hash_password(password, salt)).decode()

    click.echo(f"Seeded default account: {email}")
