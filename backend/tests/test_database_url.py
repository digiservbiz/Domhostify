from backend.app.database import normalize_database_url


def test_normalizes_render_style_postgres_url():
    assert normalize_database_url("postgres://user:pass@host:5432/db") == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )


def test_normalizes_standard_postgresql_url():
    assert normalize_database_url("postgresql://user:pass@host:5432/db") == (
        "postgresql+psycopg://user:pass@host:5432/db"
    )


def test_preserves_sqlite_url():
    assert normalize_database_url("sqlite:///./domhostify.db") == "sqlite:///./domhostify.db"
