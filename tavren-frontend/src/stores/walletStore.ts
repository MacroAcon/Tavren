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
  fetchTransactions: () => Promise<void>;
  setTransactions: (transactions: Transaction[]) => void;
  addTransaction: (transaction: Transaction) => void;
  updateTransactionStatus: (id: string, status: TransactionStatus) => void;
  setTransactionsLoading: (isLoading: boolean) => void;
  setTransactionsError: (error: string | null) => void;
  
  // Actions - Payment Methods
  fetchPaymentMethods: () => Promise<void>;
  setPaymentMethods: (methods: PaymentMethod[]) => void;
  addPaymentMethod: (method: PaymentMethod) => void;
  removePaymentMethod: (id: string) => void;
  setDefaultPaymentMethod: (id: string) => void;
  setPaymentMethodsLoading: (isLoading: boolean) => void;
  setPaymentMethodsError: (error: string | null) => void;
  
  // Actions - Summary
  fetchWalletSummary: () => Promise<void>;
  setWalletSummary: (summary: WalletSummary) => void;
  setSummaryLoading: (isLoading: boolean) => void;
  setSummaryError: (error: string | null) => void;
  
  // Wallet actions
  requestPayout: (amount: number, paymentMethodId: string) => Promise<boolean>;
  clearWalletData: () => void;
}

// Mock API calls - in real implementation these would make real API requests
async function mockFetchBalance(): Promise<WalletBalance> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        available: 152.75,
        pending: 47.25,
        currency: PayoutCurrency.USD,
        lastUpdated: new Date().toISOString()
      });
    }, 800);
  });
}

async function mockFetchTransactions(): Promise<Transaction[]> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        {
          id: 'txn-001',
          amount: 25.50,
          currency: PayoutCurrency.USD,
          type: TransactionType.Earning,
          status: TransactionStatus.Completed,
          timestamp: '2023-08-15T14:32:45Z',
          description: 'Data sharing payment from AI Research Co.',
          reference: 'REF-AI-2023-1245',
          paymentMethodId: null,
          buyerId: 'buyer-123',
          buyerName: 'AI Research Co.'
        },
        {
          id: 'txn-002',
          amount: 47.25,
          currency: PayoutCurrency.USD,
          type: TransactionType.Earning,
          status: TransactionStatus.Pending,
          timestamp: '2023-08-17T10:15:22Z',
          description: 'Consent sharing payment from DataBuyers Inc.',
          reference: 'REF-DB-2023-3422',
          paymentMethodId: null,
          buyerId: 'buyer-456',
          buyerName: 'DataBuyers Inc.'
        },
        {
          id: 'txn-003',
          amount: 100.00,
          currency: PayoutCurrency.USD,
          type: TransactionType.Payout,
          status: TransactionStatus.Completed,
          timestamp: '2023-08-10T16:45:11Z',
          description: 'Monthly payout to bank account',
          reference: 'PAY-2023-08-001',
          paymentMethodId: 'pay-001'
        }
      ]);
    }, 1000);
  });
}

async function mockFetchPaymentMethods(): Promise<PaymentMethod[]> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve([
        {
          id: 'pay-001',
          type: PaymentMethodType.BankAccount,
          isDefault: true,
          nickname: 'Main Checking',
          createdAt: '2023-07-01T12:00:00Z',
          lastUsed: '2023-08-10T16:45:11Z',
          details: {
            lastFour: '4567',
            accountType: 'checking',
            institution: 'National Bank'
          }
        },
        {
          id: 'pay-002',
          type: PaymentMethodType.PayPal,
          isDefault: false,
          nickname: 'My PayPal',
          createdAt: '2023-07-05T14:22:33Z',
          lastUsed: null,
          details: {}
        }
      ]);
    }, 900);
  });
}

async function mockFetchWalletSummary(): Promise<WalletSummary> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        totalEarned: 350.50,
        totalPaidOut: 150.00,
        lastPayout: {
          amount: 100.00,
          date: '2023-08-10T16:45:11Z',
          method: PaymentMethodType.BankAccount
        },
        estimatedWeeklyEarnings: 36.75,
        estimatedMonthlyEarnings: 157.50
      });
    }, 700);
  });
}

