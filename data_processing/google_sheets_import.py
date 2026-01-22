"""
Google Sheets import module for JESUS Company Cash Management System.
Imports customer contracts, vendor contracts, and bank balances from Google Sheets.

USES PUBLIC CSV EXPORT - NO CREDENTIALS REQUIRED!
Google Sheets must be shared as "Anyone with the link can view"

Sheet names and URL are configurable from Settings page in dashboard.
"""
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal
from urllib.parse import quote

from config.entity_mapping import assign_entity
from database.db_manager import db_manager
from database.models import CustomerContract, VendorContract, BankBalance, SystemMetadata


def _get_sheets_config() -> Tuple[str, str, str, str]:
    """
    Get Google Sheets configuration from database with fallback to defaults.

    Returns:
        Tuple of (spreadsheet_id, customers_sheet, vendors_sheet, bank_balances_sheet)
    """
    try:
        from database.settings_manager import get_google_sheets_config, extract_spreadsheet_id
        config = get_google_sheets_config()
        spreadsheet_id = extract_spreadsheet_id(config['url'])
        return (
            spreadsheet_id,
            config['customers_sheet'],
            config['vendors_sheet'],
            config['bank_balances_sheet']
        )
    except Exception:
        # Fallback to original config files
        from config.settings import SPREADSHEET_ID
        from config.google_sheets_config import (
            CUSTOMER_CONTRACTS_SHEET,
            VENDOR_CONTRACTS_SHEET,
            BANK_BALANCES_SHEET
        )
        return (
            SPREADSHEET_ID,
            CUSTOMER_CONTRACTS_SHEET,
            VENDOR_CONTRACTS_SHEET,
            BANK_BALANCES_SHEET
        )


def get_sheet_csv_url(sheet_name: str, spreadsheet_id: Optional[str] = None) -> str:
    """
    Generate CSV export URL for a Google Sheets tab.

    Args:
        sheet_name: Name of the sheet tab
        spreadsheet_id: Optional spreadsheet ID (uses database config if not provided)

    Returns:
        CSV export URL

    Example:
        >>> get_sheet_csv_url("Customer Contracts")
        'https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/gviz/tq?tqx=out:csv&sheet=Customer%20Contracts'
    """
    if spreadsheet_id is None:
        spreadsheet_id, _, _, _ = _get_sheets_config()

    # URL encode the sheet name (spaces become %20)
    encoded_sheet_name = quote(sheet_name)
    return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_sheet_name}"


def read_sheet_as_dataframe(sheet_name: str) -> pd.DataFrame:
    """
    Read a Google Sheets tab as a pandas DataFrame.

    Uses public CSV export - NO AUTHENTICATION REQUIRED!
    Sheet must be shared as "Anyone with the link can view"

    Args:
        sheet_name: Name of the sheet tab

    Returns:
        DataFrame with sheet data

    Raises:
        Exception: If sheet cannot be accessed (not public or wrong name)
    """
    csv_url = get_sheet_csv_url(sheet_name)

    try:
        # Read CSV directly from URL - no credentials needed!
        df = pd.read_csv(csv_url)

        # Strip whitespace from column names (Google Sheets often has trailing spaces)
        df.columns = df.columns.str.strip()

        return df
    except Exception as e:
        raise Exception(
            f"Failed to read sheet '{sheet_name}' from Google Sheets.\n"
            f"Possible causes:\n"
            f"1. Sheet is not public (share as 'Anyone with the link can view')\n"
            f"2. Sheet tab name is incorrect (check spelling and capitalization)\n"
            f"3. Spreadsheet ID is wrong\n"
            f"4. Network connection issue\n"
            f"Error: {e}"
        )


