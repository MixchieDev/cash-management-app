/**
 * Generic CSV builder + browser download trigger.
 */

function escapeCSVValue(value: string): string {
  if (value.includes('"') || value.includes(',') || value.includes('\n') || value.includes('\r')) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function arrayToCSV(headers: string[], rows: string[][]): string {
  const headerLine = headers.map(escapeCSVValue).join(',');
  const dataLines = rows.map((row) => row.map(escapeCSVValue).join(','));
  return [headerLine, ...dataLines].join('\n');
}

export function downloadCSV(filename: string, csvContent: string): void {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
