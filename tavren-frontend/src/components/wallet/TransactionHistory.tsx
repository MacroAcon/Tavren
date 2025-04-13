import React, { useEffect, useState } from 'react';
import { useWalletStore, notifyError } from '../../stores';
import { Transaction, TransactionStatus, TransactionType } from '../../types/wallet';
import { formatCurrency, formatDate } from '../../utils/formatters';
import './wallet.css';
import LoadingState from '../shared/LoadingState';
import ErrorState from '../shared/ErrorState';

// Icons for different transaction types
const getTransactionIcon = (type: TransactionType): string => {
  switch (type) {
    case TransactionType.Earning:
      return '💵';
    case TransactionType.Payout:
      return '🏦';
    case TransactionType.Fee:
      return '🧾';
    case TransactionType.Refund:
      return '↩️';
    default:
      return '💰';
  }
};

const TransactionHistory: React.FC = () => {
  const {
    transactions,
    isLoadingTransactions,
    transactionsError,
    fetchTransactions
  } = useWalletStore();

  // Filter state
  const [filters, setFilters] = useState({
    type: 'all',
    status: 'all',
    dateRange: 'all',
    minAmount: '',
    maxAmount: ''
  });

  // Filtered transactions
  const [filteredTransactions, setFilteredTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    // Fetch transactions on component mount
    fetchTransactions().catch(err => notifyError('Failed to load transaction history'));
  }, [fetchTransactions]);

  // Apply filters whenever transactions or filters change
  useEffect(() => {
    if (!transactions) return;
    
    let filtered = [...transactions];
    
    // Filter by type
    if (filters.type !== 'all') {
      filtered = filtered.filter(t => t.type === filters.type);
    }
    
    // Filter by status
    if (filters.status !== 'all') {
      filtered = filtered.filter(t => t.status === filters.status);
    }
    
    // Filter by date range
    if (filters.dateRange !== 'all') {
      const now = new Date();
      let startDate = new Date();
      
      switch (filters.dateRange) {
        case 'today':
          startDate.setHours(0, 0, 0, 0);
          break;
        case 'week':
          startDate.setDate(now.getDate() - 7);
          break;
        case 'month':
          startDate.setMonth(now.getMonth() - 1);
          break;
        case 'year':
          startDate.setFullYear(now.getFullYear() - 1);
          break;
      }
      
      filtered = filtered.filter(t => new Date(t.timestamp) >= startDate);
    }
    
    // Filter by amount range
    if (filters.minAmount) {
      const minAmount = parseFloat(filters.minAmount);
      if (!isNaN(minAmount)) {
        filtered = filtered.filter(t => t.amount >= minAmount);
      }
    }
    
    if (filters.maxAmount) {
      const maxAmount = parseFloat(filters.maxAmount);
      if (!isNaN(maxAmount)) {
        filtered = filtered.filter(t => t.amount <= maxAmount);
      }
    }
    
    setFilteredTransactions(filtered);
  }, [transactions, filters]);

  // Handle form input changes
  const handleFilterChange = (e: React.ChangeEvent<HTMLSelectElement | HTMLInputElement>) => {
    const { name, value } = e.target;
    setFilters(prevFilters => ({
      ...prevFilters,
      [name]: value
    }));
  };

  // Handle loading state
  if (isLoadingTransactions) {
    return <LoadingState message="Loading transaction history..." />;
  }

  // Handle error state
  if (transactionsError) {
    return <ErrorState 
      message={`There was a problem loading your transaction history: ${transactionsError}`}
      onRetry={fetchTransactions}
    />;
  }

  // Empty state
  if (!transactions || transactions.length === 0) {
    return (
      <div className="wallet-container">
        <div className="wallet-header">
          <h2>Transaction History</h2>
        </div>
        <div className="empty-state">
          <div className="empty-state-icon">📝</div>
          <h3>No transactions yet</h3>
          <p>Your transaction history will appear here once you start earning or receiving payouts.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="wallet-container">
      <div className="wallet-header">
        <h2>Transaction History</h2>
        <div className="wallet-actions">
          <button className="btn btn-secondary">Export History</button>
        </div>
      </div>

      {/* Filters */}
      <div className="transaction-filters">
        <div className="form-group">
          <label htmlFor="type">Type</label>
          <select 
            id="type" 
            name="type"
            className="form-select"
            value={filters.type}
            onChange={handleFilterChange}
          >
            <option value="all">All Types</option>
            <option value={TransactionType.Earning}>Earnings</option>
            <option value={TransactionType.Payout}>Payouts</option>
            <option value={TransactionType.Fee}>Fees</option>
            <option value={TransactionType.Refund}>Refunds</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="status">Status</label>
          <select 
            id="status" 
            name="status"
            className="form-select"
            value={filters.status}
            onChange={handleFilterChange}
          >
            <option value="all">All Statuses</option>
            <option value={TransactionStatus.Completed}>Completed</option>
            <option value={TransactionStatus.Pending}>Pending</option>
            <option value={TransactionStatus.Failed}>Failed</option>
            <option value={TransactionStatus.Cancelled}>Cancelled</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="dateRange">Date Range</label>
          <select 
            id="dateRange" 
            name="dateRange"
            className="form-select"
            value={filters.dateRange}
            onChange={handleFilterChange}
          >
            <option value="all">All Time</option>
            <option value="today">Today</option>
            <option value="week">Last 7 Days</option>
            <option value="month">Last 30 Days</option>
            <option value="year">Last Year</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="minAmount">Min Amount</label>
          <input 
            type="number"
            id="minAmount"
            name="minAmount"
            className="form-control"
            placeholder="0.00"
            value={filters.minAmount}
            onChange={handleFilterChange}
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="maxAmount">Max Amount</label>
          <input 
            type="number"
            id="maxAmount"
            name="maxAmount"
            className="form-control"
            placeholder="1000.00"
            value={filters.maxAmount}
            onChange={handleFilterChange}
          />
        </div>
      </div>

      {/* Transaction List */}
      <div className="transaction-history">
        <div className="transaction-list">
          {filteredTransactions.length === 0 ? (
            <div className="empty-state">
              <h3>No matching transactions</h3>
              <p>Try adjusting your filters to see more results.</p>
            </div>
          ) : (
            <>
              {/* Table header - only visible on desktop */}
              <div className="transaction-row transaction-header d-none d-md-grid">
                <div></div>
                <div>Description</div>
                <div>Date</div>
                <div>Status</div>
                <div>Amount</div>
                <div></div>
              </div>
              
              {/* Transactions */}
              {filteredTransactions.map(transaction => (
                <div key={transaction.id} className="transaction-row">
                  <div className={`transaction-icon ${transaction.type.toLowerCase()}`}>
                    {getTransactionIcon(transaction.type)}
                  </div>
                  
                  <div className="transaction-details">
                    <div className="transaction-description">{transaction.description}</div>
                    <div className="transaction-reference">Ref: {transaction.reference}</div>
                  </div>
                  
                  <div className="transaction-date">
                    {formatDate(transaction.timestamp, true)}
                  </div>
                  
                  <div className={`transaction-status ${transaction.status.toLowerCase()}`}>
                    {transaction.status}
                  </div>
                  
                  <div className={`transaction-amount ${transaction.type.toLowerCase()}`}>
                    {transaction.type === TransactionType.Payout || transaction.type === TransactionType.Fee
                      ? `-${formatCurrency(transaction.amount, transaction.currency)}`
                      : formatCurrency(transaction.amount, transaction.currency)}
                  </div>
                  
                  <div className="transaction-actions">
                    <button className="btn btn-icon" title="View Details">
                      📋
                    </button>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default TransactionHistory; 