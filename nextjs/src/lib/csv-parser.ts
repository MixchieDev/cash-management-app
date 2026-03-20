/**
 * Simple CSV parser for importing data.
 * Handles quoted fields, commas within quotes, and newlines within quotes.
 */

export function parseCSV(text: string): { headers: string[]; rows: Record<string, string>[] } {
  const lines = splitCSVLines(text);
  if (lines.length === 0) return { headers: [], rows: [] };

  const headers = parseCSVLine(lines[0]);
  const rows: Record<string, string>[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    // Skip empty lines and NOTES lines
    if (!line || line.startsWith('NOTES') || line.startsWith('"NOTES')) continue;
    // Skip lines that start with a quote and contain documentation (note lines from template)
    if (line.startsWith('"') && !line.includes(',')) continue;

    const values = parseCSVLine(line);
    // Skip if all values are empty
    if (values.every((v) => !v.trim())) continue;

    const row: Record<string, string> = {};
    for (let j = 0; j < headers.length; j++) {
      row[headers[j]] = (values[j] ?? '').trim();
    }
    rows.push(row);
  }

  return { headers, rows };
}

function splitCSVLines(text: string): string[] {
  const lines: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch === '"') {
      inQuotes = !inQuotes;
      current += ch;
    } else if ((ch === '\n' || ch === '\r') && !inQuotes) {
      if (ch === '\r' && text[i + 1] === '\n') i++; // skip \r\n
      if (current.trim()) lines.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  if (current.trim()) lines.push(current);
  return lines;
}

function parseCSVLine(line: string): string[] {
  const values: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      values.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  values.push(current);
  return values;
}

// ═══════════════════════════════════════════════════════════════
// Row mappers — convert CSV row objects to Convex mutation args
// ═══════════════════════════════════════════════════════════════

export function mapCustomerRow(row: Record<string, string>) {
  const monthlyFee = parseFloat(row['Monthly Fee']);
  if (!row['Company Name'] || isNaN(monthlyFee)) return null;

  return {
    companyName: row['Company Name'],
    monthlyFee,
    paymentPlan: row['Payment Plan'] || 'Monthly',
    contractStart: row['Contract Start'],
    contractEnd: row['Contract End'] || undefined,
    status: row['Status'] || 'Active',
    whoAcquired: row['Who Acquired'] || '',
    entity: row['Entity'] || 'YAHSHUA',
    invoiceDay: row['Invoice Day'] ? parseInt(row['Invoice Day']) : undefined,
    paymentTermsDays: row['Payment Terms Days'] ? parseInt(row['Payment Terms Days']) : undefined,
    reliabilityScore: row['Reliability Score'] ? parseFloat(row['Reliability Score']) : 0.8,
    bankAccount: row['Bank Account'] || 'Main Account',
    notes: row['Notes'] || undefined,
    source: 'csv-import',
  };
}

export function mapVendorRow(row: Record<string, string>) {
  const amount = parseFloat(row['Amount']);
  if (!row['Vendor Name'] || isNaN(amount)) return null;

  return {
    vendorName: row['Vendor Name'],
    category: row['Category'] || 'Operations',
    amount,
    frequency: row['Frequency'] || 'Monthly',
    dueDate: row['Due Date'] || '',
    startDate: row['Start Date'] || undefined,
    endDate: row['End Date'] || undefined,
    entity: row['Entity'] || 'YAHSHUA',
    priority: row['Priority'] ? parseInt(row['Priority']) : 4,
    flexibilityDays: row['Flexibility Days'] ? parseInt(row['Flexibility Days']) : 0,
    status: row['Status'] || 'Active',
    bankAccount: row['Bank Account'] || 'Main Account',
    notes: row['Notes'] || undefined,
    source: 'csv-import',
  };
}

export function mapBalanceRow(row: Record<string, string>) {
  const balance = parseFloat(row['Balance']);
  if (!row['Balance Date'] || isNaN(balance)) return null;

  return {
    balanceDate: row['Balance Date'],
    entity: row['Entity'] || 'YAHSHUA',
    accountName: row['Account Name'] || 'Main Account',
    balance,
    source: 'csv-import',
    notes: row['Notes'] || undefined,
  };
}
