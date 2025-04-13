import React, { useState, useEffect } from 'react';
import { 
  usePreferencesStore, 
  useWalletStore, 
  PayoutFrequency, 
  notifySuccess, 
  notifyError 
} from '../../stores';
import { PayoutCurrency } from '../../types/wallet';
import { formatCurrency } from '../../utils/formatters';
import './wallet.css';
import LoadingState from '../shared/LoadingState';
import ErrorState from '../shared/ErrorState';

const PayoutSettings: React.FC = () => {
  const {
    payoutFrequency,
    payoutThreshold,
    setPayoutFrequency,
    setPayoutThreshold
  } = usePreferencesStore();

  const {
    balance,
    paymentMethods,
    isLoadingBalance,
    isLoadingPaymentMethods,
    balanceError,
    paymentMethodsError,
    fetchBalance,
    fetchPaymentMethods,
    requestPayout
  } = useWalletStore();

  // Local form state
  const [formState, setFormState] = useState({
    frequency: payoutFrequency,
    threshold: payoutThreshold,
    isRequesting: false,
    requestAmount: '',
    paymentMethodId: ''
  });

  // Has unsaved changes
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Get default payment method
  const defaultPaymentMethod = paymentMethods?.find(m => m.isDefault) || null;

  useEffect(() => {
    // Fetch wallet balance and payment methods on component mount
    fetchBalance().catch(err => notifyError('Failed to load wallet balance'));
    fetchPaymentMethods().catch(err => notifyError('Failed to load payment methods'));
  }, [fetchBalance, fetchPaymentMethods]);

  // Update form state when store values change
  useEffect(() => {
    setFormState(prev => ({
      ...prev,
      frequency: payoutFrequency,
      threshold: payoutThreshold,
      paymentMethodId: defaultPaymentMethod?.id || ''
    }));
  }, [payoutFrequency, payoutThreshold, defaultPaymentMethod]);

  // Handle form input changes
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    setFormState(prev => ({
      ...prev,
      [name]: value
    }));
    
    setHasUnsavedChanges(true);
  };

  // Handle saving payout preferences
  const handleSavePreferences = () => {
    // Convert threshold to number
    const threshold = parseFloat(formState.threshold.toString());
    
    if (isNaN(threshold) || threshold <= 0) {
      notifyError('Please enter a valid threshold amount greater than zero');
      return;
    }
    
    // Update preferences in store
    setPayoutFrequency(formState.frequency as PayoutFrequency);
    setPayoutThreshold(threshold);
    
    // Reset unsaved changes flag
    setHasUnsavedChanges(false);
    
    notifySuccess('Payout preferences saved');
  };

  // Handle manual payout request
  const handleRequestPayout = async () => {
    // Validate amount
    const amount = parseFloat(formState.requestAmount);
    
    if (isNaN(amount) || amount <= 0) {
      notifyError('Please enter a valid amount greater than zero');
      return;
    }
    
    // Validate payment method
    if (!formState.paymentMethodId) {
      notifyError('Please select a payment method');
      return;
    }
    
    // Validate amount is available
    if (!balance || balance.available < amount) {
      notifyError('Insufficient funds for payout');
      return;
    }
    
    // Request payout
    setFormState(prev => ({ ...prev, isRequesting: true }));
    
    try {
      const success = await requestPayout(amount, formState.paymentMethodId);
      
      if (success) {
        notifySuccess('Payout requested successfully');
        setFormState(prev => ({ ...prev, requestAmount: '' }));
      } else {
        notifyError('Payout request failed');
      }
    } catch (error) {
      notifyError('An error occurred while processing your request');
    } finally {
      setFormState(prev => ({ ...prev, isRequesting: false }));
    }
  };

  // Get description text for payout frequency
  const getFrequencyDescription = (frequency: PayoutFrequency): string => {
    switch (frequency) {
      case PayoutFrequency.Manual:
        return 'You will need to request payouts manually';
      case PayoutFrequency.Weekly:
        return 'Payouts will be processed every Friday';
      case PayoutFrequency.Monthly:
        return 'Payouts will be processed on the 1st of each month';
      case PayoutFrequency.Threshold:
        return `Payouts will be processed when your balance reaches $${payoutThreshold.toFixed(2)}`;
      default:
        return '';
    }
  };

  // Handle loading states
  if (isLoadingBalance || isLoadingPaymentMethods) {
    return <LoadingState message="Loading payout settings..." />;
  }

  // Handle error states
  if (balanceError || paymentMethodsError) {
    return <ErrorState 
      message={`There was a problem loading your payout settings: ${balanceError || paymentMethodsError}`}
      onRetry={() => {
        fetchBalance();
        fetchPaymentMethods();
      }}
    />;
  }

  return (
    <div className="wallet-container">
      <div className="wallet-header">
        <h2>Payout Settings</h2>
        {hasUnsavedChanges && (
          <div className="wallet-actions">
            <button className="btn btn-primary" onClick={handleSavePreferences}>
              Save Changes
            </button>
          </div>
        )}
      </div>

      <div className="wallet-dashboard-grid">
        {/* Payout Preferences */}
        <div className="payout-form">
          <h3>Payout Preferences</h3>
          
          <div className="form-group">
            <label htmlFor="frequency">Payout Frequency</label>
            <select
              id="frequency"
              name="frequency"
              className="form-select"
              value={formState.frequency}
              onChange={handleInputChange}
            >
              <option value={PayoutFrequency.Manual}>Manual</option>
              <option value={PayoutFrequency.Weekly}>Weekly</option>
              <option value={PayoutFrequency.Monthly}>Monthly</option>
              <option value={PayoutFrequency.Threshold}>When balance reaches threshold</option>
            </select>
            <p className="form-text">{getFrequencyDescription(formState.frequency as PayoutFrequency)}</p>
          </div>
          
          {formState.frequency === PayoutFrequency.Threshold && (
            <div className="form-group">
              <label htmlFor="threshold">Payout Threshold</label>
              <div className="input-group">
                <span className="input-group-text">$</span>
                <input
                  type="number"
                  id="threshold"
                  name="threshold"
                  className="form-control"
                  placeholder="50.00"
                  min="5"
                  step="5"
                  value={formState.threshold}
                  onChange={handleInputChange}
                />
              </div>
              <p className="form-text">Payouts will be processed automatically when your balance reaches this amount</p>
            </div>
          )}
          
          <div className="form-group">
            <label>Default Payment Method</label>
            {!paymentMethods || paymentMethods.length === 0 ? (
              <div className="alert alert-warning">
                No payment methods available. Please add a payment method to receive payouts.
              </div>
            ) : (
              <div className="payment-method-summary">
                {defaultPaymentMethod ? (
                  <>
                    <div className="payment-method-name">{defaultPaymentMethod.nickname}</div>
                    <p className="form-text">
                      To change your default payment method, visit the Payment Methods page.
                    </p>
                  </>
                ) : (
                  <div className="alert alert-warning">
                    No default payment method selected. Please set a default payment method.
                  </div>
                )}
              </div>
            )}
          </div>
          
          {hasUnsavedChanges && (
            <div className="form-group">
              <button 
                className="btn btn-primary" 
                onClick={handleSavePreferences}
              >
                Save Preferences
              </button>
            </div>
          )}
        </div>
        
        {/* Request Payout */}
        <div className="payout-form">
          <h3>Request Payout</h3>
          
          {(!balance || balance.available <= 0) ? (
            <div className="alert alert-info">
              You don't have any funds available for payout at this time.
            </div>
          ) : (
            <>
              <div className="form-group">
                <label>Available for Payout</label>
                <div className="available-balance">
                  {formatCurrency(balance.available, balance.currency)}
                </div>
              </div>
              
              <div className="form-group">
                <label htmlFor="requestAmount">Payout Amount</label>
                <div className="input-group">
                  <span className="input-group-text">$</span>
                  <input
                    type="number"
                    id="requestAmount"
                    name="requestAmount"
                    className="form-control"
                    placeholder="Enter amount"
                    min="1"
                    max={balance.available}
                    value={formState.requestAmount}
                    onChange={handleInputChange}
                  />
                </div>
              </div>
              
              <div className="form-group">
                <label htmlFor="paymentMethodId">Payment Method</label>
                {(!paymentMethods || paymentMethods.length === 0) ? (
                  <div className="alert alert-warning">
                    Please add a payment method before requesting a payout.
                  </div>
                ) : (
                  <select
                    id="paymentMethodId"
                    name="paymentMethodId"
                    className="form-select"
                    value={formState.paymentMethodId}
                    onChange={handleInputChange}
                  >
                    <option value="">Select Payment Method</option>
                    {paymentMethods.map(method => (
                      <option key={method.id} value={method.id}>
                        {method.nickname} {method.isDefault ? '(Default)' : ''}
                      </option>
                    ))}
                  </select>
                )}
              </div>
              
              <div className="form-group">
                <button 
                  className="btn btn-primary" 
                  onClick={handleRequestPayout}
                  disabled={
                    formState.isRequesting || 
                    !formState.requestAmount || 
                    !formState.paymentMethodId ||
                    paymentMethods.length === 0
                  }
                >
                  {formState.isRequesting ? 'Processing...' : 'Request Payout'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PayoutSettings; 