from datetime import datetime, timedelta, timezone

from flask import Blueprint, abort, make_response, render_template
from flask_paginate import (  # type: ignore[import-untyped]
    request,
    Pagination,
    get_page_args,
    get_parameter,
)
from werkzeug import Response as WerkzeugResponse

from website.models import Product

product_bp = Blueprint("product_bp", __name__, url_prefix="/product")


@product_bp.route("/<uuid:product_uuid>", methods=["GET"])
def get(product_uuid: str) -> str:
    """Return a page with information related to the product given in parameter."""
    product = Product.query.filter(Product.uuid == product_uuid).first()
    if product is None:
        abort(404)

    since_days = int(request.args.get("since", 3000))
    if since_days > 3000:
        since_days = 3000

    since = datetime.now(timezone.utc) - timedelta(days=since_days)
    vulnerabilities = product.find_vulnerabilities(["cvelistv5"], since)
    vulnerabilities = vulnerabilities["cvelistv5"]

    page, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page"
    )
    page_name = get_parameter()
    per_page_name = get_parameter(default="per_page")
    pagination = Pagination(
        total=len(vulnerabilities),
        record_name="organizations",
        css_framework="bootstrap5",
        **{page_name: page, per_page_name: per_page},
    )
    vulnerabilities = vulnerabilities[offset : offset + per_page]

    head_titles = ["The " + product.name + " project"]
    return render_template(
        "products/product.html",
        product=product,
        vulnerabilities=vulnerabilities,
        head_titles=head_titles,
        pagination=pagination,
    )


@product_bp.route(
    "/<uuid:product_uuid>/export_cpe_information",
    methods=["GET"],
)
def export_cpe_information(product_uuid: str) -> WerkzeugResponse:
    """Export CPE information for the product."""
    product = Product.query.filter(Product.uuid == product_uuid).first()
    if product is None:
        abort(404)

    # Create a response with the raw JSON data
    response = make_response(product.as_json())

    # Set headers for file download and proper content type
    response.headers["Content-Disposition"] = (
        f"attachment; filename={product.uuid}.json"
    )
    response.headers["Content-Type"] = "application/json"

    return response
