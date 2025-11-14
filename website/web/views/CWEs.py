from collections import defaultdict

from flask import Blueprint, render_template, request
from flask_paginate import Pagination, get_page_args  # type: ignore[import-untyped]
from werkzeug.exceptions import abort

from website.web.bootstrap import vulnerabilitylookup

# Create the Blueprint
CWEs_bp = Blueprint(
    "CWEs_bp", __name__, url_prefix="/cwes", template_folder="templates"
)


@CWEs_bp.route("/", methods=["GET"])
def index() -> str:
    """Returns a pages listing CWEs, sorted by score/occurences."""
    year = request.args.get("year")
    month = request.args.get("month")
    sort = request.args.get("sort", "desc")

    period = ""
    if year and month:
        period = f"{year}-{month}"
    elif year:
        period = year

    top_cwes = vulnerabilitylookup.get_top_cwe(top_n=2000, period=period)

    cwes = []
    for cwe_id, score in top_cwes:
        cwe = vulnerabilitylookup.get_cwe(cwe_id)
        if cwe:
            cwe["Occurrences"] = int(score)
            cwes.append(cwe)

    if sort == "asc":
        cwes.sort(key=lambda c: c["Occurrences"])
    else:
        cwes.sort(key=lambda c: c["Occurrences"], reverse=True)

    return render_template("cwes/cwe_list.html", cwes=cwes, sort=sort)


@CWEs_bp.route("/<string:cwe_id>", methods=["GET"])
def cwe_detail(cwe_id: str) -> str:
    """Returns details related to the CWE specified in parameter."""
    cwe = vulnerabilitylookup.get_cwe(cwe_id)
    if not cwe:
        abort(404, description="CWE not found.")

    # Retrieval associated CAPECs
    capecs_raw = cwe.get("Related_Attack_Patterns", {}).get(
        "Related_Attack_Pattern", []
    )
    if isinstance(capecs_raw, dict):
        capecs_raw = [capecs_raw]
    elif isinstance(capecs_raw, str):
        capecs_raw = []

    capecs = []
    for pattern in capecs_raw:
        if isinstance(pattern, dict):
            capecs.append(
                {
                    "@CAPEC_ID": pattern.get("@CAPEC_ID") or pattern.get("@ID"),
                    "@Name": pattern.get("@Name", "Nom non disponible"),
                    "Description": pattern.get(
                        "Description", "Pas de description disponible."
                    ),
                }
            )
        else:
            capecs.append(
                {
                    "@CAPEC_ID": None,
                    "@Name": str(pattern),
                    "Description": "Pas de description disponible.",
                }
            )

    # Retrieval associated CVEs
    page, number, _ = get_page_args(page_parameter="page", per_page_parameter="number")
    number = number or 20
    page = max(page, 1)

    related_cves_data, total = vulnerabilitylookup.get_vulnerabilities_by_cwe(
        cwe_id, page=page, per_page=number
    )
    vulnerabilities = defaultdict(list)
    for vuln_id in related_cves_data:
        source = vulnerabilitylookup.get_vulnerability_source(vuln_id)
        vuln_data = vulnerabilitylookup.get_vulnerability(vuln_id)
        vulnerabilities[source].append((vuln_id, vuln_data))

    pagination = Pagination(
        page=page,
        total=total,
        per_page=number,
        record_name="CVEs",
    )

    return render_template(
        "cwes/cwe_detail.html",
        cwe=cwe,
        related_cves=related_cves_data,
        total=total,
        page=page,
        number=number,
        pagination=pagination,
        cwe_id=cwe_id,
        vulnerabilities=vulnerabilities,
        capecs=capecs,
    )
