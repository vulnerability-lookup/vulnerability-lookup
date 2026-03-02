from uuid import UUID

from flask import Blueprint, abort, make_response, redirect, render_template, url_for
from flask_paginate import (  # type: ignore[import-untyped]
    Pagination,
    get_page_args,
    get_parameter,
    request,
)
from sqlalchemy import or_
from werkzeug import Response as WerkzeugResponse

from website.lib.utils import escape_ilike
from website.models import Organization, Product

organization_bp = Blueprint("organization_bp", __name__, url_prefix="/organization")
organizations_bp = Blueprint("organizations_bp", __name__, url_prefix="/organizations")


@organizations_bp.route("/", methods=["GET"])
def list_organizations() -> str:
    """Return the page which will display the list of organizations."""
    organization_query = request.args.get("query", "")
    only_gna = request.args.get("only_gna", False)

    organizations = Organization.query
    if organization_query:
        escaped_query = escape_ilike(organization_query)
        try:
            uuid_obj = UUID(organization_query)
        except Exception:
            uuid_obj = None
        if uuid_obj:
            organizations = organizations.filter(
                or_(
                    Organization.uuid == uuid_obj,
                    Organization.name.ilike(f"%{escaped_query}%", escape="\\"),
                    Organization.organization_type == organization_query,
                )
            )
        else:
            organizations = organizations.filter(
                or_(
                    Organization.organization_type == organization_query,
                    Organization.name.ilike(f"%{escaped_query}%", escape="\\"),
                    Organization.short_name.ilike(f"%{escaped_query}%", escape="\\"),
                    Organization.organization_type == organization_query,
                    Organization.products.any(
                        Product.name.ilike(
                            f"%{escaped_query}%", escape="\\"
                        )  # to find the organization based on a product name
                    ),
                )
            )
    if only_gna:
        organizations = organizations.filter(Organization.gna_id != None)  # noqa: E711

    organizations = organizations.order_by(Organization.updated_timestamp.desc())

    page, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page"
    )
    page_name = get_parameter()
    per_page_name = get_parameter(default="per_page")
    pagination = Pagination(
        total=organizations.count(),
        record_name="organizations",
        css_framework="bootstrap5",
        **{page_name: page, per_page_name: per_page},
    )
    organizations = organizations.offset(offset).limit(per_page)

    return render_template(
        "organizations/organizations.html",
        organizations=organizations,
        pagination=pagination,
    )


@organization_bp.route("/<uuid:organization_uuid>", methods=["GET"])
def get_by_uuid(organization_uuid: str) -> str:
    organization = Organization.query.filter_by(uuid=organization_uuid).first()
    if not organization:
        abort(404)

    return render_template(
        "organizations/organization.html",
        organization=organization,
        head_titles=[f"The {organization.name} Organization"],
    )


@organization_bp.route("/<string:gna_id>", methods=["GET"])
def get_by_gna(gna_id: str) -> WerkzeugResponse:
    """Lookup an Organization by its GNA identifier and redirect to UUID page.

    The incoming `gna_id` path parameter may be prefixed with ``GNA-`` (case
    insensitive). This function strips that prefix, ensures the remaining value
    is a valid integer, queries the database for an Organization with a
    matching numeric ``gna_id`` and redirects to the canonical organization
    page identified by UUID.

    Behavior:
    - If the path value does not start with the expected prefix, returns 404.
    - If the numeric part is not an integer, returns 404.
    - If no Organization matches the numeric GNA id, returns 404.

    Returns:
        A redirect `WerkzeugResponse` to ``organization_bp.get_by_uuid`` on
        success.
    """

    if gna_id.lower().startswith("gna-"):
        gna_id = gna_id[4:]
    else:
        abort(404)

    try:
        gna_int = int(gna_id)
    except ValueError:
        abort(404)

    organization = Organization.query.filter_by(gna_id=gna_int).first()
    if not organization:
        abort(404)

    return redirect(
        url_for("organization_bp.get_by_uuid", organization_uuid=organization.uuid)
    )


@organization_bp.route(
    "/<uuid:organization_uuid>/export_cpe_information",
    methods=["GET"],
)
def export_cpe_information(organization_uuid: str) -> WerkzeugResponse:
    organization = Organization.query.filter(
        Organization.uuid == organization_uuid
    ).first()
    if organization is None:
        abort(404)

    # Create a response with the raw JSON data
    response = make_response(organization.as_json())

    # Set headers for file download and proper content type
    response.headers["Content-Disposition"] = (
        f"attachment; filename={organization.uuid}.json"
    )
    response.headers["Content-Type"] = "application/json"

    return response
