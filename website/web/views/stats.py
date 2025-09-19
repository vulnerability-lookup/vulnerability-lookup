from flask import Blueprint
from flask import render_template

stats_bp = Blueprint("stats_bp", __name__, url_prefix="/stats")


@stats_bp.route("/", methods=["GET"])
def index() -> str:
    """Returns a pages which displays various statistics."""
    return render_template("stats/stats.html")
