#!/user/bin/env python
# -*- coding: utf-8 -*-
"""
@Time   : 2025/11/17 
@Author : wzy
@File   : __init__.py
"""
from .github_oauth import GithubOAuth
from .oauth import OAuthUserInfo, OAuth

__all__ = [
    "OAuthUserInfo",
    "OAuth",
    "GithubOAuth"

]
