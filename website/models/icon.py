from website.web.bootstrap import db


class Icon(db.Model):  # type: ignore[name-defined, misc]
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    url = db.Column(db.String(), nullable=True, default=None)
    content = db.Column(db.String(), nullable=True, default=None)
    mimetype = db.Column(db.String(), default="image/png")
