import json
from typing import Any

from sqlalchemy import Enum
from sqlalchemy import func
from sqlalchemy.orm import validates

from website.web.bootstrap import db, vulnerabilitylookup


class Notification(db.Model):  # type: ignore[name-defined, misc]
    """Represent a vulnerability notication for a user."""

    id = db.Column(db.Integer, primary_key=True)
    notification_type = db.Column(db.String(), default="vulnerability_cpe")

    # Used when notification_type is vulnerability_cpe
    vendor = db.Column(db.String(), default="")
    product = db.Column(db.String(), default="")

    # Used when notification_type is vulnerability_organization
    organization_id = db.Column(
        db.Integer(), db.ForeignKey("organization.id"), nullable=True
    )
    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"), nullable=True)

    creation_timestamp = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    timestamp = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    frequency = db.Column(
        Enum("hourly", "daily", "weekly", name="frequency_type"),
        nullable=False,
        default="daily",
    )
    hits = db.Column(db.Integer(), default=0)
    last_execution_time = db.Column(db.DateTime(), nullable=True)
    is_active = db.Column(db.Boolean(), default=True)

    # foreign keys
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable=False)

    @validates("vendor")
    def validates_vendor(self, key: str, value: str) -> str:
        if self.notification_type == "vulnerability_cpe":
            assert value in vulnerabilitylookup.get_vendors(), AssertionError(
                "Unknown vendor."
            )
        return value

    @validates("frequency")
    def validates_frequency(self, key: str, value: str) -> str:
        assert value in [
            "hourly",
            "daily",
            "weekly",
        ], AssertionError("Unsupported frequency.")
        return value

    def as_json(self) -> str:
        return json.dumps(
            {
                "id": str(self.id),
                "vendor": self.vendor,
                "product": self.product,
                "frequency": self.frequency,
                "hits": str(self.hits),
                "creation_timestamp": self.creation_timestamp.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "timestamp": self.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "last_execution_time": self.last_execution_time.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "is_active": str(self.is_active),
                "user": str(self.user.uuid),
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return json.loads(self.as_json())
