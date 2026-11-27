from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///arriendo_deportivo.db"

engine = create_engine(DATABASE_URL, echo=False)


@event.listens_for(engine, "connect")
def _activar_foreign_keys(dbapi_connection, connection_record):
    """Activa las restricciones de llave foránea en cada conexión SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)
Base = declarative_base()


def init_db():
    """Importa los modelos y crea las tablas en SQLite si no existen."""
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)