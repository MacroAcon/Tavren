/**
 * Wallet & Payment Management Types
 */

export enum PaymentMethodType {
  BankAccount = 'bank_account',
  PayPal = 'paypal',
  Venmo = 'venmo',
  CreditCard = 'credit_card',
  Crypto = 'crypto'
}

export enum TransactionType {
  Payout = 'payout',
  Earning = 'earning',
  Refund = 'refund',
  Fee = 'fee'
}

export enum TransactionStatus {
  Pending = 'pending',
  Completed = 'completed',
  Failed = 'failed',
  Cancelled = 'cancelled'
}

export enum PayoutCurrency {
  USD = 'usd',
  EUR = 'eur',
  GBP = 'gbp',
  CAD = 'cad',
  AUD = 'aud'
}

export interface WalletBalance {
  available: number;
  pending: number;
  currency: PayoutCurrency;
  lastUpdated: string;
}

export interface PaymentMethod {
  id: string;
  type: PaymentMethodType;
  isDefault: boolean;
  nickname: string;
  createdAt: string;
  lastUsed: string | null;
  details: {
    // Common fields
    lastFour?: string;
    
    // Bank account fields
    accountType?: string;
    institution?: string;
    
    // Credit card fields
    expiryDate?: string;
    cardBrand?: string;
    
    // PayPal/Venmo fields
    email?: string;
    
    // Crypto fields
    currency?: string;
    address?: string;
    
    // Allow for additional fields
    [key: string]: string | undefined;
  };
}

export interface Transaction {
  id: string;
  amount: number;
  currency: PayoutCurrency;
  type: TransactionType;
  status: TransactionStatus;
  timestamp: string;
  description: string;
  reference: string;
  paymentMethodId: string | null;
  buyerId?: string;
  buyerName?: string;
}

export interface WalletSummary {
  totalEarned: number;
  totalPaidOut: number;
  lastPayout: {
    amount: number;
    date: string;
    method: PaymentMethodType;
  } | null;
  estimatedWeeklyEarnings: number;
  estimatedMonthlyEarnings: number;
} 