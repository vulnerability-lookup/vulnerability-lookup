from typing import Any, Dict

from website.web.filters import vulnlookup


def get_capec(capec_id: str) -> Dict[str, Any]:
    """Returns a CAPEC entry from a CAPEC id."""
    if vulnlookup is None:
        raise RuntimeError("vulnerabilitylookup not initialized")

    capec = vulnlookup.get_capec("CAPEC-" + capec_id)
    if not capec:
        return {"error": "CAPEC not found."}

    return {
        "@CAPEC_ID": capec.get("@CAPEC_ID") or capec.get("@ID") or capec_id,
        "@Name": capec.get("@Name", "Nom non disponible"),
        "Description": capec.get("Description", "Pas de description disponible."),
    }


def render_description(description: str | dict[str, Any]) -> list[str]:
    """
    Normalize a CWE mitigation description into a list of text elements.

    This function accepts either a plain string or a structured dictionary containing
    XHTML-formatted content. If the input is a string, it returns it wrapped in a list.
    If the input is a dictionary, it attempts to extract descriptive elements from
    the keys "xhtml:p", "xhtml:ul", and "xhtml:lu", handling various substructures
    such as lists and nested items under "xhtml:li".

    Args:
        description (str | dict[str, Any]): The input description, either as a plain
            string or a structured dictionary using XHTML-like tags.

    Returns:
        list[str]: A list of extracted text segments. If no content is found or the
        input is invalid, returns a list containing a default message.
    """
    if isinstance(description, str):
        return [description]

    if not isinstance(description, dict):
        return ["No description available"]

    elements = []

    for key in ("xhtml:p", "xhtml:ul", "xhtml:lu"):
        value = description.get(key)
        if value:
            if isinstance(value, str):
                elements.append(value)
            elif isinstance(value, list):
                elements.extend(value)
            elif isinstance(value, dict) and "xhtml:li" in value:
                items = value["xhtml:li"]
                if isinstance(items, str):
                    elements.append(items)
                elif isinstance(items, list):
                    elements.extend(items)

    if not elements:
        return ["No description available"]

    return elements
