import React, { useState, useEffect } from 'react';
import './data-package-history.css';

// Define TypeScript interfaces
interface DataPackage {
  packageId: string;
  dataType: string;
  createdAt: string;
  expiresAt: string;
  buyer: {
    id: string;
    name: string;
    trustTier: string;
  };
  purpose: string;
  anonymizationLevel: string;
  accessLevel: string;
  rewardAmount: number;
  encryptionStatus: string;
  tokenExpiry: string;
  recordCount: number;
  status: 'active' | 'expired' | 'revoked';
}

interface AuditRecord {
  id: number;
  timestamp: string;
  operation: string;
  status: string;
  buyerId: string;
  buyerName: string;
  errorMessage?: string;
}

interface DataPackageHistoryProps {
  userId: string;
}

const DataPackageHistory: React.FC<DataPackageHistoryProps> = ({ userId }) => {
  const [dataPackages, setDataPackages] = useState<DataPackage[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<DataPackage | null>(null);
  const [auditRecords, setAuditRecords] = useState<AuditRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('all'); // 'all', 'active', 'expired', 'revoked'
  const [sortBy, setSortBy] = useState('date'); // 'date', 'dataType', 'buyer'
  const [sortOrder, setSortOrder] = useState('desc'); // 'asc', 'desc'

  // Fetch data packages from the API
  useEffect(() => {
    const fetchDataPackages = async () => {
      try {
        setLoading(true);
        // In a real implementation, replace with actual API endpoint
        const response = await fetch(`/api/data-packages/history?userId=${userId}`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch data packages');
        }
        
        const data = await response.json();
        setDataPackages(data);
        setError(null);
      } catch (err) {
        setError('Error loading data packages. Please try again.');
        console.error('Error fetching data packages:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDataPackages();
  }, [userId]);

  // Fetch audit records for a specific package
  const fetchAuditRecords = async (packageId: string) => {
    try {
      // In a real implementation, replace with actual API endpoint
      const response = await fetch(`/api/data-packages/audit/${packageId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch audit records for package ${packageId}`);
      }
      
      const data = await response.json();
      setAuditRecords(data);
    } catch (err) {
      console.error('Error fetching audit records:', err);
      setAuditRecords([]);
    }
  };

  // Handle package selection
  const handleSelectPackage = (pkg: DataPackage) => {
    setSelectedPackage(pkg);
    fetchAuditRecords(pkg.packageId);
  };

  // Apply filters and sorting
  const getFilteredAndSortedPackages = () => {
    // Apply filter
    let filtered = dataPackages;
    if (filter !== 'all') {
      filtered = dataPackages.filter(pkg => pkg.status === filter);
    }
    
    // Apply sorting
    return filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'date':
          comparison = new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime();
          break;
        case 'dataType':
          comparison = a.dataType.localeCompare(b.dataType);
          break;
        case 'buyer':
          comparison = a.buyer.name.localeCompare(b.buyer.name);
          break;
        default:
          comparison = 0;
      }
      
      return sortOrder === 'asc' ? comparison : -comparison;
    });
  };

  // Format date
  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get CSS class for package status
  const getStatusClass = (status: string): string => {
    switch (status) {
      case 'active':
        return 'status-active';
      case 'expired':
        return 'status-expired';
      case 'revoked':
        return 'status-revoked';
      default:
        return '';
    }
  };

  // Get CSS class for trust tier
  const getTrustTierClass = (tier: string): string => {
    switch (tier.toLowerCase()) {
      case 'low':
        return 'trust-low';
      case 'standard':
        return 'trust-standard';
      case 'high':
        return 'trust-high';
      default:
        return 'trust-unknown';
    }
  };
  
  // Get CSS class for anonymization level
  const getAnonymizationClass = (level: string): string => {
    switch (level.toLowerCase()) {
      case 'none':
        return 'anon-none';
      case 'minimal':
        return 'anon-minimal';
      case 'partial':
        return 'anon-partial';
      case 'full':
        return 'anon-full';
      default:
        return 'anon-unknown';
    }
  };

  // Handle sort change
  const handleSortChange = (field: string) => {
    if (sortBy === field) {
      // Toggle order if same field
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // New field, default to descending
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  // Render filters and sort controls
  const renderControls = () => {
    return (
      <div className="package-controls">
        <div className="filter-controls">
          <label htmlFor="filter">Filter:</label>
          <select 
            id="filter" 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="all">All Packages</option>
            <option value="active">Active Only</option>
            <option value="expired">Expired Only</option>
            <option value="revoked">Revoked Only</option>
          </select>
        </div>
        
        <div className="sort-controls">
          <label htmlFor="sort">Sort by:</label>
          <div className="sort-buttons">
            <button 
              className={`sort-button ${sortBy === 'date' ? 'active' : ''}`}
              onClick={() => handleSortChange('date')}
            >
              Date {sortBy === 'date' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
            <button 
              className={`sort-button ${sortBy === 'dataType' ? 'active' : ''}`}
              onClick={() => handleSortChange('dataType')}
            >
              Data Type {sortBy === 'dataType' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
            <button 
              className={`sort-button ${sortBy === 'buyer' ? 'active' : ''}`}
              onClick={() => handleSortChange('buyer')}
            >
              Buyer {sortBy === 'buyer' && (sortOrder === 'asc' ? '↑' : '↓')}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Render the package list
  const renderPackageList = () => {
    const filteredPackages = getFilteredAndSortedPackages();
    
    if (filteredPackages.length === 0) {
      return (
        <div className="no-packages">
          <p>No data packages found.</p>
        </div>
      );
    }

    return (
      <div className="package-list">
        <div className="package-list-header">
          <div className="status-col">Status</div>
          <div className="type-col">Data Type</div>
          <div className="buyer-col">Buyer</div>
          <div className="date-col">Created</div>
          <div className="reward-col">Reward</div>
        </div>
        
        {filteredPackages.map(pkg => (
          <div 
            key={pkg.packageId}
            className={`package-item ${selectedPackage?.packageId === pkg.packageId ? 'selected' : ''}`}
            onClick={() => handleSelectPackage(pkg)}
          >
            <div className={`status-col ${getStatusClass(pkg.status)}`}>
              {pkg.status}
            </div>
            <div className="type-col">
              {pkg.dataType}
            </div>
            <div className="buyer-col">
              <span className={`buyer-trust ${getTrustTierClass(pkg.buyer.trustTier)}`}>
                {pkg.buyer.name}
              </span>
            </div>
            <div className="date-col">
              {formatDate(pkg.createdAt)}
            </div>
            <div className="reward-col">
              ${pkg.rewardAmount.toFixed(2)}
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Render the package details
  const renderPackageDetails = () => {
    if (!selectedPackage) {
      return (
        <div className="select-package-prompt">
          <p>Select a data package to view details</p>
        </div>
      );
    }

    return (
      <div className="package-details">
        <h3 className="details-title">{selectedPackage.dataType} Data Package</h3>
        
        <div className="details-sections">
          <div className="details-section">
            <h4>Package Information</h4>
            <div className="detail-item">
              <span className="label">Package ID:</span>
              <span className="value">{selectedPackage.packageId}</span>
            </div>
            <div className="detail-item">
              <span className="label">Created:</span>
              <span className="value">{formatDate(selectedPackage.createdAt)}</span>
            </div>
            <div className="detail-item">
              <span className="label">Expires:</span>
              <span className="value">{formatDate(selectedPackage.expiresAt)}</span>
            </div>
            <div className="detail-item">
              <span className="label">Status:</span>
              <span className={`value status-badge ${getStatusClass(selectedPackage.status)}`}>
                {selectedPackage.status}
              </span>
            </div>
            <div className="detail-item">
              <span className="label">Records:</span>
              <span className="value">{selectedPackage.recordCount} items</span>
            </div>
          </div>
          
          <div className="details-section">
            <h4>Buyer Information</h4>
            <div className="detail-item">
              <span className="label">Buyer:</span>
              <span className="value">{selectedPackage.buyer.name}</span>
            </div>
            <div className="detail-item">
              <span className="label">Trust Tier:</span>
              <span className={`value trust-badge ${getTrustTierClass(selectedPackage.buyer.trustTier)}`}>
                {selectedPackage.buyer.trustTier}
              </span>
            </div>
            <div className="detail-item">
              <span className="label">Purpose:</span>
              <span className="value">{selectedPackage.purpose}</span>
            </div>
            <div className="detail-item">
              <span className="label">Reward:</span>
              <span className="value reward-value">${selectedPackage.rewardAmount.toFixed(2)}</span>
            </div>
          </div>
          
          <div className="details-section">
            <h4>Privacy & Security</h4>
            <div className="detail-item">
              <span className="label">Anonymization:</span>
              <span className={`value anon-badge ${getAnonymizationClass(selectedPackage.anonymizationLevel)}`}>
                {selectedPackage.anonymizationLevel}
              </span>
            </div>
            <div className="detail-item">
              <span className="label">Access Level:</span>
              <span className="value">{selectedPackage.accessLevel}</span>
            </div>
            <div className="detail-item">
              <span className="label">Encryption:</span>
              <span className="value">{selectedPackage.encryptionStatus}</span>
            </div>
            <div className="detail-item">
              <span className="label">Token Expiry:</span>
              <span className="value">{formatDate(selectedPackage.tokenExpiry)}</span>
            </div>
          </div>
        </div>
        
        <div className="audit-section">
          <h4>Access History</h4>
          {auditRecords.length === 0 ? (
            <p className="no-audit-records">No access records found for this package.</p>
          ) : (
            <div className="audit-list">
              {auditRecords.map(record => (
                <div key={record.id} className="audit-item">
                  <div className="audit-timestamp">{formatDate(record.timestamp)}</div>
                  <div className="audit-operation">{record.operation}</div>
                  <div className={`audit-status ${record.status === 'success' ? 'success' : 'error'}`}>
                    {record.status}
                  </div>
                  <div className="audit-buyer">{record.buyerName}</div>
                  {record.errorMessage && (
                    <div className="audit-error">{record.errorMessage}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return <div className="package-history loading">Loading data packages...</div>;
  }

  if (error) {
    return <div className="package-history error">{error}</div>;
  }

  return (
    <div className="package-history">
      <h2>Data Package History</h2>
      
      {renderControls()}
      
      <div className="package-container">
        <div className="packages-panel">
          {renderPackageList()}
        </div>
        
        <div className="details-panel">
          {renderPackageDetails()}
        </div>
      </div>
    </div>
  );
};

export default DataPackageHistory; 