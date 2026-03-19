'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { formatCurrency } from '@/lib/currency';
import { useCreateScenario } from '@/hooks/use-scenarios';
import { useAppStore } from '@/stores/app-store';
import { useProjection } from '@/hooks/use-projections';
import { ScenarioCalculator, type ScenarioChangeData } from '@/lib/engine/scenario-calculator';
import Decimal from 'decimal.js';
import { toast } from 'sonner';
import { X } from 'lucide-react';
import { ComparisonChart } from './comparison-chart';

interface ScenarioChange {
  changeType: string;
  startDate: string;
  endDate: string | null;
  label: string;
  monthlyCost: number;
  // Hiring
  employees?: number;
  salaryPerEmployee?: number;
  // Expense
  expenseName?: string;
  expenseAmount?: number;
  // Revenue
  newClients?: number;
  revenuePerClient?: number;
  // Customer loss
  lostRevenue?: number;
}

export function ScenarioBuilder() {
  const { selectedEntity } = useAppStore();
  const [scenarioName, setScenarioName] = useState('');
  const [changes, setChanges] = useState<ScenarioChange[]>([]);
  const [runResult, setRunResult] = useState<{
    baseline: { date: string; endingCash: string }[];
    scenario: { date: string; endingCash: string }[];
  } | null>(null);

  const createScenario = useCreateScenario();
  const { data: projection } = useProjection(selectedEntity, 'monthly', 'realistic');

  // Hiring form state
  const [hireEmployees, setHireEmployees] = useState(5);
  const [hireSalary, setHireSalary] = useState(50000);
  const [hireStart, setHireStart] = useState('');

  // Expense form state
  const [expName, setExpName] = useState('');
  const [expAmount, setExpAmount] = useState(50000);
  const [expCategory, setExpCategory] = useState('Software/Tech');
  const [expStart, setExpStart] = useState('');

  // Revenue form state
  const [revClients, setRevClients] = useState(3);
  const [revPerClient, setRevPerClient] = useState(100000);
  const [revStart, setRevStart] = useState('');

  // Customer loss state
  const [lossRevenue, setLossRevenue] = useState(100000);
  const [lossStart, setLossStart] = useState('');

  function addHiring() {
    if (!hireStart) { toast.error('Please set a start date'); return; }
    setChanges([...changes, {
      changeType: 'hiring',
      startDate: hireStart,
      endDate: null,
      label: `Hire ${hireEmployees} @ ${formatCurrency(hireSalary)}/mo`,
      monthlyCost: hireEmployees * hireSalary,
      employees: hireEmployees,
      salaryPerEmployee: hireSalary,
    }]);
    toast.success('Hiring change added');
  }

  function addExpense() {
    if (!expStart || !expName) { toast.error('Please fill all fields'); return; }
    setChanges([...changes, {
      changeType: 'expense',
      startDate: expStart,
      endDate: null,
      label: `${expName}: ${formatCurrency(expAmount)}/mo`,
      monthlyCost: expAmount,
      expenseName: expName,
      expenseAmount: expAmount,
    }]);
    toast.success('Expense change added');
  }

  function addRevenue() {
    if (!revStart) { toast.error('Please set a start date'); return; }
    setChanges([...changes, {
      changeType: 'revenue',
      startDate: revStart,
      endDate: null,
      label: `${revClients} new clients @ ${formatCurrency(revPerClient)}/mo`,
      monthlyCost: -(revClients * revPerClient),
      newClients: revClients,
      revenuePerClient: revPerClient,
    }]);
    toast.success('Revenue change added');
  }

  function addCustomerLoss() {
    if (!lossStart) { toast.error('Please set a start date'); return; }
    setChanges([...changes, {
      changeType: 'customer_loss',
      startDate: lossStart,
      endDate: null,
      label: `Lose ${formatCurrency(lossRevenue)}/mo revenue`,
      monthlyCost: lossRevenue,
      lostRevenue: lossRevenue,
    }]);
    toast.success('Customer loss added');
  }

  function removeChange(index: number) {
    setChanges(changes.filter((_, i) => i !== index));
  }

  async function handleSave() {
    if (!scenarioName) { toast.error('Enter a scenario name'); return; }
    if (changes.length === 0) { toast.error('Add at least one change'); return; }

    try {
      const result = await createScenario.mutateAsync({
        scenarioName,
        entity: selectedEntity === 'Consolidated' ? 'Consolidated' : selectedEntity,
        description: `${changes.length} changes`,
        changes: changes.map((c) => {
          const change: Record<string, unknown> = {
            changeType: c.changeType,
            startDate: c.startDate,
          };
          if (c.endDate) change.endDate = c.endDate;
          if (c.employees) change.employees = c.employees;
          if (c.salaryPerEmployee) change.salaryPerEmployee = c.salaryPerEmployee;
          if (c.expenseName) change.expenseName = c.expenseName;
          if (c.expenseAmount) change.expenseAmount = c.expenseAmount;
          if (c.newClients) change.newClients = c.newClients;
          if (c.revenuePerClient) change.revenuePerClient = c.revenuePerClient;
          if (c.lostRevenue) change.lostRevenue = c.lostRevenue;
          return change;
        }),
      });

      toast.success('Scenario saved');
    } catch {
      toast.error('Failed to save scenario');
    }
  }

  function handleRun() {
    if (changes.length === 0) { toast.error('Add at least one change'); return; }
    if (!projection || projection.dataPoints.length === 0) {
      toast.error('No projection data available'); return;
    }

    const calculator = new ScenarioCalculator();

    // Convert baseline to engine format
    const baselinePoints = projection.dataPoints.map((dp: any) => ({
      date: new Date(dp.date),
      startingCash: new Decimal(dp.startingCash),
      inflows: new Decimal(dp.inflows),
      outflows: new Decimal(dp.outflows),
      endingCash: new Decimal(dp.endingCash),
      entity: dp.entity,
      timeframe: dp.timeframe,
      scenarioType: dp.scenarioType,
      isNegative: dp.isNegative,
    }));

    // Convert changes to engine format
    const engineChanges: ScenarioChangeData[] = changes.map((c) => ({
      changeType: c.changeType,
      startDate: new Date(c.startDate),
      endDate: c.endDate ? new Date(c.endDate) : null,
      employees: c.employees,
      salaryPerEmployee: c.salaryPerEmployee ? new Decimal(c.salaryPerEmployee) : undefined,
      expenseName: c.expenseName,
      expenseAmount: c.expenseAmount ? new Decimal(c.expenseAmount) : undefined,
      newClients: c.newClients,
      revenuePerClient: c.revenuePerClient ? new Decimal(c.revenuePerClient) : undefined,
      lostRevenue: c.lostRevenue ? new Decimal(c.lostRevenue) : undefined,
    }));

    const scenarioPoints = calculator.applyScenarioChanges(baselinePoints, engineChanges);

    setRunResult({
      baseline: projection.dataPoints.map((dp: any) => ({
        date: dp.date,
        endingCash: dp.endingCash,
      })),
      scenario: scenarioPoints.map((dp) => ({
        date: dp.date instanceof Date ? dp.date.toISOString().split('T')[0] : String(dp.date),
        endingCash: dp.endingCash.toFixed(2),
      })),
    });

    toast.success('Scenario calculated');
  }

  const totalMonthlyImpact = changes.reduce((sum, c) => sum + c.monthlyCost, 0);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-3 gap-6">
        {/* Left: Change builders */}
        <div className="col-span-2">
          <Tabs defaultValue="hiring">
            <TabsList className="w-full">
              <TabsTrigger value="hiring" className="flex-1">Hiring</TabsTrigger>
              <TabsTrigger value="expenses" className="flex-1">Expenses</TabsTrigger>
              <TabsTrigger value="revenue" className="flex-1">Revenue</TabsTrigger>
              <TabsTrigger value="loss" className="flex-1">Customer Loss</TabsTrigger>
            </TabsList>

            <TabsContent value="hiring">
              <Card className="border-0 shadow-sm">
                <CardContent className="pt-6 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Number of Employees</Label>
                      <Input type="number" min={1} max={100} value={hireEmployees}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setHireEmployees(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label>Salary per Employee</Label>
                      <Input type="number" min={20000} value={hireSalary}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setHireSalary(Number(e.target.value))} />
                    </div>
                  </div>
                  <div>
                    <Label>Start Date</Label>
                    <Input type="date" value={hireStart}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setHireStart(e.target.value)} />
                  </div>
                  <p className="text-sm text-[#86868B]">
                    Monthly payroll impact: <span className="font-medium text-[#FF3B30]">{formatCurrency(hireEmployees * hireSalary)}</span>
                  </p>
                  <Button onClick={addHiring} className="bg-[#007AFF]">Add Hiring to Scenario</Button>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="expenses">
              <Card className="border-0 shadow-sm">
                <CardContent className="pt-6 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Expense Name</Label>
                      <Input value={expName}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setExpName(e.target.value)}
                        placeholder="e.g., New Office Lease" />
                    </div>
                    <div>
                      <Label>Monthly Amount</Label>
                      <Input type="number" min={10000} value={expAmount}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setExpAmount(Number(e.target.value))} />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Category</Label>
                      <Select value={expCategory} onValueChange={(v: string | null) => v && setExpCategory(v)}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          {['Software/Tech', 'Operations', 'Rent', 'Utilities'].map(c => (
                            <SelectItem key={c} value={c}>{c}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Start Date</Label>
                      <Input type="date" value={expStart}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setExpStart(e.target.value)} />
                    </div>
                  </div>
                  <Button onClick={addExpense} className="bg-[#007AFF]">Add Expense to Scenario</Button>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="revenue">
              <Card className="border-0 shadow-sm">
                <CardContent className="pt-6 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Number of New Clients</Label>
                      <Input type="number" min={1} max={50} value={revClients}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRevClients(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label>Revenue per Client</Label>
                      <Input type="number" min={10000} value={revPerClient}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRevPerClient(Number(e.target.value))} />
                    </div>
                  </div>
                  <div>
                    <Label>Start Date</Label>
                    <Input type="date" value={revStart}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRevStart(e.target.value)} />
                  </div>
                  <p className="text-sm text-[#86868B]">
                    New monthly revenue: <span className="font-medium text-[#34C759]">{formatCurrency(revClients * revPerClient)}</span>
                  </p>
                  <Button onClick={addRevenue} className="bg-[#007AFF]">Add Revenue to Scenario</Button>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="loss">
              <Card className="border-0 shadow-sm">
                <CardContent className="pt-6 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Monthly Revenue Lost</Label>
                      <Input type="number" min={10000} value={lossRevenue}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLossRevenue(Number(e.target.value))} />
                    </div>
                    <div>
                      <Label>Loss Start Date</Label>
                      <Input type="date" value={lossStart}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLossStart(e.target.value)} />
                    </div>
                  </div>
                  <Button onClick={addCustomerLoss} className="bg-[#007AFF]">Add Customer Loss to Scenario</Button>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Right: Current scenario summary */}
        <div>
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Current Scenario</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Scenario Name</Label>
                <Input value={scenarioName}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setScenarioName(e.target.value)}
                  placeholder="e.g., Q2 Expansion Plan" />
              </div>

              <div>
                <Badge variant="secondary">{selectedEntity}</Badge>
              </div>

              <Separator />

              {changes.length === 0 ? (
                <p className="text-sm text-[#86868B] text-center py-4">
                  No changes added yet
                </p>
              ) : (
                <div className="space-y-2">
                  {changes.map((c, i) => (
                    <div key={i} className="flex items-center justify-between rounded-lg bg-[#F5F5F7] px-3 py-2">
                      <div>
                        <p className="text-xs font-medium text-[#1D1D1F]">{c.label}</p>
                        <p className="text-xs text-[#86868B]">
                          From {c.startDate}
                        </p>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => removeChange(i)}>
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              <Separator />

              <div className="text-center">
                <p className="text-xs text-[#86868B]">Monthly Net Impact</p>
                <p className={`text-lg font-semibold ${totalMonthlyImpact > 0 ? 'text-[#FF3B30]' : 'text-[#34C759]'}`}>
                  {totalMonthlyImpact > 0 ? '-' : '+'}{formatCurrency(Math.abs(totalMonthlyImpact))}
                </p>
              </div>

              <div className="flex gap-2">
                <Button onClick={handleRun} className="flex-1 bg-[#007AFF]"
                  disabled={changes.length === 0}>
                  Run Scenario
                </Button>
                <Button onClick={handleSave} variant="outline" className="flex-1"
                  disabled={changes.length === 0 || createScenario.isPending}>
                  Save
                </Button>
              </div>
              <Button variant="ghost" className="w-full text-[#86868B]"
                onClick={() => { setChanges([]); setRunResult(null); setScenarioName(''); }}>
                Clear All
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Results */}
      {runResult && (
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">Scenario Results</CardTitle>
          </CardHeader>
          <CardContent>
            <ComparisonChart
              baseline={runResult.baseline}
              scenarios={[{ name: scenarioName || 'Scenario', dataPoints: runResult.scenario }]}
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
