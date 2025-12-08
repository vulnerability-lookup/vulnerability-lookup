#!/usr/bin/env python3

import json
from datetime import datetime, timezone
from uuid import UUID

from flask import (
    Blueprint,
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (  # type: ignore[import-untyped]
    current_user,
    login_required,
)
from flask_paginate import (  # type: ignore[import-untyped]
    Pagination,
    get_page_args,
    get_parameter,
)
from sqlalchemy import or_
from werkzeug import Response as WerkzeugResponse

from website.lib.utils import allowed_file, escape_ilike
from website.models import (
    Sighting,
    User,
)
from website.web.bootstrap import db
from website.web.forms import (
    SightingForm,
)
from website.web.permissions import admin_permission

admin_sighting_bp = Blueprint(
    "admin_sighting_bp", __name__, url_prefix="/admin/sighting"
)
admin_sightings_bp = Blueprint(
    "admin_sightings_bp", __name__, url_prefix="/admin/sightings"
)


@admin_sightings_bp.route("/", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def list_sightings() -> str:
    sighting_query = request.args.get("query", "")
    sightings = Sighting.query
    if sighting_query:
        escaped_query = escape_ilike(sighting_query)
        try:
            uuid_obj = UUID(sighting_query)
        except Exception:
            uuid_obj = None
        if uuid_obj:
            sightings = sightings.filter(
                or_(
                    Sighting.uuid == uuid_obj,
                    Sighting.type == sighting_query,
                    Sighting.source.ilike(f"%{escaped_query}%", escape="\\"),
                    Sighting.vulnerability.ilike(f"%{escaped_query}%", escape="\\"),
                    Sighting.author.has(login=escaped_query),
                )
            )
        else:
            sightings = sightings.filter(
                or_(
                    Sighting.type == sighting_query,
                    Sighting.source.ilike(f"%{escaped_query}%", escape="\\"),
                    Sighting.vulnerability.ilike(f"%{escaped_query}%", escape="\\"),
                    Sighting.author.has(login=escaped_query),
                )
            )
    sightings = sightings.order_by(Sighting.creation_timestamp.desc())
    page, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page"
    )
    page_name = get_parameter()
    per_page_name = get_parameter(default="per_page")
    pagination = Pagination(
        total=sightings.count(),
        record_name="sightings",
        css_framework="bootstrap5",
        **{page_name: page, per_page_name: per_page},
    )
    sightings = sightings.offset(offset).limit(per_page)

    return render_template(
        "admin/sightings.html",
        sightings=sightings,
        pagination=pagination,
    )


@admin_sighting_bp.route("/<uuid:sighting_uuid>/edit", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def form_sighting(sighting_uuid: str = "") -> str:
    """Return a form to edit a sighting."""
    action = "Edit the sighting"
    head_titles = [action]

    sighting = Sighting.query.filter(Sighting.uuid == sighting_uuid).first()
    if None is sighting:
        abort(404)

    form = SightingForm(obj=sighting)

    return render_template(
        "admin/edit_sighting.html",
        action=action,
        head_titles=head_titles,
        form=form,
        sighting=sighting,
    )


@admin_sighting_bp.route("/<uuid:sighting_uuid>/edit", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def process_sighting_form(sighting_uuid: str = "") -> str | WerkzeugResponse:
    """Edit a sighting."""
    form = SightingForm()

    sighting = Sighting.query.filter(Sighting.uuid == sighting_uuid).first()
    if None is sighting:
        abort(404)

    if not form.validate():
        return render_template("admin/edit_sighting.html", form=form)

    form.populate_obj(sighting)
    try:
        db.session.commit()
        flash("Sighting successfully updated.", "success")
    except Exception:
        db.session.rollback()
        flash("Error when updating sighting.", "danger")
    return redirect(
        url_for("admin_sighting_bp.form_sighting", sighting_uuid=sighting.uuid)
    )


@admin_sightings_bp.route("/export", methods=["GET"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def export_sightings() -> WerkzeugResponse:
    """Export sightings in a JSON file."""
    now = datetime.now(timezone.utc).isoformat()
    to_return = []
    for sighting in Sighting.query.filter():
        to_return.append(sighting.to_dict())
    response = make_response(to_return)
    response.mimetype = "application/json"
    response.headers["Content-Disposition"] = (
        f"attachment; filename=sightings_{now}.json"
    )
    return response


@admin_sightings_bp.route("/import", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def import_sightings() -> WerkzeugResponse:
    """Import sightings from a JSON sighting export file."""
    if request.files.get("sightings", False):
        data = request.files.get("sightings", None)
        if data is None or data.filename is None or not allowed_file(data.filename):
            flash("File not allowed.", "danger")
            return redirect(url_for("admin_bp.dashboard"))

        try:
            sightings = json.loads(data.read())
        except Exception:
            flash("Problem when reading file.", "danger")
            return redirect(url_for("admin_bp.dashboard"))

        nb_imported_sightings = 0
        for sighting in sightings:
            try:
                author_id = (
                    User.query.filter(User.uuid == sighting["author"]).first().id
                )
            except Exception:
                author_id = current_user.id
            sighting.pop("author")

            if not Sighting.query.get(UUID(sighting["uuid"])):
                try:
                    new_sighting = Sighting(**sighting, author_id=author_id)
                except Exception:
                    continue
                db.session.add(new_sighting)
                nb_imported_sightings += 1
        db.session.commit()
        flash(f"{nb_imported_sightings} sightings imported.", "success")
    return redirect(url_for("admin_bp.dashboard"))


@admin_sighting_bp.route("/<uuid:sighting_uuid>/delete", methods=["POST"])
@login_required  # type: ignore[untyped-decorator]
@admin_permission.require(http_exception=403)  # type: ignore[untyped-decorator]
def delete_sighting(sighting_uuid: str = "") -> WerkzeugResponse:
    """Allow administrators to delete any sightings."""
    sighting = Sighting.query.filter(Sighting.uuid == sighting_uuid).first()
    if sighting is None:
        abort(404)
    db.session.delete(sighting)
    db.session.commit()
    flash("Sighting deleted.", "success")
    return redirect(url_for("admin_sightings_bp.list_sightings"))
