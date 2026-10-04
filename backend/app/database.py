import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(DATABASE_DIR, "raven.db")
# SQLite by default; set DATABASE_URL (e.g. postgresql+psycopg://user:pass@host/db) for Postgres
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 60} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    """create_all() skips indexes on tables that already exist, so add any missing ones."""
    from . import models  # noqa: F401  (registers the tables on Base.metadata)
    Base.metadata.create_all(bind=engine)
    _add_missing_columns()
    _add_search_indexes()
    for table in Base.metadata.sorted_tables:
        for index in table.indexes:
            index.create(bind=engine, checkfirst=True)


def _add_missing_columns():
    """Additive migration: add nullable columns that exist on a model but not yet in the database."""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name not in existing and column.nullable:
                    col_type = column.type.compile(dialect=engine.dialect)
                    conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN {column.name} {col_type}'))


# Columns searched with ILIKE '%term%'. On Postgres a trigram index makes those searches use an index.
_TRGM_COLUMNS = [
    ("parliament_questions", "title"),
    ("candidates", "name"),
    ("ngos", "name"),
    ("donors", "name"),
]


def _add_search_indexes():
    if engine.dialect.name != "postgresql":
        return
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        for table, column in _TRGM_COLUMNS:
            conn.execute(text(
                f"CREATE INDEX IF NOT EXISTS ix_{table}_{column}_trgm ON {table} USING gin ({column} gin_trgm_ops)"
            ))