def parse_date(date_str: str) -> Optional[date]:
    """
    Parse date string in various formats.

    Args:
        date_str: Date string from Google Sheets

    Returns:
        datetime.date object or None if empty

    Raises:
        ValueError: If date format is invalid
    """
    if not date_str or str(date_str).strip() == '':
        return None

    date_str = str(date_str).strip()

    # Try common date formats
    formats = [
        '%Y-%m-%d',  # 2026-01-15
        '%m/%d/%Y',  # 01/15/2026
        '%d/%m/%Y',  # 15/01/2026
        '%Y/%m/%d',  # 2026/01/15
        '%m-%d-%Y',  # 01-15-2026
        '%d-%m-%Y',  # 15-01-2026
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    raise ValueError(f"Invalid date format: '{date_str}'. Expected formats: YYYY-MM-DD, MM/DD/YYYY, etc.")


def parse_decimal(value: str) -> Decimal:
    """
    Parse decimal value from Google Sheets.

    Args:
        value: String value from Google Sheets

    Returns:
        Decimal value

    Raises:
        ValueError: If value cannot be parsed
    """
    if not value or str(value).strip() == '':
        return Decimal('0.00')

    # Remove currency symbols, commas, and spaces
    cleaned = str(value).replace('₱', '').replace(',', '').replace(' ', '').strip()

    try:
        return Decimal(cleaned).quantize(Decimal('0.01'))
    except Exception as e:
        raise ValueError(f"Invalid decimal value: '{value}'. Error: {e}")


def import_customer_contracts(save_to_db: bool = True) -> List[Dict]:
    """
    Import customer contracts from Google Sheets using public CSV export.

    NO CREDENTIALS REQUIRED - uses public CSV export URL.
    Sheet names are configurable from Settings page.

    Args:
        save_to_db: If True, save to database (default: True)

    Returns:
        List of customer contract dictionaries

    Raises:
        ValueError: If validation fails
    """
    print("Importing customer contracts from Google Sheets...")

    # Get sheet name from database config
    _, customers_sheet, _, _ = _get_sheets_config()

    # Read sheet as DataFrame (no authentication needed!)
    df = read_sheet_as_dataframe(customers_sheet)

    if df.empty:
        print("⚠ No customer contracts found in Google Sheets")
        return []

    customers = []
    skipped_inactive = 0
    skipped_errors = 0

    for idx, row in df.iterrows():
        try:
            # Skip empty rows
            if pd.isna(row.get('Company Name')) or str(row.get('Company Name', '')).strip() == '':
                continue

            # Check client status - ONLY import Active customers
            client_status = str(row.get('Client Status', '')).strip()
            if client_status != 'Active':
                skipped_inactive += 1
                print(f"  Skipping row {idx + 2}: Client Status = '{client_status}' (not Active)")
                continue

            # Validate required fields
            required_fields = ['Company Name', 'Monthly Fee', 'Payment Plan', 'Contract Start', 'Who acquired the client']
            for field in required_fields:
                if pd.isna(row.get(field)) or str(row.get(field, '')).strip() == '':
                    raise ValueError(f"Missing required field '{field}' in row {idx + 2}")

            # Assign entity based on acquisition source
            entity = assign_entity(str(row['Who acquired the client']).strip())

            # Parse data
            customer = {
                'company_name': str(row['Company Name']).strip(),
                'monthly_fee': parse_decimal(str(row['Monthly Fee'])),
                'payment_plan': str(row['Payment Plan']).strip(),
                'contract_start': parse_date(str(row['Contract Start'])),
                'contract_end': parse_date(str(row.get('Contract End', ''))) if not pd.isna(row.get('Contract End')) else None,
                'status': client_status,
                'who_acquired': str(row['Who acquired the client']).strip(),
                'entity': entity,
                'invoice_day': int(row.get('Invoice Day')) if not pd.isna(row.get('Invoice Day')) and row.get('Invoice Day') != '' else None,  # None = use global setting
                'payment_terms_days': int(row.get('Payment Terms Days')) if not pd.isna(row.get('Payment Terms Days')) and row.get('Payment Terms Days') != '' else None,  # None = use global setting
                'reliability_score': Decimal(str(row.get('Reliability Score', 0.80))) if not pd.isna(row.get('Reliability Score')) else Decimal('0.80'),
                'notes': str(row.get('Notes', '')).strip() if not pd.isna(row.get('Notes')) else None
            }

            customers.append(customer)

        except Exception as e:
            skipped_errors += 1
            print(f"⚠ Error processing row {idx + 2}: {e}")
            continue  # Skip this row but continue processing

    print(f"✓ Parsed {len(customers)} ACTIVE customer contracts")
    if skipped_inactive > 0:
        print(f"  Skipped {skipped_inactive} inactive customers")
    if skipped_errors > 0:
        print(f"  Skipped {skipped_errors} rows with errors")

    # Save to database
    if save_to_db:
        with db_manager.session_scope() as session:
            # Clear existing contracts
            session.query(CustomerContract).delete()

            # Insert new contracts
            for customer_data in customers:
                customer = CustomerContract(**customer_data)
                session.add(customer)

        print(f"✓ Saved {len(customers)} customer contracts to database")

    return customers


def import_vendor_contracts(save_to_db: bool = True) -> List[Dict]:
    """
    Import vendor contracts from Google Sheets using public CSV export.

    NO CREDENTIALS REQUIRED - uses public CSV export URL.
    Sheet names are configurable from Settings page.

    Args:
        save_to_db: If True, save to database (default: True)

    Returns:
        List of vendor contract dictionaries

    Raises:
        ValueError: If validation fails
    """
    print("Importing vendor contracts from Google Sheets...")

    # Get sheet name from database config
    _, _, vendors_sheet, _ = _get_sheets_config()

    # Read sheet as DataFrame (no authentication needed!)
    df = read_sheet_as_dataframe(vendors_sheet)

    if df.empty:
        print("⚠ No vendor contracts found in Google Sheets")
        return []

    vendors = []
    skipped_errors = 0

    for idx, row in df.iterrows():
        try:
            # Skip empty rows
            if pd.isna(row.get('Vendor Name')) or str(row.get('Vendor Name', '')).strip() == '':
                continue

            # Validate required fields
            required_fields = ['Vendor Name', 'Category', 'Amount', 'Frequency', 'Due Date', 'Entity']
            for field in required_fields:
                if pd.isna(row.get(field)) or str(row.get(field, '')).strip() == '':
                    raise ValueError(f"Missing required field '{field}' in row {idx + 2}")

            # Parse due_date - handle both day of month (integer) and full dates
            due_date_value = row['Due Date']
            if isinstance(due_date_value, (int, float)):
                # If it's a day number, create a date for current month
                from datetime import date
                today = date.today()
                day = int(due_date_value)
                due_date_obj = date(today.year, today.month, day)
            else:
                # If it's a date string, parse it
                due_date_obj = parse_date(str(due_date_value))

            # Parse start_date (optional field)
            # If empty/null, vendor is already active (no start date restriction)
            # If specified, vendor expense only appears in projections from this date onwards
            start_date_value = row.get('Start Date')
            if not pd.isna(start_date_value) and str(start_date_value).strip():
                start_date_obj = parse_date(str(start_date_value))
            else:
                # No start date = vendor is already active (use None)
                start_date_obj = None

            # Parse end_date (optional field)
            # If empty/null, vendor expense continues indefinitely
            # If specified, vendor expense stops after this date
            end_date_value = row.get('End Date')
            if not pd.isna(end_date_value) and str(end_date_value).strip():
                end_date_obj = parse_date(str(end_date_value))
            else:
                # No end date = vendor expense continues indefinitely
                end_date_obj = None

            # Parse frequency and convert to title case (database constraint requirement)
            # Google Sheets may have "MONTHLY", "QUARTERLY" etc - convert to "Monthly", "Quarterly"
            frequency_value = str(row['Frequency']).strip().title()

            # Handle special cases for frequency to match database constraints
            # Valid: One-time, Daily, Weekly, Bi-weekly, Monthly, Quarterly, Annual
            if frequency_value == 'Bi-Weekly':
                frequency_value = 'Bi-weekly'
            elif frequency_value == 'One-Time':
                frequency_value = 'One-time'
            elif frequency_value == 'Annually':
                frequency_value = 'Annual'
            elif frequency_value in ['As Needed', 'As-Needed']:
                # "As Needed" is not a valid frequency - map to "Monthly" as default
                frequency_value = 'Monthly'
                print(f"  Note: Converting 'As Needed' frequency to 'Monthly' for {row['Vendor Name']}")

            # Handle entity - may be "YOWI" or "Both" in sheets, need "YAHSHUA" or "ABBA" or "Both"
            entity_value = str(row['Entity']).strip()
            if entity_value == 'YOWI':
                entity_value = 'YAHSHUA'
            elif entity_value == 'TAI':
                entity_value = 'ABBA'

            # Handle category - map variations to valid categories
            # Valid: Payroll, Loans, Software/Tech, Operations, Rent, Utilities
            category_value = str(row['Category']).strip()
            category_mapping = {
                'Deliver Services': 'Operations',
                'Delivery Services': 'Operations',
                'Software': 'Software/Tech',
                'Tech': 'Software/Tech',
                'Software & Tech': 'Software/Tech',
            }
            if category_value in category_mapping:
                category_value = category_mapping[category_value]
                print(f"  Note: Mapping category '{row['Category']}' to '{category_value}' for {row['Vendor Name']}")

            # Parse data
            vendor = {
                'vendor_name': str(row['Vendor Name']).strip(),
                'category': category_value,
                'amount': parse_decimal(str(row['Amount'])),
                'frequency': frequency_value,
                'due_date': due_date_obj,
                'start_date': start_date_obj,
                'end_date': end_date_obj,
                'entity': entity_value,
                'priority': int(row.get('Priority', 3)) if not pd.isna(row.get('Priority')) else 3,
                'flexibility_days': int(row.get('Flexibility Days', 0)) if not pd.isna(row.get('Flexibility Days')) else 0,
                'status': str(row.get('Status', 'Active')).strip() if not pd.isna(row.get('Status')) else 'Active',
                'notes': str(row.get('Notes', '')).strip() if not pd.isna(row.get('Notes')) else None
            }

            vendors.append(vendor)

        except Exception as e:
            skipped_errors += 1
            print(f"⚠ Error processing row {idx + 2}: {e}")
            continue  # Skip this row but continue processing

    print(f"✓ Parsed {len(vendors)} vendor contracts")
    if skipped_errors > 0:
        print(f"  Skipped {skipped_errors} rows with errors")

    # Save to database
    if save_to_db:
        with db_manager.session_scope() as session:
            # Clear existing contracts
            session.query(VendorContract).delete()

            # Insert new contracts
            for vendor_data in vendors:
                vendor = VendorContract(**vendor_data)
                session.add(vendor)

        print(f"✓ Saved {len(vendors)} vendor contracts to database")

    return vendors


def import_bank_balances(save_to_db: bool = True) -> List[Dict]:
    """
    Import bank balances from Google Sheets using public CSV export.

    NO CREDENTIALS REQUIRED - uses public CSV export URL.
    Sheet names are configurable from Settings page.

    Expects format with columns: Date, YAHSHUA Balance, ABBA Balance, Total, Notes
    Converts to one row per entity in database.

    Args:
        save_to_db: If True, save to database (default: True)

    Returns:
        List of bank balance dictionaries

    Raises:
        ValueError: If validation fails
    """
    print("Importing bank balances from Google Sheets...")

    # Get sheet name from database config
    _, _, _, bank_balances_sheet = _get_sheets_config()

    # Read sheet as DataFrame (no authentication needed!)
    df = read_sheet_as_dataframe(bank_balances_sheet)

    if df.empty:
        print("⚠ No bank balances found in Google Sheets")
        return []

    balances = []
    skipped_errors = 0

    for idx, row in df.iterrows():
        try:
            # Skip empty rows
            if pd.isna(row.get('Date')) or str(row.get('Date', '')).strip() == '':
                continue

            # Validate required fields
            balance_date = parse_date(str(row['Date']))
            notes = str(row.get('Notes', '')).strip() if not pd.isna(row.get('Notes')) else None

            # Parse YAHSHUA balance
            if 'YAHSHUA Balance' in row and not pd.isna(row['YAHSHUA Balance']):
                yahshua_balance = parse_decimal(str(row['YAHSHUA Balance']))
                balances.append({
                    'balance_date': balance_date,
                    'entity': 'YAHSHUA',
                    'balance': yahshua_balance,
                    'source': 'Google Sheets Import',
                    'notes': notes
                })

            # Parse ABBA balance
            if 'ABBA Balance' in row and not pd.isna(row['ABBA Balance']):
                abba_balance = parse_decimal(str(row['ABBA Balance']))
                balances.append({
                    'balance_date': balance_date,
                    'entity': 'ABBA',
                    'balance': abba_balance,
                    'source': 'Google Sheets Import',
                    'notes': notes
                })

        except Exception as e:
            skipped_errors += 1
            print(f"⚠ Error processing row {idx + 2}: {e}")
            continue  # Skip this row but continue processing

    print(f"✓ Parsed {len(balances)} bank balance entries")
    if skipped_errors > 0:
        print(f"  Skipped {skipped_errors} rows with errors")

    # Save to database
    if save_to_db:
        with db_manager.session_scope() as session:
            # Clear existing balances
            session.query(BankBalance).delete()

            # Insert new balances
            for balance_data in balances:
                balance = BankBalance(**balance_data)
                session.add(balance)

        print(f"✓ Saved {len(balances)} bank balance entries to database")

    return balances


def sync_all_data() -> Dict[str, int]:
    """
    Sync all data from Google Sheets (customers, vendors, bank balances).

    Returns:
        Dictionary with counts of imported records

    Raises:
        Exception: If any import fails
    """
    print("\n" + "=" * 70)
    print("SYNCING ALL DATA FROM GOOGLE SHEETS")
    print("=" * 70 + "\n")

    start_time = datetime.now()

    try:
        customers = import_customer_contracts(save_to_db=True)
        vendors = import_vendor_contracts(save_to_db=True)
        balances = import_bank_balances(save_to_db=True)

        # Update sync timestamp in metadata
        with db_manager.session_scope() as session:
            metadata = session.query(SystemMetadata).filter_by(key='last_google_sheets_sync').first()
            if metadata:
                metadata.value = datetime.now().isoformat()
            else:
                metadata = SystemMetadata(
                    key='last_google_sheets_sync',
                    value=datetime.now().isoformat()
                )
                session.add(metadata)

        elapsed = (datetime.now() - start_time).total_seconds()

        print("\n" + "=" * 70)
        print("SYNC COMPLETE")
        print("=" * 70)
        print(f"Customer Contracts: {len(customers)}")
        print(f"Vendor Contracts: {len(vendors)}")
        print(f"Bank Balances: {len(balances)}")
        print(f"Time Elapsed: {elapsed:.2f} seconds")
        print("=" * 70 + "\n")

        return {
            'customers': len(customers),
            'vendors': len(vendors),
            'balances': len(balances),
            'elapsed_seconds': elapsed
        }

    except Exception as e:
        print(f"\n✗ SYNC FAILED: {e}\n")
        raise
