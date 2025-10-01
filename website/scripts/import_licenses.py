#! /usr/bin/python
import json

import requests

from website.web.bootstrap import db
from website.models import License


def import_osi_approved_licenses() -> None:
    r = requests.get("https://spdx.org/licenses/licenses.json", timeout=10)
    if r.status_code == 200:
        result = json.loads(r.content)
        try:
            db.session.bulk_save_objects(
                [
                    License(name=license["name"], license_id=license["licenseId"])
                    for license in result["licenses"]
                    if license["isOsiApproved"] and not license["isDeprecatedLicenseId"]
                ]
            )
            db.session.commit()
        except Exception:
            pass
