/**
 * Zustand store for client-side UI state.
 * Replaces Streamlit's st.session_state for UI concerns.
 */
import { create } from 'zustand';
import type { EntityOrConsolidated, Timeframe, ScenarioType } from '@/lib/types';

interface AppState {
  // Entity selection (shared across pages)
  selectedEntity: EntityOrConsolidated;
  setSelectedEntity: (entity: EntityOrConsolidated) => void;

  // Dashboard state
  timeframe: Timeframe;
  setTimeframe: (tf: Timeframe) => void;
  scenarioType: ScenarioType;
  setScenarioType: (st: ScenarioType) => void;

  // Modal state
  transactionModalOpen: boolean;
  transactionModalDate: string | null;
  openTransactionModal: (date: string) => void;
  closeTransactionModal: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  selectedEntity: 'Consolidated',
  setSelectedEntity: (entity) => set({ selectedEntity: entity }),

  timeframe: 'monthly',
  setTimeframe: (timeframe) => set({ timeframe }),
  scenarioType: 'realistic',
  setScenarioType: (scenarioType) => set({ scenarioType }),

  transactionModalOpen: false,
  transactionModalDate: null,
  openTransactionModal: (date) =>
    set({ transactionModalOpen: true, transactionModalDate: date }),
  closeTransactionModal: () =>
    set({ transactionModalOpen: false, transactionModalDate: null }),
}));
