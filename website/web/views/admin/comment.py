#!/usr/bin/env python3

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (  # type: ignore[import-untyped]
    login_required,
)
from flask_paginate import (  # type: ignore[import-untyped]
    Pagination,
    get_page_args,
    get_parameter,
)
from sqlalchemy import or_
from werkzeug import Response as WerkzeugResponse

from website.lib.utils import escape_ilike
from website.models import (
    Comment,
)
from website.web.bootstrap import db
from website.web.permissions import admin_permission

admin_comment_bp = Blueprint("admin_comment_bp", __name__, url_prefix="/admin/comment")
admin_comments_bp = Blueprint(
    "admin_comments_bp", __name__, url_prefix="/admin/comments"
)


@admin_comments_bp.route("/", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def list_comments() -> str:
    comment_query = request.args.get("query", "")
    comments = Comment.query
    if comment_query:
        escaped_query = escape_ilike(comment_query)
        comments = comments.filter(
            or_(
                Comment.title.ilike(f"%{escaped_query}%", escape="\\"),
                Comment.description.ilike(f"%{escaped_query}%", escape="\\"),
                Comment.author.has(name=comment_query),
            )
        )
    comments = comments.order_by(Comment.timestamp.desc())
    page, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page"
    )
    page_name = get_parameter()
    per_page_name = get_parameter(default="per_page")
    pagination = Pagination(
        total=comments.count(),
        record_name="comments",
        css_framework="bootstrap5",
        **{page_name: page, per_page_name: per_page},
    )
    comments = comments.offset(offset).limit(per_page)
    return render_template(
        "admin/comments.html", comments=comments, pagination=pagination
    )


@admin_comment_bp.route("/<uuid:comment_uuid>", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def view_comment(comment_uuid: str) -> str:
    comment = Comment.query.filter(Comment.uuid == comment_uuid).first()
    if comment is None:
        abort(404)
    return render_template("admin/view_comment.html", comment=comment)


@admin_comment_bp.route("/toggle/<uuid:comment_uuid>", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def toggle_comment(comment_uuid: str) -> WerkzeugResponse:
    """Publish/Unpublish a comment."""
    comment = Comment.query.filter(Comment.uuid == comment_uuid).first()
    if comment is None:
        abort(404)
    comment.is_published = not comment.is_published
    db.session.commit()
    flash(
        "Comment {status}.".format(
            status="published" if comment.is_published else "unpublished"
        ),
        "success",
    )
    return redirect(url_for("admin_comments_bp.list_comments"))


@admin_comment_bp.route("/delete/<uuid:comment_uuid>", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def delete_comment(comment_uuid: str) -> WerkzeugResponse:
    """Delete a comment."""
    comment = Comment.query.filter(Comment.uuid == comment_uuid).first()
    if comment is None:
        abort(404)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted.", "success")
    return redirect(url_for("admin_comments_bp.list_comments"))
