"""SQLAlchemy engine, session factory, and Base declarative class."""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# For SQLite, need check_same_thread=False for FastAPI's async usage.
# For PostgreSQL, these connect_args are not needed.
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

# Enable WAL mode and foreign keys for SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _add_missing_columns():
    """Eski bazalarga yangi ustunlarni qo'shadi (oddiy avto-migratsiya).

    create_all() mavjud jadvalga yangi ustun qo'shmaydi. Shuning uchun
    modelda bor, lekin bazada yo'q ustunlar ALTER TABLE orqali qo'shiladi.
    """
    from sqlalchemy import inspect, text

    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                continue
            have = {c["name"] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name in have:
                    continue
                col_type = col.type.compile(dialect=engine.dialect)
                default_sql = ""
                d = col.default.arg if col.default is not None and not callable(col.default.arg) else None
                if isinstance(d, bool):
                    default_sql = f" DEFAULT {int(d)}"
                elif isinstance(d, (int, float)):
                    default_sql = f" DEFAULT {d}"
                elif isinstance(d, str):
                    default_sql = " DEFAULT '" + d.replace("'", "''") + "'"
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col_type}{default_sql}'))
                print(f"[MIGRATION] {table.name}.{col.name} qo'shildi")


def create_tables():
    """Create all tables. Called once on application startup."""
    import app.models  # noqa: F401 — ensure all models are imported
    Base.metadata.create_all(bind=engine)
    _add_missing_columns()
