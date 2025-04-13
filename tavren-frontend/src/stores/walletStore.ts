import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { 
  WalletBalance, 
  Transaction, 
  PaymentMethod, 
  WalletSummary,
  TransactionStatus,
  TransactionType,
  PaymentMethodType,
  PayoutCurrency
} from '../types/wallet';
import apiClient from '../utils/apiClient';

export interface WalletState {
  // Wallet data
  balance: WalletBalance | null;
  transactions: Transaction[];
  paymentMethods: PaymentMethod[];
  walletSummary: WalletSummary | null;
  
  // Loading states
  isLoadingBalance: boolean;
  isLoadingTransactions: boolean;
  isLoadingPaymentMethods: boolean;
  isLoadingSummary: boolean;
  
  // Error states
  balanceError: string | null;
  transactionsError: string | null;
  paymentMethodsError: string | null;
  summaryError: string | null;
  
  // Actions - Balance
  fetchBalance: () => Promise<void>;
  setBalance: (balance: WalletBalance) => void;
  setBalanceLoading: (isLoading: boolean) => void;
  setBalanceError: (error: string | null) => void;
  
  // Actions - Transactions
  fetchTransactions: (page?: number, limit?: number) => Promise<void>;
  setTransactions: (transactions: Transaction[]) => void;
  addTransaction: (transaction: Transaction) => void;
  updateTransactionStatus: (id: string, status: TransactionStatus) => void;
  setTransactionsLoading: (isLoading: boolean) => void;
  setTransactionsError: (error: string | null) => void;
  
  // Actions - Payment Methods
  fetchPaymentMethods: () => Promise<void>;
  setPaymentMethods: (methods: PaymentMethod[]) => void;
  addPaymentMethod: (method: PaymentMethod) => void;
  removePaymentMethod: (id: string) => Promise<boolean>;
  setDefaultPaymentMethod: (id: string) => Promise<boolean>;
  setPaymentMethodsLoading: (isLoading: boolean) => void;
  setPaymentMethodsError: (error: string | null) => void;
  
  // Actions - Summary
  fetchWalletSummary: () => Promise<void>;
  setWalletSummary: (summary: WalletSummary) => void;
  setSummaryLoading: (isLoading: boolean) => void;
  setSummaryError: (error: string | null) => void;
  
  // Wallet actions
  requestPayout: (amount: number, paymentMethodId: string) => Promise<boolean>;
  updatePayoutSettings: (settings: { frequency?: string, threshold?: number, methodId?: string }) => Promise<boolean>;
  clearWalletData: () => void;
}

