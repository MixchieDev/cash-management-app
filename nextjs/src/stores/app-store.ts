/**
 * Zustand store for client-side UI state.
 */
import { create } from 'zustand';
import type { Timeframe, ScenarioType } from '@/lib/types';

export interface SelectedAccount {
  entity: string;
  accountName: string;
}

interface AppState {
  // Account selection (replaces entity selector)
  selectedAccounts: SelectedAccount[];
  allAccountsSelected: boolean; // = Consolidated mode
  setSelectedAccounts: (accounts: SelectedAccount[]) => void;
  setAllAccountsSelected: (all: boolean) => void;
  toggleAccount: (account: SelectedAccount) => void;

  // Derived: unique entities from selected accounts
  getSelectedEntities: () => string[];

  // Backward compat: entity string for components that still use it
  selectedEntity: string;

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

export const useAppStore = create<AppState>((set, get) => ({
  selectedAccounts: [],
  allAccountsSelected: true, // Start in consolidated mode
  setSelectedAccounts: (accounts) => set({
    selectedAccounts: accounts,
    allAccountsSelected: false,
    selectedEntity: accounts.length > 0
      ? [...new Set(accounts.map((a) => a.entity))].join(', ')
      : 'Consolidated',
  }),
  setAllAccountsSelected: (all) => set({
    allAccountsSelected: all,
    selectedAccounts: [],
    selectedEntity: 'Consolidated',
  }),
  toggleAccount: (account) => {
    const current = get().selectedAccounts;
    const exists = current.some(
      (a) => a.entity === account.entity && a.accountName === account.accountName
    );
    const updated = exists
      ? current.filter((a) => !(a.entity === account.entity && a.accountName === account.accountName))
      : [...current, account];

    set({
      selectedAccounts: updated,
      allAccountsSelected: false,
      selectedEntity: updated.length > 0
        ? [...new Set(updated.map((a) => a.entity))].join(', ')
        : 'Consolidated',
    });
  },

  getSelectedEntities: () => {
    const state = get();
    if (state.allAccountsSelected) return [];
    return [...new Set(state.selectedAccounts.map((a) => a.entity))];
  },

  selectedEntity: 'Consolidated',

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
