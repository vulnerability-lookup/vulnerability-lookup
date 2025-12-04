from typing import Any, Dict


def extract_credits(vuln: Dict[str, Any]) -> list[Dict[str, Any]]:
    """
    Extract credits from OSSF Malicious Packages sources.
    Normalize into a list of dicts with 'type', 'value', and 'contacts' keys.
    """
    credits_out = []

    for credit in vuln.get("credits", []):
        # Normalize type
        credit_type = credit.get("type", "REPORTER").lower()
        if credit_type == "reporter":
            credit_type = "finder"
        elif credit_type == "developer":
            credit_type = "remediation developer"

        name = credit.get("name", "")
        contacts = credit.get("contact", [])

        credits_out.append({"type": credit_type, "value": name, "contacts": contacts})

    return credits_out
