#!/usr/bin/env python3

import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from flask import abort, request
from flask_login import current_user  # type: ignore[import-untyped]
from gcve import gcve0_to_cve

from website.models import User
from website.web.bootstrap import db
from website.web.permissions import login_user_bundle

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def auth_feedkey_func(func: Callable[P, R]) -> Callable[P, R]:
    """Authentication decorator using the X-FEED-KEY.
    It is used to protect the access to authenticated RSS/Atom feeds."""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if not current_user.is_authenticated:
            token = request.args.get("X-FEED-KEY")
            if not token:
                logger.warning("Missing X-FEED-KEY in request parameters.")
                abort(401, description="Authentication required.")

            user = User.query.filter(User.feedkey == token).first()
            if not user:
                logger.warning("Unauthorized access attempt with invalid token.")
                abort(401, description="Unauthorized.")

            if not user.is_active:
                logger.warning(f"Access denied for inactive user: {user.login}")
                abort(403, description="Account is not active.")

            login_user_bundle(user)
            user.last_seen = datetime.now(timezone.utc)
            db.session.commit()

        return func(*args, **kwargs)

    return wrapper


def convert_gcve0_to_cve_param(
    param_name: str = "vulnerability_id",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if param_name in kwargs:
                identifier: str = str(kwargs[param_name])
                try:
                    kwargs[param_name] = gcve0_to_cve(identifier)
                except ValueError:
                    pass
            return func(*args, **kwargs)

        return wrapper

    return decorator
