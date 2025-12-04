#!/usr/bin/env python3

from flask import (
    Blueprint,
    render_template,
    request,
)
from flask_login import (  # type: ignore[import-untyped]
    login_required,
)
from flask_paginate import (  # type: ignore[import-untyped]
    Pagination,
    get_page_args,
    get_parameter,
)
from sqlalchemy import desc, distinct, func, or_

from website.lib.utils import escape_ilike
from website.models import (
    Notification,
    User,
)
from website.web.bootstrap import db
from website.web.permissions import admin_permission

admin_notification_bp = Blueprint(
    "admin_notification_bp", __name__, url_prefix="/admin/notification"
)
admin_notifications_bp = Blueprint(
    "admin_notifications_bp", __name__, url_prefix="/admin/notifications"
)


@admin_notifications_bp.route("/", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def list_notifications() -> str:
    notification_query = request.args.get("query", "")
    notifications = Notification.query
    if notification_query:
        escaped_query = escape_ilike(notification_query)
        notifications = notifications.filter(
            or_(
                Notification.vendor.ilike(f"%{escaped_query}%", escape="\\"),
                Notification.product.ilike(f"%{escaped_query}%", escape="\\"),
                Notification.subscriber.has(login=escaped_query),
            )
        )
    notifications = notifications.order_by(Notification.last_execution_time.desc())

    # Pagination
    page, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page"
    )
    page_name = get_parameter()
    per_page_name = get_parameter(default="per_page")
    pagination = Pagination(
        total=notifications.count(),
        record_name="notifications",
        css_framework="bootstrap5",
        **{page_name: page, per_page_name: per_page},
    )
    notifications = notifications.offset(offset).limit(per_page)

    # Top notifications
    top_notifications = (
        db.session.query(
            func.lower(Notification.vendor).label("vendor"),
            func.lower(Notification.product).label("product"),
            func.count().label("count"),
        )
        .group_by(func.lower(Notification.vendor), func.lower(Notification.product))
        .order_by(desc("count"))
        .limit(10)
        .all()
    )

    # Count the number of distinct users having created at least one notification
    nb_users_with_notifications = db.session.query(
        func.count(distinct(Notification.user_id))
    ).scalar()

    # Top users: those who use the notification system the most.
    top_users = (
        db.session.query(
            Notification.user_id,
            User.login,
            func.count(Notification.id).label("notification_count"),
        )
        .join(User, Notification.user_id == User.id)  # Join with the User table
        .group_by(Notification.user_id, User.login)
        .order_by(desc("notification_count"))
        .limit(10)
        .all()
    )

    return render_template(
        "admin/notifications.html",
        notifications=notifications,
        top_notifications=top_notifications,
        nb_users_with_notifications=nb_users_with_notifications,
        top_users=top_users,
        pagination=pagination,
    )
