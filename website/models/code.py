from sqlalchemy import func

from website.web.bootstrap import db


class Code(db.Model):  # type: ignore[name-defined, misc]
    """Represent a source code of a product."""

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code_type = db.Column(db.Enum("purl", "scm", name="code_type_enum"), nullable=False)
    purl = db.Column(db.Text, nullable=True, unique=True)
    url = db.Column(db.Text, nullable=True, unique=True)
    scm_type = db.Column(
        db.Enum("git", "mercurial", "svn", "bazaar", name="scm_type_enum"),
        nullable=True,
    )
    branch = db.Column(db.String(255), nullable=True)
    commit_hash = db.Column(db.String(64), nullable=True)
    tag = db.Column(db.String(255), nullable=True)
    creation_timestamp = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    timestamp = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # foreign keys
    product_id = db.Column(db.Integer(), db.ForeignKey("product.id"), default=None)
