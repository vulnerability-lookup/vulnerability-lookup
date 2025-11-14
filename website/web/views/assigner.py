from flask import Blueprint, render_template, request

from website.web.bootstrap import vulnerabilitylookup

# Create the Blueprint
assigners_bp = Blueprint(
    "assigners_bp", __name__, url_prefix="/assigners", template_folder="templates"
)


@assigners_bp.route("/", methods=["GET"])
def index() -> str:
    """Returns a pages listing Vulnerability Assigners, sorted by score/occurences."""
    year = request.args.get("year")
    month = request.args.get("month")
    sort = request.args.get("sort", "desc")

    period = ""
    if year and month:
        period = f"{year}-{month}"
    elif year:
        period = year

    top_assigners = vulnerabilitylookup.get_top_assigners(top_n=2000, period=period)

    if sort == "asc":
        top_assigners.sort(key=lambda c: c[1])
    else:
        top_assigners.sort(key=lambda c: c[1], reverse=True)

    return render_template(
        "assigners/assigner_list.html", assigners=top_assigners, sort=sort
    )
