#!/usr/bin/env python3

from datetime import timezone

import markdown  # type: ignore[import-untyped]
from feedgen.feed import FeedGenerator  # type: ignore[import-untyped]
from flask import (
    Blueprint,
    Response,
    abort,
    render_template,
    request,
    url_for,
)
from flask_paginate import (  # type: ignore[import-untyped]
    Pagination,
    get_page_args,
    get_parameter,
)
from markdown.extensions.tables import TableExtension  # type: ignore[import-untyped]

from vulnerabilitylookup.default import get_config
from website.lib.sanitizers import sanitize_html_fragment
from website.lib.utils import inject_xslt
from website.models import Bundle
from website.web.bootstrap import application

bundle_bp = Blueprint(
    "bundle_bp", __name__, url_prefix="/bundle", template_folder="bundles"
)
bundles_bp = Blueprint(
    "bundles_bp", __name__, url_prefix="/bundles", template_folder="bundles"
)

local_instance_name = get_config("generic", "local_instance_name").lower()


@bundles_bp.route("/", methods=["GET"])
def list_bundles() -> str:
    bundles = Bundle.query
    bundles = bundles.order_by(Bundle.creation_timestamp.desc())

    # Pagination
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
        "bundles/bundles.html", bundles=bundles, pagination=pagination
    )


@bundle_bp.route("/<uuid:bundle_uuid>", methods=["GET"])
def get(bundle_uuid: str = "") -> str:
    """Return details about the bundle."""
    elem = Bundle.query.filter(Bundle.uuid == bundle_uuid).first()
    if elem is None:
        abort(404)
    html_from_markdown = markdown.markdown(
        elem.description,
        extensions=["fenced_code", TableExtension(use_align_attribute=True)],
    )
    html_from_markdown = sanitize_html_fragment(html_from_markdown)
    return render_template(
        "bundles/bundle.html", bundle=elem, description=html_from_markdown
    )


@bundles_bp.route("/feed.<string:format>", defaults={"per_page": 10}, methods=["GET"])
def feed_bundles(per_page: int = 10, format: str = "atom") -> Response:
    """RSS/ATOM feed for the recent bundles."""
    user = request.args.get("user", "")
    public_domain = get_config("generic", "public_domain")
    _, per_page, offset = get_page_args(
        page_parameter="page", per_page_parameter="per_page"
    )
    feed_max_per_page = application.config.get("FEED_MAX_PER_PAGE", 50)
    if per_page > feed_max_per_page:
        per_page = feed_max_per_page
    fg = FeedGenerator()
    fg.id(f"https://{public_domain}/bundles/feed.{format}")
    fg.title("Most recent bundles.")
    fg.subtitle(f"Contains only the most {per_page} recent bundles.")
    fg.author(
        {
            "name": "Vulnerability-Lookup",
            "email": application.config.get("ADMIN_EMAIL", ""),
        }
    )
    fg.link(href=f"https://{public_domain}", rel="alternate")
    fg.language("en")

    query = Bundle.query
    if user:
        query = query.filter(Bundle.author.has(login=user))
    query = query.order_by(Bundle.timestamp.desc())
    bundles = query.offset(offset).limit(per_page)

    for bundle in bundles:
        fe = fg.add_entry()
        fe.author(
            [
                {
                    "name": bundle.author.name,
                    "uri": url_for(
                        "user_bp.profile", login=bundle.author.login, _external=True
                    ),
                }
            ]
        )
        fe.id(f"https://{public_domain}/bundle/{bundle.uuid}")
        fe.title(bundle.name)
        fe.link(href=f"https://{public_domain}/bundle/{bundle.uuid}")
        fe.content(bundle.description)
        fe.description(bundle.description)
        fe.published(bundle.timestamp.replace(tzinfo=timezone.utc))

    # Generate feed with XSLT
    feed_bytes = inject_xslt(
        fg.atom_str(pretty=True) if format == "atom" else fg.rss_str(pretty=True)
    )
    return Response(feed_bytes, mimetype="application/xml")
