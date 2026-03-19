'use client';

import { PageHeader } from '@/components/layout/header';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScenarioBuilder } from '@/components/scenarios/scenario-builder';
import { ScenarioCompare } from '@/components/scenarios/scenario-compare';
import { StrategicPlanning } from '@/components/scenarios/strategic-planning';

export default function ScenariosPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Scenario Modeling"
        subtitle="What-if analysis for strategic decisions"
      />

      <Tabs defaultValue="build">
        <TabsList>
          <TabsTrigger value="build">Build Scenario</TabsTrigger>
          <TabsTrigger value="compare">Compare Scenarios</TabsTrigger>
          <TabsTrigger value="strategic">Strategic Planning</TabsTrigger>
        </TabsList>

        <TabsContent value="build">
          <ScenarioBuilder />
        </TabsContent>

        <TabsContent value="compare">
          <ScenarioCompare />
        </TabsContent>

        <TabsContent value="strategic">
          <StrategicPlanning />
        </TabsContent>
      </Tabs>
    </div>
  );
}