async function mockRequestPayout(amount: number, paymentMethodId: string): Promise<boolean> {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Simulate success most of the time, occasional failure
      const success = Math.random() > 0.1;
      resolve(success);
    }, 1200);
  });
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
          const balance = await mockFetchBalance();
          set({ balance, isLoadingBalance: false });
        } catch (error) {
          set({ 
            isLoadingBalance: false, 
            balanceError: error instanceof Error ? error.message : 'Failed to fetch balance' 
          });
        }
      },
      
      setBalance: (balance) => set({ balance }),
      setBalanceLoading: (isLoading) => set({ isLoadingBalance: isLoading }),
      setBalanceError: (error) => set({ balanceError: error }),
      
      // Transaction actions
      fetchTransactions: async () => {
        try {
          set({ isLoadingTransactions: true, transactionsError: null });
          const transactions = await mockFetchTransactions();
          set({ transactions, isLoadingTransactions: false });
        } catch (error) {
          set({ 
            isLoadingTransactions: false, 
            transactionsError: error instanceof Error ? error.message : 'Failed to fetch transactions' 
          });
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
      
      // Payment methods actions
      fetchPaymentMethods: async () => {
        try {
          set({ isLoadingPaymentMethods: true, paymentMethodsError: null });
          const methods = await mockFetchPaymentMethods();
          set({ paymentMethods: methods, isLoadingPaymentMethods: false });
        } catch (error) {
          set({ 
            isLoadingPaymentMethods: false, 
            paymentMethodsError: error instanceof Error ? error.message : 'Failed to fetch payment methods' 
          });
        }
      },
      
      setPaymentMethods: (methods) => set({ paymentMethods: methods }),
      
      addPaymentMethod: (method) => set(
        (state) => {
          // If this is marked as default, unmark others
          let updatedMethods = state.paymentMethods;
          if (method.isDefault) {
            updatedMethods = updatedMethods.map(m => ({
              ...m,
              isDefault: false
            }));
          }
          return { paymentMethods: [...updatedMethods, method] };
        }
      ),
      
      removePaymentMethod: (id) => set(
        (state) => ({
          paymentMethods: state.paymentMethods.filter(m => m.id !== id)
        })
      ),
      
      setDefaultPaymentMethod: (id) => set(
        (state) => ({
          paymentMethods: state.paymentMethods.map(m => ({
            ...m,
            isDefault: m.id === id
          }))
        })
      ),
      
      setPaymentMethodsLoading: (isLoading) => set({ isLoadingPaymentMethods: isLoading }),
      setPaymentMethodsError: (error) => set({ paymentMethodsError: error }),
      
      // Summary actions
      fetchWalletSummary: async () => {
        try {
          set({ isLoadingSummary: true, summaryError: null });
          const summary = await mockFetchWalletSummary();
          set({ walletSummary: summary, isLoadingSummary: false });
        } catch (error) {
          set({ 
            isLoadingSummary: false, 
            summaryError: error instanceof Error ? error.message : 'Failed to fetch wallet summary' 
          });
        }
      },
      
      setWalletSummary: (summary) => set({ walletSummary: summary }),
      setSummaryLoading: (isLoading) => set({ isLoadingSummary: isLoading }),
      setSummaryError: (error) => set({ summaryError: error }),
      
      // Wallet actions
      requestPayout: async (amount, paymentMethodId) => {
        try {
          // Validate amount is available
          const { balance } = get();
          if (!balance || balance.available < amount) {
            set({ transactionsError: 'Insufficient balance for payout' });
            return false;
          }
          
          // Validate payment method exists
          const { paymentMethods } = get();
          const method = paymentMethods.find(m => m.id === paymentMethodId);
          if (!method) {
            set({ paymentMethodsError: 'Invalid payment method' });
            return false;
          }
          
          // Request payout
          const success = await mockRequestPayout(amount, paymentMethodId);
          
          if (success) {
            // If successful, update the balance and add a transaction
            const newTransaction: Transaction = {
              id: `payout-${Date.now()}`,
              amount,
              currency: balance.currency,
              type: TransactionType.Payout,
              status: TransactionStatus.Pending,
              timestamp: new Date().toISOString(),
              description: `Payout to ${method.nickname}`,
              reference: `PAY-${new Date().toISOString().slice(0, 10)}`,
              paymentMethodId
            };
            
            set((state) => ({
              balance: state.balance ? {
                ...state.balance,
                available: state.balance.available - amount,
                lastUpdated: new Date().toISOString()
              } : null,
              transactions: [newTransaction, ...state.transactions]
            }));
          }
          
          return success;
        } catch (error) {
          set({ transactionsError: error instanceof Error ? error.message : 'Failed to process payout' });
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
        // Only persist data, not loading states or errors
        balance: state.balance,
        transactions: state.transactions,
        paymentMethods: state.paymentMethods,
        walletSummary: state.walletSummary
      })
    }
  )
);

// Selectors for efficient state access
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