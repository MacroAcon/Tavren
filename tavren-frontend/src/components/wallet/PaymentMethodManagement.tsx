import React, { useEffect, useState } from 'react';
import { useWalletStore, notifySuccess, notifyError } from '../../stores';
import { PaymentMethod, PaymentMethodType } from '../../types/wallet';
import './wallet.css';
import LoadingState from '../shared/LoadingState';
import ErrorState from '../shared/ErrorState';
import Dialog from '../shared/Dialog';

const PaymentMethodManagement: React.FC = () => {
  const {
    paymentMethods,
    isLoadingPaymentMethods,
    paymentMethodsError,
    fetchPaymentMethods,
    addPaymentMethod,
    removePaymentMethod,
    setDefaultPaymentMethod
  } = useWalletStore();

  // Local state for adding new payment method form
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showRemoveDialog, setShowRemoveDialog] = useState<string | null>(null);
  const [newMethod, setNewMethod] = useState<Partial<PaymentMethod>>({
    type: PaymentMethodType.BankAccount,
    nickname: '',
    details: {}
  });

  useEffect(() => {
    // Fetch payment methods on component mount
    fetchPaymentMethods().catch(err => notifyError('Failed to load payment methods'));
  }, [fetchPaymentMethods]);

  // Handle form input for new payment method
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    if (name.startsWith('details.')) {
      const detailName = name.split('.')[1];
      setNewMethod(prev => ({
        ...prev,
        details: {
          ...prev.details,
          [detailName]: value
        }
      }));
    } else {
      setNewMethod(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  // Handle payment method type change
  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const type = e.target.value as PaymentMethodType;
    
    // Reset details when type changes
    setNewMethod(prev => ({
      ...prev,
      type,
      details: {}
    }));
  };

  // Handle form submission
  const handleAddPaymentMethod = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Create new payment method object
    const newPaymentMethod: PaymentMethod = {
      id: `pay-${Date.now()}`, // Generated ID (would come from backend)
      type: newMethod.type as PaymentMethodType,
      isDefault: paymentMethods.length === 0, // Set as default if it's the first one
      nickname: newMethod.nickname || `My ${newMethod.type}`,
      createdAt: new Date().toISOString(),
      lastUsed: null,
      details: newMethod.details || {}
    };
    
    // Add payment method to store
    addPaymentMethod(newPaymentMethod);
    
    // Reset form and close dialog
    setNewMethod({
      type: PaymentMethodType.BankAccount,
      nickname: '',
      details: {}
    });
    setShowAddDialog(false);
    
    // Show success notification
    notifySuccess('Payment method added successfully');
  };

  // Handle removal confirmation
  const handleRemoveMethod = () => {
    if (showRemoveDialog) {
      removePaymentMethod(showRemoveDialog);
      setShowRemoveDialog(null);
      notifySuccess('Payment method removed');
    }
  };

  // Handle making a payment method default
  const handleSetDefault = (id: string) => {
    setDefaultPaymentMethod(id);
    notifySuccess('Default payment method updated');
  };

  // Render form fields based on payment method type
  const renderTypeSpecificFields = () => {
    switch (newMethod.type) {
      case PaymentMethodType.BankAccount:
        return (
          <>
            <div className="form-group">
              <label htmlFor="details.accountType">Account Type</label>
              <select
                id="details.accountType"
                name="details.accountType"
                className="form-select"
                value={newMethod.details?.accountType || ''}
                onChange={handleInputChange}
                required
              >
                <option value="">Select Account Type</option>
                <option value="checking">Checking</option>
                <option value="savings">Savings</option>
                <option value="business">Business</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="details.institution">Bank Name</label>
              <input
                type="text"
                id="details.institution"
                name="details.institution"
                className="form-control"
                placeholder="e.g. Chase, Bank of America"
                value={newMethod.details?.institution || ''}
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="details.lastFour">Last 4 Digits</label>
              <input
                type="text"
                id="details.lastFour"
                name="details.lastFour"
                className="form-control"
                placeholder="Last 4 digits of account"
                pattern="[0-9]{4}"
                maxLength={4}
                value={newMethod.details?.lastFour || ''}
                onChange={handleInputChange}
                required
              />
            </div>
          </>
        );
      
      case PaymentMethodType.PayPal:
      case PaymentMethodType.Venmo:
        return (
          <div className="form-group">
            <label htmlFor="details.email">Email Address</label>
            <input
              type="email"
              id="details.email"
              name="details.email"
              className="form-control"
              placeholder="your-email@example.com"
              value={newMethod.details?.email || ''}
              onChange={handleInputChange}
              required
            />
          </div>
        );
      
      case PaymentMethodType.CreditCard:
        return (
          <>
            <div className="form-group">
              <label htmlFor="details.cardBrand">Card Brand</label>
              <select
                id="details.cardBrand"
                name="details.cardBrand"
                className="form-select"
                value={newMethod.details?.cardBrand || ''}
                onChange={handleInputChange}
                required
              >
                <option value="">Select Card Brand</option>
                <option value="visa">Visa</option>
                <option value="mastercard">Mastercard</option>
                <option value="amex">American Express</option>
                <option value="discover">Discover</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="details.lastFour">Last 4 Digits</label>
              <input
                type="text"
                id="details.lastFour"
                name="details.lastFour"
                className="form-control"
                placeholder="Last 4 digits of card"
                pattern="[0-9]{4}"
                maxLength={4}
                value={newMethod.details?.lastFour || ''}
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="details.expiryDate">Expiration Date</label>
              <input
                type="month"
                id="details.expiryDate"
                name="details.expiryDate"
                className="form-control"
                value={newMethod.details?.expiryDate || ''}
                onChange={handleInputChange}
                required
              />
            </div>
          </>
        );
      
      case PaymentMethodType.Crypto:
        return (
          <>
            <div className="form-group">
              <label htmlFor="details.currency">Cryptocurrency</label>
              <select
                id="details.currency"
                name="details.currency"
                className="form-select"
                value={newMethod.details?.currency || ''}
                onChange={handleInputChange}
                required
              >
                <option value="">Select Cryptocurrency</option>
                <option value="btc">Bitcoin (BTC)</option>
                <option value="eth">Ethereum (ETH)</option>
                <option value="usdc">USD Coin (USDC)</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="details.address">Wallet Address</label>
              <input
                type="text"
                id="details.address"
                name="details.address"
                className="form-control"
                placeholder="Your wallet address"
                value={newMethod.details?.address || ''}
                onChange={handleInputChange}
                required
              />
            </div>
          </>
        );
      
      default:
        return null;
    }
  };

  // Get icon for payment method type
  const getPaymentMethodIcon = (type: PaymentMethodType): string => {
    switch (type) {
      case PaymentMethodType.BankAccount:
        return '🏦';
      case PaymentMethodType.PayPal:
        return '🅿️';
      case PaymentMethodType.Venmo:
        return '📱';
      case PaymentMethodType.CreditCard:
        return '💳';
      case PaymentMethodType.Crypto:
        return '🪙';
      default:
        return '💰';
    }
  };

  // Get display name for payment method type
  const getPaymentMethodTypeName = (type: PaymentMethodType): string => {
    switch (type) {
      case PaymentMethodType.BankAccount:
        return 'Bank Account';
      case PaymentMethodType.PayPal:
        return 'PayPal';
      case PaymentMethodType.Venmo:
        return 'Venmo';
      case PaymentMethodType.CreditCard:
        return 'Credit Card';
      case PaymentMethodType.Crypto:
        return 'Cryptocurrency';
      default:
        return 'Other';
    }
  };

  // Format details for display
  const formatPaymentMethodDetails = (method: PaymentMethod): string => {
    switch (method.type) {
      case PaymentMethodType.BankAccount:
        return `${method.details.institution || 'Bank'} •••• ${method.details.lastFour || '****'}`;
      case PaymentMethodType.PayPal:
      case PaymentMethodType.Venmo:
        return method.details.email || 'No email provided';
      case PaymentMethodType.CreditCard:
        return `${method.details.cardBrand || 'Card'} •••• ${method.details.lastFour || '****'}`;
      case PaymentMethodType.Crypto:
        const address = method.details.address || '';
        return address ? `${address.slice(0, 8)}...${address.slice(-8)}` : 'No address provided';
      default:
        return '';
    }
  };

  // Handle loading states
  if (isLoadingPaymentMethods) {
    return <LoadingState message="Loading payment methods..." />;
  }

  // Handle error states
  if (paymentMethodsError) {
    return <ErrorState 
      message={`There was a problem loading your payment methods: ${paymentMethodsError}`}
      onRetry={fetchPaymentMethods}
    />;
  }

  return (
    <div className="wallet-container">
      <div className="wallet-header">
        <h2>Payment Methods</h2>
        <div className="wallet-actions">
          <button className="btn btn-primary" onClick={() => setShowAddDialog(true)}>
            Add Payment Method
          </button>
        </div>
      </div>

      {/* Payment Method List */}
      {(!paymentMethods || paymentMethods.length === 0) ? (
        <div className="empty-state">
          <div className="empty-state-icon">💳</div>
          <h3>No payment methods</h3>
          <p>Add a payment method to receive your earnings.</p>
          <button className="btn btn-primary" onClick={() => setShowAddDialog(true)}>
            Add Payment Method
          </button>
        </div>
      ) : (
        <div className="payment-method-list">
          {paymentMethods.map(method => (
            <div 
              key={method.id} 
              className={`payment-method-card ${method.isDefault ? 'default' : ''}`}
            >
              {method.isDefault && <div className="default-badge">Default</div>}
              
              <div className="payment-method-header">
                <div className="payment-method-icon">
                  {getPaymentMethodIcon(method.type)}
                </div>
                <div>
                  <h4 className="payment-method-name">{method.nickname}</h4>
                  <div className="payment-method-type">
                    {getPaymentMethodTypeName(method.type)}
                  </div>
                </div>
              </div>
              
              <div className="payment-method-info">
                <div className="payment-method-detail">
                  <span>Details:</span>
                  <span>{formatPaymentMethodDetails(method)}</span>
                </div>
                
                <div className="payment-method-detail">
                  <span>Added:</span>
                  <span>{new Date(method.createdAt).toLocaleDateString()}</span>
                </div>
                
                {method.lastUsed && (
                  <div className="payment-method-detail">
                    <span>Last Used:</span>
                    <span>{new Date(method.lastUsed).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
              
              <div className="payment-method-actions">
                {!method.isDefault && (
                  <button 
                    className="btn btn-sm btn-secondary"
                    onClick={() => handleSetDefault(method.id)}
                  >
                    Make Default
                  </button>
                )}
                
                <button 
                  className="btn btn-sm btn-danger"
                  onClick={() => setShowRemoveDialog(method.id)}
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Payment Method Dialog */}
      <Dialog
        isOpen={showAddDialog}
        title="Add Payment Method"
        onClose={() => setShowAddDialog(false)}
      >
        <form onSubmit={handleAddPaymentMethod} className="add-payment-form">
          <div className="form-group">
            <label htmlFor="type">Payment Method Type</label>
            <select
              id="type"
              name="type"
              className="form-select"
              value={newMethod.type}
              onChange={handleTypeChange}
              required
            >
              <option value={PaymentMethodType.BankAccount}>Bank Account</option>
              <option value={PaymentMethodType.PayPal}>PayPal</option>
              <option value={PaymentMethodType.Venmo}>Venmo</option>
              <option value={PaymentMethodType.CreditCard}>Credit Card</option>
              <option value={PaymentMethodType.Crypto}>Cryptocurrency</option>
            </select>
          </div>
          
          <div className="form-group">
            <label htmlFor="nickname">Nickname</label>
            <input
              type="text"
              id="nickname"
              name="nickname"
              className="form-control"
              placeholder={`My ${getPaymentMethodTypeName(newMethod.type as PaymentMethodType)}`}
              value={newMethod.nickname}
              onChange={handleInputChange}
            />
          </div>
          
          {renderTypeSpecificFields()}
          
          <div className="form-group">
            <div className="form-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setShowAddDialog(false)}>
                Cancel
              </button>
              <button type="submit" className="btn btn-primary">
                Add Payment Method
              </button>
            </div>
          </div>
        </form>
      </Dialog>

      {/* Remove Confirmation Dialog */}
      <Dialog
        isOpen={!!showRemoveDialog}
        title="Remove Payment Method"
        onClose={() => setShowRemoveDialog(null)}
      >
        <p>Are you sure you want to remove this payment method? This action cannot be undone.</p>
        <div className="dialog-actions">
          <button 
            className="btn btn-secondary" 
            onClick={() => setShowRemoveDialog(null)}
          >
            Cancel
          </button>
          <button 
            className="btn btn-danger" 
            onClick={handleRemoveMethod}
          >
            Remove
          </button>
        </div>
      </Dialog>
    </div>
  );
};

export default PaymentMethodManagement; 