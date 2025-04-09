import re
import uuid
from typing import Any

import bleach  # type: ignore[import-untyped]
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import validates

from website.web.bootstrap import db


class CommentDisclosure(db.Model):  # type: ignore[name-defined, misc]
    """Represent a comment related to a vulnerability disclosure."""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(UUID(as_uuid=True), unique=True, default=lambda: uuid.uuid4())
    vulnerability_lookup_origin = db.Column(UUID(as_uuid=True), nullable=False)
    description = db.Column(db.String(), nullable=False)
    description_format = db.Column(db.String(), default="text", nullable=False)
    creation_timestamp = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_timestamp = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # foreign keys
    author_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable=False)
    vulnerability_disclosure_id = db.Column(
        db.Integer(),
        db.ForeignKey("vulnerability_disclosure.id", ondelete="CASCADE"),
        nullable=False,
    )

    @validates("description")
    def validates_description(self, key: str, value: str) -> str:
        assert 0 <= len(value) <= 5000, AssertionError("Maximum length for bio: 5000")
        value = value.strip()

        # Remove Markdown images: ![alt](url)
        value = re.sub(r"!\[.*?\]\s*\(.*?\)", "", value, flags=re.DOTALL)

        # Remove Markdown links to external sites
        value = re.sub(
            r"\[.*?\]\s*\(\s*https?://[^\s)]+?\s*\)",
            "",
            value,
            flags=re.DOTALL | re.IGNORECASE,
        )

        # Sanitize the bio using bleach
        allowed_tags = ["b", "i", "u", "em", "strong", "a"]
        allowed_attributes = {"a": ["href", "title"]}
        value = bleach.clean(
            value, tags=allowed_tags, attributes=allowed_attributes, strip=True
        )

        return value

    @validates("description_format")
    def validates_description_format(self, key: str, value: str) -> str:
        assert value.lower() in ["markdown", "text"], AssertionError(
            "value must be 'markdown' or 'text'."
        )
        return value.lower()

    def __repr__(self) -> str:
        return f"<CommentDisclosure uuid={self.uuid}>"

    def to_dict(self) -> dict[str, Any]:
        return {
            "uuid": str(self.uuid),
            "vulnerability_lookup_origin": str(self.vulnerability_lookup_origin),
            "author": str(self.author.uuid),
            "description": self.description,
            "description_format": self.description_format,
            "creation_timestamp": self.creation_timestamp.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "updated_timestamp": self.updated_timestamp.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
        }