export const useWalletStore = create<WalletState>()(
  persist(
    (set, get) => ({
      // Initial state
      balance: null,
      transactions: [],
      paymentMethods: [],
      walletSummary: null,
      
      isLoadingBalance: false,
      isLoadingTransactions: false,
      isLoadingPaymentMethods: false,
      isLoadingSummary: false,
      
      balanceError: null,
      transactionsError: null,
      paymentMethodsError: null,
      summaryError: null,
      
      // Balance actions
      fetchBalance: async () => {
        try {
          set({ isLoadingBalance: true, balanceError: null });
          const balance = await apiClient.get<WalletBalance>('/wallet/balance');
          set({ balance, isLoadingBalance: false });
        } catch (error) {
          set({ 
            isLoadingBalance: false, 
            balanceError: error instanceof Error ? error.message : 'Failed to fetch balance' 
          });
          throw error;
        }
      },
      
      setBalance: (balance) => set({ balance }),
      setBalanceLoading: (isLoading) => set({ isLoadingBalance: isLoading }),
      setBalanceError: (error) => set({ balanceError: error }),
      
      // Transaction actions
      fetchTransactions: async (page = 1, limit = 20) => {
        try {
          set({ isLoadingTransactions: true, transactionsError: null });
          const params = { page, limit };
          const transactions = await apiClient.get<Transaction[]>('/wallet/transactions', { params });
          set({ transactions, isLoadingTransactions: false });
        } catch (error) {
          set({ 
            isLoadingTransactions: false, 
            transactionsError: error instanceof Error ? error.message : 'Failed to fetch transactions' 
          });
          throw error;
        }
      },
      
      setTransactions: (transactions) => set({ transactions }),
      
      addTransaction: (transaction) => set(
        (state) => ({ transactions: [transaction, ...state.transactions] })
      ),
      
      updateTransactionStatus: (id, status) => set(
        (state) => ({
          transactions: state.transactions.map(txn => 
            txn.id === id ? { ...txn, status } : txn
          )
        })
      ),
      
      setTransactionsLoading: (isLoading) => set({ isLoadingTransactions: isLoading }),
      setTransactionsError: (error) => set({ transactionsError: error }),
      
      // Payment method actions
      fetchPaymentMethods: async () => {
        try {
          set({ isLoadingPaymentMethods: true, paymentMethodsError: null });
          const paymentMethods = await apiClient.get<PaymentMethod[]>('/wallet/payment-methods');
          set({ paymentMethods, isLoadingPaymentMethods: false });
        } catch (error) {
          set({ 
            isLoadingPaymentMethods: false, 
            paymentMethodsError: error instanceof Error ? error.message : 'Failed to fetch payment methods' 
          });
          throw error;
        }
      },
      
      setPaymentMethods: (methods) => set({ paymentMethods: methods }),
      
      addPaymentMethod: (method) => set(
        (state) => ({ paymentMethods: [...state.paymentMethods, method] })
      ),
      
      removePaymentMethod: async (id) => {
        try {
          await apiClient.delete<{ success: boolean }>(`/wallet/payment-methods/${id}`);
          set((state) => ({
            paymentMethods: state.paymentMethods.filter(method => method.id !== id)
          }));
          return true;
        } catch (error) {
          set({ 
            paymentMethodsError: error instanceof Error ? error.message : 'Failed to remove payment method' 
          });
          return false;
        }
      },
      
      setDefaultPaymentMethod: async (id) => {
        try {
          await apiClient.patch<{ success: boolean }>(`/wallet/payment-methods/${id}/default`);
          set((state) => ({
            paymentMethods: state.paymentMethods.map(method => ({
              ...method,
              isDefault: method.id === id
            }))
          }));
          return true;
        } catch (error) {
          set({ 
            paymentMethodsError: error instanceof Error ? error.message : 'Failed to set default payment method' 
          });
          return false;
        }
      },
      
      setPaymentMethodsLoading: (isLoading) => set({ isLoadingPaymentMethods: isLoading }),
      setPaymentMethodsError: (error) => set({ paymentMethodsError: error }),
      
      // Wallet summary actions
      fetchWalletSummary: async () => {
        try {
          set({ isLoadingSummary: true, summaryError: null });
          const walletSummary = await apiClient.get<WalletSummary>('/wallet/summary');
          set({ walletSummary, isLoadingSummary: false });
        } catch (error) {
          set({ 
            isLoadingSummary: false, 
            summaryError: error instanceof Error ? error.message : 'Failed to fetch wallet summary' 
          });
          throw error;
        }
      },
      
      setWalletSummary: (summary) => set({ walletSummary: summary }),
      setSummaryLoading: (isLoading) => set({ isLoadingSummary: isLoading }),
      setSummaryError: (error) => set({ summaryError: error }),
      
      // Wallet actions
      requestPayout: async (amount, paymentMethodId) => {
        try {
          const result = await apiClient.post<{ success: boolean, transactionId: string }>('/wallet/payout', {
            amount,
            paymentMethodId
          });
          
          if (result.success && result.transactionId) {
            // Fetch the new transaction
            const newTransaction = await apiClient.get<Transaction>(`/wallet/transactions/${result.transactionId}`);
            
            // Add to transactions list
            get().addTransaction(newTransaction);
            
            // Refresh balance
            get().fetchBalance();
            
            return true;
          }
          return false;
        } catch (error) {
          return false;
        }
      },
      
      updatePayoutSettings: async (settings) => {
        try {
          await apiClient.patch<{ success: boolean }>('/wallet/payout-settings', settings);
          return true;
        } catch (error) {
          return false;
        }
      },
      
      clearWalletData: () => set({
        balance: null,
        transactions: [],
        paymentMethods: [],
        walletSummary: null,
        balanceError: null,
        transactionsError: null,
        paymentMethodsError: null,
        summaryError: null
      })
    }),
    {
      name: 'tavren-wallet-storage',
      partialize: (state) => ({
        // Only persist these values
        balance: state.balance,
        transactions: state.transactions,
        paymentMethods: state.paymentMethods,
        walletSummary: state.walletSummary
      })
    }
  )
);

// Selectors
export const selectBalance = (state: WalletState) => state.balance;
export const selectTransactions = (state: WalletState) => state.transactions;
export const selectPaymentMethods = (state: WalletState) => state.paymentMethods;
export const selectWalletSummary = (state: WalletState) => state.walletSummary;
export const selectIsLoadingWallet = (state: WalletState) => (
  state.isLoadingBalance || 
  state.isLoadingTransactions || 
  state.isLoadingPaymentMethods || 
  state.isLoadingSummary
);
export const selectDefaultPaymentMethod = (state: WalletState) => 
  state.paymentMethods.find(m => m.isDefault) || null; 