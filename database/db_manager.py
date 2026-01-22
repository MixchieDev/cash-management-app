"""
Database manager for JESUS Company Cash Management System.
Handles database connections, session management, and schema initialization.
"""
from typing import Optional, Generator
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from config.settings import DATABASE_URL, DATABASE_DIR
from database.models import Base


class DatabaseManager:
    """Manage database connections and sessions."""

    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize database manager.

        Args:
            db_url: Database URL (defaults to settings.DATABASE_URL)
        """
        self.db_url = db_url or DATABASE_URL

        # Configure engine based on database type
        if self.db_url.startswith('sqlite'):
            # SQLite-specific configuration
            self.engine = create_engine(
                self.db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False  # Set to True for SQL debugging
            )
        else:
            # PostgreSQL or other databases
            self.engine = create_engine(
                self.db_url,
                pool_size=5,
                max_overflow=10,
                echo=False
            )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy session

        Usage:
            session = db.get_session()
            try:
                # Do database operations
                session.commit()
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
        """
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope for database operations.

        Yields:
            SQLAlchemy session

        Usage:
            with db.session_scope() as session:
                # Do database operations
                # Automatically commits on success, rolls back on error
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def init_schema(self) -> None:
        """
        Initialize database schema.
        Creates all tables from SQLAlchemy models.
        """
        # Create all tables from models
        Base.metadata.create_all(bind=self.engine)

        print("✓ Database schema initialized successfully")

    def init_schema_from_sql(self) -> None:
        """
        Initialize database schema from SQL file.
        Alternative to init_schema() for precise schema control.
        """
        sql_file = Path(__file__).parent / 'migrations' / 'init_schema.sql'

        if not sql_file.exists():
            raise FileNotFoundError(f"Schema file not found: {sql_file}")

        with open(sql_file, 'r') as f:
            schema_sql = f.read()

        # Execute schema SQL
        with self.engine.connect() as conn:
            # Split by semicolons and execute each statement
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            for stmt in statements:
                conn.execute(text(stmt))
            conn.commit()

        print(f"✓ Database schema initialized from {sql_file}")

    def drop_all_tables(self) -> None:
        """
        Drop all tables (DANGEROUS - use only in development/testing).
        """
        Base.metadata.drop_all(bind=self.engine)
        print("⚠ All tables dropped")

    def reset_database(self) -> None:
        """
        Reset database (drop all tables and recreate schema).
        DANGEROUS - use only in development/testing.
        """
        self.drop_all_tables()
        self.init_schema()
        print("✓ Database reset complete")

    def get_table_names(self) -> list:
        """
        Get list of all table names in database.

        Returns:
            List of table names
        """
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        return inspector.get_table_names()

    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.

        Args:
            table_name: Name of table to check

        Returns:
            True if table exists, False otherwise
        """
        return table_name in self.get_table_names()

    def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> list:
        """
        Execute raw SQL query.

        Args:
            sql: SQL query string
            params: Query parameters (optional)

        Returns:
            List of result rows
        """
        with self.engine.connect() as conn:
            result = conn.execute(text(sql), params or {})
            return list(result)


# Global database instance
print(f"[DB] Initializing database with URL: {DATABASE_URL}")
db_manager = DatabaseManager()

# Auto-initialize schema if tables don't exist (needed for Streamlit Cloud /tmp database)
if not db_manager.table_exists('customer_contracts'):
    print("[DB] Tables don't exist, initializing schema...")
    db_manager.init_schema()
else:
    print("[DB] Tables already exist")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions.
    Use with FastAPI or similar frameworks.

    Yields:
        Database session
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()
