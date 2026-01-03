#!/usr/bin/env python3
"""
Migration Script: Split "Both" Vendors into Separate Entity Entries

This script migrates all vendor contracts with entity='Both' into separate
YAHSHUA and ABBA entries, using the current split ratios from config.

IMPORTANT: Backup database before running!

Usage:
    python scripts/migrate_both_vendors.py         # Interactive mode with prompts
    python scripts/migrate_both_vendors.py --yes   # Auto-confirm (skip prompts)
"""
from datetime import date
from decimal import Decimal
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db_manager import db_manager
from database.models import VendorContract

# Historical split ratio (before removal of VENDOR_BOTH_SPLIT)
VENDOR_BOTH_SPLIT = {
    'YAHSHUA': Decimal('0.5'),
    'ABBA': Decimal('0.5')
}


def backup_database(auto_confirm: bool = False):
    """
    Remind user to backup database before migration.

    Args:
        auto_confirm: If True, skip prompts and proceed automatically
    """
    print("\n" + "=" * 70)
    print("⚠️  DATABASE MIGRATION - BACKUP REQUIRED")
    print("=" * 70)
    print("\nThis script will modify vendor data by:")
    print("  1. Finding all vendors with entity='Both'")
    print("  2. Creating separate YAHSHUA and ABBA vendor entries")
    print("  3. Deleting the original 'Both' vendors")
    print("\n⚠️  IMPORTANT: Backup your database before proceeding!")
    print("\nTo backup:")
    print("  cp database/jesus_cash_management.db database/jesus_cash_management.db.backup")
    print("\n" + "=" * 70)

    if auto_confirm:
        print("\n✅ Auto-confirm mode: Proceeding with migration...\n")
        return

    response = input("\nHave you backed up the database? (yes/no): ").strip().lower()
    if response != 'yes':
        print("\n❌ Migration cancelled. Please backup database first.")
        sys.exit(1)

    print("\n✅ Proceeding with migration...\n")


def find_both_vendors():
    """
    Find all vendors with entity='Both'.

    Returns:
        List of VendorContract objects with entity='Both'
    """
    with db_manager.session_scope() as session:
        both_vendors = session.query(VendorContract)\
            .filter(VendorContract.entity == 'Both')\
            .all()

        # Detach from session so we can use outside context
        session.expunge_all()
        return both_vendors


def split_vendor(vendor: VendorContract, session) -> tuple:
    """
    Split a "Both" vendor into YAHSHUA and ABBA entries.

    Args:
        vendor: VendorContract with entity='Both'
        session: SQLAlchemy session

    Returns:
        Tuple of (yahshua_vendor, abba_vendor)
    """
    # Calculate split amounts
    yahshua_ratio = VENDOR_BOTH_SPLIT.get('YAHSHUA', Decimal('0.5'))
    abba_ratio = VENDOR_BOTH_SPLIT.get('ABBA', Decimal('0.5'))

    yahshua_amount = vendor.amount * yahshua_ratio
    abba_amount = vendor.amount * abba_ratio

    # Create YAHSHUA vendor
    yahshua_vendor = VendorContract(
        vendor_name=f"{vendor.vendor_name} - YAHSHUA",
        category=vendor.category,
        amount=yahshua_amount,
        frequency=vendor.frequency,
        due_date=vendor.due_date,
        entity='YAHSHUA',
        priority=vendor.priority,
        flexibility_days=vendor.flexibility_days,
        status=vendor.status,
        notes=f"Split from shared vendor '{vendor.vendor_name}' ({yahshua_ratio * 100}% share)"
    )

    # Create ABBA vendor
    abba_vendor = VendorContract(
        vendor_name=f"{vendor.vendor_name} - ABBA",
        category=vendor.category,
        amount=abba_amount,
        frequency=vendor.frequency,
        due_date=vendor.due_date,
        entity='ABBA',
        priority=vendor.priority,
        flexibility_days=vendor.flexibility_days,
        status=vendor.status,
        notes=f"Split from shared vendor '{vendor.vendor_name}' ({abba_ratio * 100}% share)"
    )

    return yahshua_vendor, abba_vendor


