import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import markdown  # type: ignore[import-untyped]
from bleach import clean  # type: ignore[import-untyped]
from dateutil.parser import parse  # type: ignore[import-untyped]
from gcve import to_gcve_id
from markdown.extensions.tables import TableExtension  # type: ignore[import-untyped]
from markupsafe import Markup

from website.lib.constants import ALLOWED_ATTRIBUTES, ALLOWED_TAGS
from website.lib.sanitizers import sanitize_html_fragment

#
# This module defines custom Jinja filters that are registered and exposed
# via the `bootstrap.py` module for use in templates.
#

vulnlookup = None


def init_filters(vl: Any) -> None:
    global vulnlookup
    vulnlookup = vl

    import website.web.filters.capec as capec
    import website.web.filters.cvev5 as cvev5
    import website.web.filters.ossf as ossf

    _filters = [capec, cvev5, ossf]


def cve_to_gcve(cve: str) -> str:
    """Convert a CVE ID to a GCVE-compatible ID.
    If the input is not a CVE ID returns the string unchanged."""
    try:
        return to_gcve_id(cve)
    except ValueError:
        return cve


def is_url(value: str) -> bool:
    if not value:
        return False
    url_pattern = re.compile(
        r"^(https?:\/\/)?"  # optional scheme
        r"(([a-zA-Z\d-]+\.)+[a-zA-Z]{2,}|localhost|"  # domain or localhost
        r"(\d{1,3}\.){3}\d{1,3})"  # or IP address
        r"(:\d+)?"  # optional port
        r"(\/[-a-zA-Z\d%_.~+]*)*"  # path
        r"(\?[;&a-zA-Z\d%_.~+=-]*)?"  # query string
        r"(\#[-a-zA-Z\d_]*)?$",  # fragment locator
        re.IGNORECASE,
    )
    return re.match(url_pattern, value) is not None


def str_to_obj(str: str) -> Dict[str, Any]:
    """Returns a Python object from a (JSON) string."""
    try:
        return json.loads(str)
    except Exception:
        return {"message": "Error when deserializing the string."}


def datetimeformat(value: datetime, format: str = "%Y-%m-%d %H:%M") -> str:
    """Converts a datetime obect to a formatted string."""
    if None is value:
        return ""
    return value.strftime(format)


def string_to_datetime(value: str, format: str = "") -> str:
    """Converts the format of a formatted string."""
    if None is value:
        return ""
    now = datetime.now(timezone.utc)
    try:
        new_date_time = parse(value)
    except Exception:
        return value
    if format:
        return datetimeformat(new_date_time, format)
    elif new_date_time.year == now.year and new_date_time.month == now.month:
        return datetimeformat(new_date_time, "%d")
    elif new_date_time.year == now.year:
        return datetimeformat(new_date_time, "%b %d")
    else:
        return datetimeformat(new_date_time)


def to_markdown(value: str) -> str:
    """Converts a markdown string to sanitized HTML."""
    try:
        # Convert Markdown to HTML
        raw_html = markdown.markdown(
            value, extensions=["fenced_code", TableExtension(use_align_attribute=True)]
        )

        # Sanitize HTML using bleach
        safe_html = clean(
            raw_html,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True,  # Remove disallowed tags completely
        )
        return safe_html
    except Exception:
        return value


def render_tag_badges(tags: list[str]) -> str:
    """
    Render a list of tags as styled Bootstrap badges.
    """
    if not tags:
        return ""

    html = []
    for tag in tags:
        html.append(f'<span class="badge bg-secondary me-1">{tag}</span>')
    return Markup("".join(html))


def hash(value: str) -> str:
    """Returns a hexadecimal SHA 256 hash of the input value."""
    m = hashlib.sha256()
    m.update(value.encode())
    return m.hexdigest()


def update_query_params(url: str, **new_params: str) -> str:
    """
    Update or add query parameters to a given URL.

    This function parses the input URL, extracts its query parameters, and
    updates them with the new parameters provided in `new_params`. If a
    parameter already exists in the URL, its value is replaced. This ensures
    that no duplicate query parameters are added to the URL.

    Args:
        url (str): The URL to be updated.
        **new_params: Arbitrary keyword arguments representing the query
                      parameters to be added or updated in the URL.

    Returns:
        str: The updated URL with the new query parameters.
    """
    # Parse the URL and extract its components
    url_parts = urlparse(url)

    # Parse the query string into a dictionary (parse_qs returns lists for values)
    query_params: Dict[str, str] = {
        key: value[0] for key, value in parse_qs(url_parts.query).items()
    }

    # Update with the new parameters (this will replace any existing ones)
    query_params.update(new_params)

    # Reconstruct the URL with updated query parameters
    updated_query: str = urlencode(query_params)
    new_url: str = urlunparse(url_parts._replace(query=updated_query))

    return new_url


def sanitize_html(html_str: str) -> str:
    return sanitize_html_fragment(html_str)
