import { arrayToCSV, downloadCSV } from '@/lib/export-csv';

const TEMPLATES: Record<string, { headers: string[]; sampleRows: string[][]; notes: string[] }> = {
  customers: {
    headers: [
      'Company Name',
      'Monthly Fee',
      'Payment Plan',
      'Contract Start',
      'Contract End',
      'Status',
      'Who Acquired',
      'Entity',
      'Invoice Day',
      'Payment Terms Days',
      'Reliability Score',
      'Bank Account',
      'Notes',
    ],
    sampleRows: [
      [
        'Acme Corp',
        '150000',
        'Monthly',
        '2026-01-01',
        '2027-01-01',
        'Active',
        'YOWI',
        'YAHSHUA',
        '15',
        '30',
        '0.8',
        'Main Account',
        'Key client',
      ],
      [
        'Beta Inc',
        '75000',
        'Quarterly',
        '2026-03-01',
        '',
        'Active',
        'TAI',
        'ABBA',
        '',
        '',
        '0.9',
        '',
        '',
      ],
    ],
    notes: [
      'NOTES:',
      '"Monthly Fee: Amount in PHP (no currency symbol, no commas)"',
      '"Payment Plan: Monthly | Quarterly | Annual | Bi-annually | More than 1 year"',
      '"Dates: YYYY-MM-DD format. Contract End can be blank for ongoing contracts."',
      '"Status: Active | Inactive | Pending | Cancelled"',
      '"Who Acquired: See Settings > Acquisition Sources for valid values"',
      '"Entity: YAHSHUA | ABBA"',
      '"Invoice Day: Day of month (1-28). Leave blank to use default."',
      '"Payment Terms Days: e.g. 30 for Net 30. Leave blank to use default."',
      '"Reliability Score: 0 to 1 (e.g. 0.8 = 80% on-time). Leave blank for default 0.8."',
      '"Bank Account: See Settings > Bank Accounts for valid values. Leave blank for Main Account."',
    ],
  },
  vendors: {
    headers: [
      'Vendor Name',
      'Category',
      'Amount',
      'Frequency',
      'Due Date',
      'Start Date',
      'End Date',
      'Entity',
      'Priority',
      'Flexibility Days',
      'Status',
      'Bank Account',
      'Notes',
    ],
    sampleRows: [
      [
        'AWS',
        'Software/Tech',
        '50000',
        'Monthly',
        '2026-01-21',
        '2026-01-01',
        '',
        'YAHSHUA',
        '3',
        '10',
        'Active',
        'Main Account',
        'Cloud hosting',
      ],
      [
        'Office Rent',
        'Operations',
        '200000',
        'Monthly',
        '2026-01-01',
        '',
        '',
        'YAHSHUA',
        '4',
        '5',
        'Active',
        '',
        '',
      ],
    ],
    notes: [
      'NOTES:',
      '"Amount: Amount in PHP (no currency symbol, no commas)"',
      '"Category: Payroll | Loans | Software/Tech | Operations | Rent | Utilities"',
      '"Frequency: One-time | Daily | Weekly | Bi-weekly | Monthly | Quarterly | Annual"',
      '"Dates: YYYY-MM-DD format. Start/End Date can be blank."',
      '"Entity: YAHSHUA | ABBA"',
      '"Priority: 1 = Payroll (non-negotiable), 2 = Loans, 3 = Software/Tech, 4 = Operations"',
      '"Flexibility Days: How many days payment can be delayed (0 = no flexibility)"',
      '"Status: Active | Inactive | Paid | Pending"',
    ],
  },
  balances: {
    headers: [
      'Balance Date',
      'Entity',
      'Account Name',
      'Balance',
      'Notes',
    ],
    sampleRows: [
      ['2026-03-01', 'YAHSHUA', 'Main Account', '5000000', 'Opening balance'],
      ['2026-03-01', 'ABBA', 'Main Account', '1500000', ''],
    ],
    notes: [
      'NOTES:',
      '"Balance Date: YYYY-MM-DD format"',
      '"Entity: YAHSHUA | ABBA"',
      '"Account Name: See Settings > Bank Accounts for valid values"',
      '"Balance: Amount in PHP (no currency symbol, no commas)"',
    ],
  },
};

export function downloadTemplate(type: 'customers' | 'vendors' | 'balances'): void {
  const template = TEMPLATES[type];
  const csv = arrayToCSV(template.headers, template.sampleRows);
  const withNotes = csv + '\n\n' + template.notes.join('\n');
  downloadCSV(`template-${type}.csv`, withNotes);
}

export function downloadAllTemplates(): void {
  downloadTemplate('customers');
  setTimeout(() => downloadTemplate('vendors'), 100);
  setTimeout(() => downloadTemplate('balances'), 200);
}

export const TEMPLATE_TYPES = [
  { value: 'customers' as const, label: 'Customer Contracts' },
  { value: 'vendors' as const, label: 'Vendor Contracts' },
  { value: 'balances' as const, label: 'Bank Balances' },
];
