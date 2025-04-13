import React, { useEffect } from 'react';
import { useWalletStore, useNotificationStore, notifyError } from '../../stores';
import { formatCurrency } from '../../utils/formatters';
import './wallet.css';
import LoadingState from '../shared/LoadingState';
import ErrorState from '../shared/ErrorState';

const WalletDashboard: React.FC = () => {
  const {
    balance,
    walletSummary,
    isLoadingBalance,
    isLoadingSummary,
    balanceError,
    summaryError,
    fetchBalance,
    fetchWalletSummary
  } = useWalletStore();

  useEffect(() => {
    // Fetch wallet data on component mount
    fetchBalance().catch(err => notifyError('Failed to load wallet balance'));
    fetchWalletSummary().catch(err => notifyError('Failed to load wallet summary'));
  }, [fetchBalance, fetchWalletSummary]);

  // Handle loading states
  if (isLoadingBalance || isLoadingSummary) {
    return <LoadingState message="Loading wallet data..." />;
  }

  // Handle error states
  if (balanceError || summaryError) {
    return <ErrorState 
      message={`There was a problem loading your wallet data: ${balanceError || summaryError}`}
      onRetry={() => {
        fetchBalance();
        fetchWalletSummary();
      }}
    />;
  }

  // Handle case when data isn't available yet
  if (!balance || !walletSummary) {
    return <div className="empty-state">
      <div className="empty-state-icon">💰</div>
      <h3>Your wallet is being set up</h3>
      <p>We're preparing your wallet. This should only take a moment.</p>
      <button onClick={() => {
        fetchBalance();
        fetchWalletSummary();
      }} className="btn btn-primary">Refresh</button>
    </div>;
  }

  return (
    <div className="wallet-container">
      <div className="wallet-header">
        <h2>Wallet Dashboard</h2>
        <div className="wallet-actions">
          <button className="btn btn-primary">Request Payout</button>
        </div>
      </div>

      {/* Balance Card */}
      <div className="balance-card">
        <div className="balance-header">Available Balance</div>
        <div className="balance-amount">{formatCurrency(balance.available, balance.currency)}</div>
        <div className="balance-pending">
          {balance.pending > 0 ? 
            `${formatCurrency(balance.pending, balance.currency)} pending` : 
            'No pending earnings'}
        </div>
        
        <div className="balance-card-row">
          <div className="balance-stat">
            <div className="balance-stat-value">
              {formatCurrency(walletSummary.estimatedWeeklyEarnings, balance.currency)}
            </div>
            <div className="balance-stat-label">Weekly Est.</div>
          </div>
          
          <div className="balance-stat">
            <div className="balance-stat-value">
              {formatCurrency(walletSummary.totalEarned, balance.currency)}
            </div>
            <div className="balance-stat-label">Total Earned</div>
          </div>
          
          <div className="balance-stat">
            <div className="balance-stat-value">
              {formatCurrency(walletSummary.totalPaidOut, balance.currency)}
            </div>
            <div className="balance-stat-label">Total Paid</div>
          </div>
        </div>
      </div>

      {/* Dashboard Grid - Summary and Stats */}
      <div className="wallet-dashboard-grid">
        <div className="summary-card">
          <h3>Revenue Summary</h3>
          
          <div className="summary-stat">
            <div className="summary-label">Last Payout</div>
            <div className="summary-value">
              {walletSummary.lastPayout ? 
                formatCurrency(walletSummary.lastPayout.amount, balance.currency) :
                'No payouts yet'}
            </div>
          </div>
          
          <div className="summary-stat">
            <div className="summary-label">Last Payout Date</div>
            <div className="summary-value">
              {walletSummary.lastPayout ? 
                new Date(walletSummary.lastPayout.date).toLocaleDateString() :
                'N/A'}
            </div>
          </div>
          
          <div className="summary-stat">
            <div className="summary-label">Weekly Estimated</div>
            <div className="summary-value">
              {formatCurrency(walletSummary.estimatedWeeklyEarnings, balance.currency)}
            </div>
          </div>
          
          <div className="summary-stat">
            <div className="summary-label">Monthly Estimated</div>
            <div className="summary-value">
              {formatCurrency(walletSummary.estimatedMonthlyEarnings, balance.currency)}
            </div>
          </div>
        </div>
        
        <div className="summary-card">
          <h3>Quick Actions</h3>
          <button className="btn btn-primary btn-block mb-2">Request Payout</button>
          <button className="btn btn-secondary btn-block mb-2">Add Payment Method</button>
          <button className="btn btn-secondary btn-block">Manage Payout Settings</button>
        </div>
      </div>
    </div>
  );
}

export default WalletDashboard; 