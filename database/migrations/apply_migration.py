"""
Apply database migrations for JESUS Company Cash Management System.

Usage:
    python database/migrations/apply_migration.py 001_add_vendor_start_date.sql
"""
import sys
import sqlite3
from pathlib import Path
from datetime import datetime


def apply_migration(migration_file: str, db_path: str = None) -> None:
    """
    Apply a SQL migration file to the database.

    Args:
        migration_file: Path to the migration SQL file
        db_path: Path to the database file (default: database/jesus_cash_management.db)
    """
    # Determine database path
    if db_path is None:
        project_root = Path(__file__).parent.parent.parent
        db_path = project_root / "database" / "jesus_cash_management.db"
    else:
        db_path = Path(db_path)

    # Read migration file
    migration_path = Path(__file__).parent / migration_file
    if not migration_path.exists():
        raise FileNotFoundError(f"Migration file not found: {migration_path}")

    print(f"\n{'=' * 70}")
    print(f"APPLYING DATABASE MIGRATION")
    print(f"{'=' * 70}\n")
    print(f"Migration: {migration_file}")
    print(f"Database: {db_path}")
    print()

    with open(migration_path, 'r') as f:
        migration_sql = f.read()

    # Backup database before migration
    backup_path = db_path.parent / f"{db_path.name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup: {backup_path.name}")

    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created\n")

    # Apply migration
    print("Applying migration...")
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Execute migration SQL
        cursor.executescript(migration_sql)
        conn.commit()

        print(f"✓ Migration applied successfully\n")

        # Verify schema version
        cursor.execute("SELECT value FROM system_metadata WHERE key = 'schema_version'")
        version = cursor.fetchone()
        if version:
            print(f"Schema version: {version[0]}\n")

        conn.close()

        print(f"{'=' * 70}")
        print(f"MIGRATION COMPLETE")
        print(f"{'=' * 70}\n")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}\n")
        print(f"Restoring backup...")
        shutil.copy2(backup_path, db_path)
        print(f"✓ Database restored from backup\n")
        raise


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\nUsage: python database/migrations/apply_migration.py <migration_file.sql>\n")
        print("Available migrations:")
        migrations_dir = Path(__file__).parent
        for migration in sorted(migrations_dir.glob("*.sql")):
            if migration.name != "init_schema.sql":
                print(f"  - {migration.name}")
        print()
        sys.exit(1)

    migration_file = sys.argv[1]
    apply_migration(migration_file)