def migrate_both_vendors(auto_confirm: bool = False):
    """
    Main migration function.

    Args:
        auto_confirm: If True, skip prompts and proceed automatically

    Finds all "Both" vendors and splits them into separate entity entries.
    """
    print("\n📋 MIGRATION SUMMARY")
    print("=" * 70)

    # Find all "Both" vendors
    both_vendors = find_both_vendors()

    if not both_vendors:
        print("✅ No vendors with entity='Both' found. Migration not needed.")
        return

    print(f"\nFound {len(both_vendors)} vendor(s) with entity='Both':\n")

    for vendor in both_vendors:
        print(f"  • {vendor.vendor_name:30} | ₱{vendor.amount:>12,.2f} | {vendor.frequency}")

    print("\n" + "=" * 70)

    if not auto_confirm:
        response = input(f"\nProceed with splitting {len(both_vendors)} vendor(s)? (yes/no): ").strip().lower()
        if response != 'yes':
            print("\n❌ Migration cancelled.")
            return

    print("\n🔄 Starting migration...\n")
    print("-" * 70)

    # Perform migration
    with db_manager.session_scope() as session:
        migrated_count = 0

        for vendor in both_vendors:
            # Merge vendor into current session (since it was detached)
            vendor = session.merge(vendor)

            # Split into YAHSHUA and ABBA
            yahshua_vendor, abba_vendor = split_vendor(vendor, session)

            # Add new vendors
            session.add(yahshua_vendor)
            session.add(abba_vendor)

            print(f"✅ Migrated: {vendor.vendor_name}")
            print(f"   → YAHSHUA: {yahshua_vendor.vendor_name} | ₱{yahshua_vendor.amount:,.2f}")
            print(f"   → ABBA:    {abba_vendor.vendor_name} | ₱{abba_vendor.amount:,.2f}")

            # Delete original "Both" vendor
            session.delete(vendor)
            print(f"   🗑️  Deleted original 'Both' vendor\n")

            migrated_count += 1

        # Commit all changes
        session.commit()
        print("-" * 70)
        print(f"\n✅ Migration complete! Migrated {migrated_count} vendor(s).")

    # Verify migration
    verify_migration()


def verify_migration():
    """
    Verify that no "Both" vendors remain after migration.
    """
    print("\n🔍 Verifying migration...\n")

    both_vendors = find_both_vendors()

    if both_vendors:
        print(f"⚠️  WARNING: {len(both_vendors)} vendor(s) still have entity='Both'")
        for vendor in both_vendors:
            print(f"   • {vendor.vendor_name}")
    else:
        print("✅ Verification successful: No 'Both' vendors remaining")

    # Count total vendors by entity
    with db_manager.session_scope() as session:
        yahshua_count = session.query(VendorContract)\
            .filter(VendorContract.entity == 'YAHSHUA')\
            .count()
        abba_count = session.query(VendorContract)\
            .filter(VendorContract.entity == 'ABBA')\
            .count()

    print(f"\n📊 Vendor Count by Entity:")
    print(f"   YAHSHUA: {yahshua_count}")
    print(f"   ABBA:    {abba_count}")
    print(f"   Total:   {yahshua_count + abba_count}")


def main():
    """Run migration."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Migrate 'Both' vendors into separate entity-specific entries"
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help="Auto-confirm all prompts (skip user input)"
    )
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("VENDOR 'BOTH' ENTITY MIGRATION SCRIPT")
    print("=" * 70)

    # Initialize database
    db_manager.init_schema()

    # Remind user to backup
    backup_database(auto_confirm=args.yes)

    # Run migration
    migrate_both_vendors(auto_confirm=args.yes)

    print("\n" + "=" * 70)
    print("✅ MIGRATION COMPLETE")
    print("=" * 70)
    print("\n📝 Next Steps:")
    print("   1. Update database model to remove 'Both' constraint")
    print("   2. Remove VENDOR_BOTH_SPLIT from config/constants.py")
    print("   3. Remove split logic from projection_engine/cash_projector.py")
    print("   4. Remove split logic from database/queries.py")
    print("   5. Update test data script")
    print("   6. Test projections to verify correctness")
    print()


if __name__ == '__main__':
    main()
