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
    Bundle,
)
from website.web.bootstrap import db
from website.web.permissions import admin_permission

admin_bundle_bp = Blueprint("admin_bundle_bp", __name__, url_prefix="/admin/bundle")
admin_bundles_bp = Blueprint("admin_bundles_bp", __name__, url_prefix="/admin/bundles")


@admin_bundles_bp.route("/", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def list_bundles() -> str:
    bundle_query = request.args.get("query", "")
    bundles = Bundle.query
    if bundle_query:
        escaped_query = escape_ilike(bundle_query)
        bundles = bundles.filter(
            or_(
                Bundle.name.ilike(f"%{escaped_query}%", escape="\\"),
                Bundle.description.ilike(f"%{escaped_query}%", escape="\\"),
                Bundle.author.has(name=escaped_query),
            )
        )
    bundles = bundles.order_by(Bundle.timestamp.desc())
    page, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page"
    )
    page_name = get_parameter()
    per_page_name = get_parameter(default="per_page")
    pagination = Pagination(
        total=bundles.count(),
        record_name="bundles",
        css_framework="bootstrap5",
        **{page_name: page, per_page_name: per_page},
    )
    bundles = bundles.offset(offset).limit(per_page)

    return render_template(
        "admin/bundles.html",
        bundles=bundles,
        pagination=pagination,
    )


@admin_bundle_bp.route("/create", methods=["GET"])
@admin_bundle_bp.route("/edit/<uuid:bundle_uuid>", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def form_bundle(bundle_uuid: str = "") -> str:
    """Returns a page in order to create or edit a bundle.
    Only available to administrators."""
    action = "Create a bundle"
    head_titles = [action]

    if not bundle_uuid:
        # Creation of a new bundle
        return render_template(
            "admin/edit_bundle.html",
            action=action,
            head_titles=head_titles,
            bundle={},
        )

    # Edition of an existing bundle
    bundle = Bundle.query.filter(Bundle.uuid == bundle_uuid).first()
    action = "Edit a bundle"
    head_titles = [action]
    head_titles.append(bundle.name)
    return render_template(
        "admin/edit_bundle.html",
        action=action,
        head_titles=head_titles,
        bundle=bundle,
    )


@admin_bundle_bp.route("/delete/<uuid:bundle_uuid>", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def delete_bundle(bundle_uuid: str) -> WerkzeugResponse:
    """Delete a bundle."""
    bundle = Bundle.query.filter(Bundle.uuid == bundle_uuid).first()
    if bundle is None:
        abort(404)
    db.session.delete(bundle)
    db.session.commit()
    flash("Bundle deleted.", "success")
    return redirect(url_for("admin_bundles_bp.list_bundles"))
