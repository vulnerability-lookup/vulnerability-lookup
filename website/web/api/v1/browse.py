import logging

from flask import request
from flask_restx import (  # type: ignore[import-untyped]
    Namespace,
    Resource,
)

from website.web.bootstrap import vulnerabilitylookup

logger = logging.getLogger(__name__)

browse_ns = Namespace(
    "browse", description="Endpoints for accessing vendor and product information."
)


@browse_ns.route("/")
@browse_ns.doc(description="Get the known vendors.")
class Vendors(Resource):  # type: ignore[misc]
    def get(self) -> list[str]:
        """Get the known vendors."""
        vendor = request.args.get("vendor", "").lower()
        vendors = list(vulnerabilitylookup.get_vendors())
        if vendor and len(vendor) >= 3:
            vendors = [elem for elem in vendors if vendor in elem]
        return vendors


@browse_ns.route("/<string:vendor>")
@browse_ns.doc(description="Get the known products for a vendor.")
class VendorProducts(Resource):  # type: ignore[misc]
    def get(self, vendor: str) -> list[str]:
        """Get the known products for a vendor."""
        return list(vulnerabilitylookup.get_vendor_products(vendor))
