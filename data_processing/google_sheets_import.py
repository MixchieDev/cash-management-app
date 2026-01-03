"""
Google Sheets import module for JESUS Company Cash Management System.
Imports customer contracts, vendor contracts, and bank balances from Google Sheets.
"""
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Optional
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from config.settings import GOOGLE_SHEETS_CREDS_PATH, SPREADSHEET_ID
from config.google_sheets_config import (
    CUSTOMER_CONTRACTS_SHEET,
    VENDOR_CONTRACTS_SHEET,
    BANK_BALANCES_SHEET
)
from config.entity_mapping import assign_entity
from database.db_manager import db_manager
from database.models import CustomerContract, VendorContract, BankBalance, SystemMetadata


def connect_to_google_sheets() -> gspread.Client:
    """
    Connect to Google Sheets API.

    Returns:
        Authenticated Google Sheets client

    Raises:
        FileNotFoundError: If credentials file not found
        Exception: If authentication fails
    """
    creds_path = Path(GOOGLE_SHEETS_CREDS_PATH)

    if not creds_path.exists():
        raise FileNotFoundError(
            f"Google Sheets credentials not found at: {creds_path}\n"
            f"Please download credentials from Google Cloud Console and save to this path."
        )

    # Define the scope
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]

    # Authenticate
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        str(creds_path), scope
    )
    client = gspread.authorize(credentials)

    return client


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
    Import customer contracts from Google Sheets.

    Args:
        save_to_db: If True, save to database (default: True)

    Returns:
        List of customer contract dictionaries

    Raises:
        ValueError: If validation fails
    """
    print("Importing customer contracts from Google Sheets...")

    # Connect to Google Sheets
    client = connect_to_google_sheets()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(CUSTOMER_CONTRACTS_SHEET)

    # Get all records
    records = sheet.get_all_records()

    if not records:
        print("⚠ No customer contracts found in Google Sheets")
        return []

    customers = []
    skipped_inactive = 0
    skipped_errors = 0

    for idx, record in enumerate(records, start=2):  # Start at 2 (row 1 is header)
        try:
            # Skip empty rows
            if not record.get('Company Name') or str(record.get('Company Name', '')).strip() == '':
                continue

            # Check client status - ONLY import Active customers
            client_status = str(record.get('Client Status', '')).strip()
            if client_status != 'Active':
                skipped_inactive += 1
                print(f"  Skipping row {idx}: Client Status = '{client_status}' (not Active)")
                continue

            # Validate required fields
            required_fields = ['Company Name', 'Monthly Fee', 'Payment Plan', 'Contract Start', 'Who acquired the client']
            for field in required_fields:
                if field not in record or not str(record[field]).strip():
                    raise ValueError(f"Missing required field '{field}' in row {idx}")

            # Assign entity based on acquisition source
            entity = assign_entity(record['Who acquired the client'])

            # Parse data
            customer = {
                'company_name': str(record['Company Name']).strip(),
                'monthly_fee': parse_decimal(record['Monthly Fee']),
                'payment_plan': str(record['Payment Plan']).strip(),
                'contract_start': parse_date(record['Contract Start']),
                'contract_end': parse_date(record.get('Contract End', '')),
                'status': client_status,
                'who_acquired': str(record['Who acquired the client']).strip(),
                'entity': entity,
                'invoice_day': int(record.get('Invoice Day', 15)),
                'payment_terms_days': int(record.get('Payment Terms Days', 30)),
                'reliability_score': Decimal(str(record.get('Reliability Score', 0.80))),
                'notes': str(record.get('Notes', '')).strip() or None
            }

            customers.append(customer)

        except Exception as e:
            skipped_errors += 1
            print(f"⚠ Error processing row {idx}: {e}")
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
    Import vendor contracts from Google Sheets.

    Args:
        save_to_db: If True, save to database (default: True)

    Returns:
        List of vendor contract dictionaries

    Raises:
        ValueError: If validation fails
    """
    print("Importing vendor contracts from Google Sheets...")

    # Connect to Google Sheets
    client = connect_to_google_sheets()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(VENDOR_CONTRACTS_SHEET)

    # Get all records
    records = sheet.get_all_records()

    if not records:
        print("⚠ No vendor contracts found in Google Sheets")
        return []

    vendors = []
    skipped_errors = 0

    for idx, record in enumerate(records, start=2):
        try:
            # Skip empty rows
            if not record.get('Vendor Name') or str(record.get('Vendor Name', '')).strip() == '':
                continue

            # Validate required fields
            required_fields = ['Vendor Name', 'Category', 'Amount', 'Frequency', 'Due Date', 'Entity']
            for field in required_fields:
                if field not in record or not str(record[field]).strip():
                    raise ValueError(f"Missing required field '{field}' in row {idx}")

            # Parse due_date - handle both day of month (integer) and full dates
            due_date_value = record['Due Date']
            if isinstance(due_date_value, (int, float)):
                # If it's a day number, create a date for current month
                from datetime import date
                today = date.today()
                day = int(due_date_value)
                due_date_obj = date(today.year, today.month, day)
            else:
                # If it's a date string, parse it
                due_date_obj = parse_date(due_date_value)

            # Parse data
            vendor = {
                'vendor_name': str(record['Vendor Name']).strip(),
                'category': str(record['Category']).strip(),
                'amount': parse_decimal(record['Amount']),
                'frequency': str(record['Frequency']).strip(),
                'due_date': due_date_obj,
                'entity': str(record['Entity']).strip(),
                'priority': int(record.get('Priority', 3)),
                'flexibility_days': int(record.get('Flexibility Days', 0)),
                'status': str(record.get('Status', 'Active')).strip(),
                'notes': str(record.get('Notes', '')).strip() or None
            }

            vendors.append(vendor)

        except Exception as e:
            skipped_errors += 1
            print(f"⚠ Error processing row {idx}: {e}")
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
    Import bank balances from Google Sheets.

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

    # Connect to Google Sheets
    client = connect_to_google_sheets()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    sheet = spreadsheet.worksheet(BANK_BALANCES_SHEET)

    # Get all records
    records = sheet.get_all_records()

    if not records:
        print("⚠ No bank balances found in Google Sheets")
        return []

    balances = []
    skipped_errors = 0

    for idx, record in enumerate(records, start=2):
        try:
            # Skip empty rows
            if not record.get('Date') or str(record.get('Date', '')).strip() == '':
                continue

            # Validate required fields
            balance_date = parse_date(record['Date'])
            notes = str(record.get('Notes', '')).strip() or None

            # Parse YAHSHUA balance
            if 'YAHSHUA Balance' in record and record['YAHSHUA Balance']:
                yahshua_balance = parse_decimal(record['YAHSHUA Balance'])
                balances.append({
                    'balance_date': balance_date,
                    'entity': 'YAHSHUA',
                    'balance': yahshua_balance,
                    'source': 'Google Sheets Import',
                    'notes': notes
                })

            # Parse ABBA balance
            if 'ABBA Balance' in record and record['ABBA Balance']:
                abba_balance = parse_decimal(record['ABBA Balance'])
                balances.append({
                    'balance_date': balance_date,
                    'entity': 'ABBA',
                    'balance': abba_balance,
                    'source': 'Google Sheets Import',
                    'notes': notes
                })

        except Exception as e:
            skipped_errors += 1
            print(f"⚠ Error processing row {idx}: {e}")
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
