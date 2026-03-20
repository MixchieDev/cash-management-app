'use client';

import { useAppStore } from '@/stores/app-store';
import { PageHeader } from '@/components/layout/header';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CustomerTable } from '@/components/contracts/customer-table';
import { VendorTable } from '@/components/contracts/vendor-table';
import { BankBalanceTable } from '@/components/contracts/bank-balance-table';
import { OverrideManager } from '@/components/contracts/override-manager';
import { Button } from '@/components/ui/button';
import { Users, Building2, Landmark, CalendarClock, Download } from 'lucide-react';
import { downloadTemplate, downloadAllTemplates, TEMPLATE_TYPES } from '@/lib/import-templates';

export default function ContractsPage() {
  const { allAccountsSelected, selectedAccounts } = useAppStore();

  // For contract lists: show all when consolidated, or filter by selected entities
  const selectedEntities = allAccountsSelected || selectedAccounts.length === 0
    ? []
    : [...new Set(selectedAccounts.map((a) => a.entity))];

  const selectedEntity = selectedEntities.length === 1 ? selectedEntities[0] : 'Consolidated';

  // Account names for filtering contracts within an entity
  const selectedAccountNames = allAccountsSelected || selectedAccounts.length === 0
    ? []
    : selectedAccounts.map((a) => a.accountName);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Contracts"
        subtitle="Manage customer and vendor contracts, bank balances, and payment overrides"
      >
        <div className="flex items-center gap-1">
          {TEMPLATE_TYPES.map((t) => (
            <Button
              key={t.value}
              variant="ghost"
              size="sm"
              className="text-xs gap-1 text-slate-500 hover:text-slate-900"
              onClick={() => downloadTemplate(t.value)}
            >
              <Download className="h-3 w-3" />
              {t.label}
            </Button>
          ))}
        </div>
      </PageHeader>

      <Tabs defaultValue="customers">
        <TabsList className="bg-[#F5F5F7] border border-[#E5E5E7]">
          <TabsTrigger value="customers" className="gap-1.5">
            <Users className="h-3.5 w-3.5" />
            Customer Contracts
          </TabsTrigger>
          <TabsTrigger value="vendors" className="gap-1.5">
            <Building2 className="h-3.5 w-3.5" />
            Vendor Contracts
          </TabsTrigger>
          <TabsTrigger value="balances" className="gap-1.5">
            <Landmark className="h-3.5 w-3.5" />
            Bank Balances
          </TabsTrigger>
          <TabsTrigger value="overrides" className="gap-1.5">
            <CalendarClock className="h-3.5 w-3.5" />
            Payment Overrides
          </TabsTrigger>
        </TabsList>

        <TabsContent value="customers" className="mt-4">
          <Card className="border-0 shadow-sm bg-transparent">
            <CardContent className="p-0">
              <CustomerTable entity={selectedEntity} accountFilter={selectedAccountNames} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="vendors" className="mt-4">
          <Card className="border-0 shadow-sm bg-transparent">
            <CardContent className="p-0">
              <VendorTable entity={selectedEntity} accountFilter={selectedAccountNames} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="balances" className="mt-4">
          <Card className="border-0 shadow-sm bg-transparent">
            <CardContent className="p-0">
              <BankBalanceTable entity={selectedEntity} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="overrides" className="mt-4">
          <Card className="border-0 shadow-sm bg-transparent">
            <CardContent className="p-0">
              <OverrideManager entity={selectedEntity} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
