import pytest

import website.models  # Import all models to ensure they're registered with SQLAlchemy
from website.models import db_create
from website.web.bootstrap import application
from website.web.bootstrap import db as _db


@pytest.fixture(scope="session")
def app(request):  # type: ignore[no-untyped-def]
    """Session-wide test `Flask` application."""
    app = application

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    def teardown() -> None:
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope="session")
def db(app, request):  # type: ignore[no-untyped-def]
    """Session-wide test database."""

    def teardown() -> None:
        _db.drop_all()

    _db.app = app  # type: ignore[attr-defined]
    # _db.init_app(_db.app)
    try:
        # create the database for the tests
        db_create(
            _db,
            app.config["DB_CONFIG_DICT"],
            app.config["DATABASE_NAME"],
        )
    except Exception:
        # in case it already exists
        pass
    # initialize the database
    _db.create_all()

    # Verify KEV tables were created
    from sqlalchemy import inspect
    inspector = inspect(_db.engine)
    tables = inspector.get_table_names()
    print(f"Created tables: {tables}")
    assert "kev_entry" in tables, f"kev_entry table not created! Available tables: {tables}"
    assert "kev_evidence" in tables, f"kev_evidence table not created! Available tables: {tables}"

    request.addfinalizer(teardown)
    return _db


@pytest.fixture(scope="function")
def session(db, request):  # type: ignore[no-untyped-def]
    """Creates a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db._make_scoped_session(options=options)

    db.session = session

    def teardown() -> None:
        transaction.rollback()
        connection.close()
        session.remove()

    request.addfinalizer(teardown)
    return session
