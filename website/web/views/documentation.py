#!/usr/bin/env python3

from flask import Blueprint, abort, flash, send_from_directory
from markupsafe import Markup
from werkzeug import Response as WerkzeugResponse

from vulnerabilitylookup.default import get_homedir

# Define the blueprint
homedir = get_homedir()
static_folder = homedir.joinpath("docs/_build/html")
documentation_bp = Blueprint(
    "documentation_bp",
    __name__,
    url_prefix="/documentation",
    static_folder=static_folder,
)


@documentation_bp.route("/<path:filename>")
def serve_documentation(filename: str) -> WerkzeugResponse:
    """Serve static files from the Sphinx build folder."""
    if not static_folder.exists() or not documentation_bp.static_folder:
        flash(
            Markup(
                "The documentation has yet to be generated. "
                "See the <a href='https://vulnerability.circl.lu/documentation/command-line-interface.html' target='_blank'>official documentation</a>."
            ),
            "warning",
        )
        return abort(404)
    return send_from_directory(documentation_bp.static_folder, filename)


@documentation_bp.route("/")
def serve_index() -> WerkzeugResponse:
    """Redirect `/documentation` to `/documentation/index.html`"""
    if not static_folder.exists() or not documentation_bp.static_folder:
        flash(
            Markup(
                "The documentation has yet to be generated. "
                "See the <a href='https://vulnerability.circl.lu/documentation/command-line-interface.html' target='_blank'>official documentation</a>."
            ),
            "warning",
        )
        return abort(404)
    return send_from_directory(documentation_bp.static_folder, "index.html")
