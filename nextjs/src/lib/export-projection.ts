import { formatCurrency } from '@/lib/currency';
import { arrayToCSV, downloadCSV } from '@/lib/export-csv';
import type { ProjectionDataPoint, RevenueEvent, ExpenseEvent } from '@/lib/types';

interface ExportMetadata {
  entity: string;
  scenario: string;
  timeframe: string;
  balanceDate: string | null;
}

export function exportProjection(
  data: {
    dataPoints: ProjectionDataPoint[];
    revenueEvents: RevenueEvent[];
    expenseEvents: ExpenseEvent[];
  },
  metadata: ExportMetadata
): void {
  const today = new Date().toISOString().split('T')[0];
  const sections: string[] = [];

  // Section 1 — Metadata
  sections.push(
    [
      'Cash Flow Projection Export',
      `Entity:,${metadata.entity}`,
      `Scenario:,${metadata.scenario}`,
      `Timeframe:,${metadata.timeframe}`,
      `Balance Date:,${metadata.balanceDate ?? 'N/A'}`,
      `Exported:,${today}`,
    ].join('\n')
  );

  // Section 2 — Projection Summary
  const summaryHeaders = ['Date', 'Starting Cash', 'Inflows', 'Outflows', 'Ending Cash'];
  const summaryRows = data.dataPoints.map((dp) => [
    dp.date,
    formatCurrency(dp.startingCash),
    formatCurrency(dp.inflows),
    formatCurrency(dp.outflows),
    formatCurrency(dp.endingCash),
  ]);
  sections.push('PROJECTION SUMMARY\n' + arrayToCSV(summaryHeaders, summaryRows));

  // Section 3 — Revenue Events
  const revenueHeaders = ['Date', 'Company', 'Amount', 'Entity', 'Payment Plan'];
  const revenueRows = data.revenueEvents.map((e) => [
    e.date,
    e.companyName,
    formatCurrency(e.amount),
    e.entity,
    e.paymentPlan,
  ]);
  sections.push('REVENUE EVENTS\n' + arrayToCSV(revenueHeaders, revenueRows));

  // Section 4 — Expense Events
  const expenseHeaders = ['Date', 'Vendor', 'Amount', 'Entity', 'Category', 'Priority', 'Payroll'];
  const expenseRows = data.expenseEvents.map((e) => [
    e.date,
    e.vendorName,
    formatCurrency(e.amount),
    e.entity,
    e.category,
    String(e.priority),
    e.isPayroll ? 'Yes' : 'No',
  ]);
  sections.push('EXPENSE EVENTS\n' + arrayToCSV(expenseHeaders, expenseRows));

  const csvContent = sections.join('\n\n');
  const filename = `cash-projection-${metadata.entity.toLowerCase()}-${metadata.scenario}-${today}.csv`;
  downloadCSV(filename, csvContent);
}
