import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './agent-exchange.css';

// Define types for our exchange data
interface ExchangeAlternative {
  access_level: string;
  compensation: number;
}

interface Exchange {
  exchange_id: string;
  timestamp: string;
  buyer_id: string;
  data_type: string;
  access_level: string;
  purpose: string;
  compensation: number;
  status: 'accepted' | 'declined';
  consent_id?: string;
  alternative_suggested?: boolean;
  alternative?: ExchangeAlternative;
}

interface ExchangeHistoryProps {
  userId: string;
}

const AgentExchangeHistory: React.FC<ExchangeHistoryProps> = ({ userId }) => {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchExchanges = async () => {
      try {
        setLoading(true);
        // In production, this would use the actual API endpoint
        const response = await fetch(`/api/agent/exchanges/${userId}`);
        
        if (!response.ok) {
          throw new Error(`Error fetching exchanges: ${response.statusText}`);
        }
        
        const data = await response.json();
        setExchanges(data.exchanges || []);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch agent exchanges:', err);
        setError('Failed to load agent exchanges. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchExchanges();
  }, [userId]);

  const handleExchangeClick = (exchangeId: string) => {
    navigate(`/agent-exchanges/${exchangeId}`);
  };

  // Format date for display
  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Format compensation value
  const formatCompensation = (amount: number) => {
    return `$${amount.toFixed(2)}`;
  };

  if (loading) {
    return <div className="agent-exchange-container">Loading exchanges...</div>;
  }

  if (error) {
    return <div className="agent-exchange-container">{error}</div>;
  }

  return (
    <div className="agent-exchange-container">
      <div className="agent-exchange-header">
        <h2>Agent Exchange History</h2>
      </div>

      {exchanges.length === 0 ? (
        <div className="no-exchanges">
          <div className="no-exchanges-icon">📭</div>
          <div className="empty-state-message">No agent exchanges yet</div>
          <div className="empty-state-desc">Agent exchanges will appear here when data buyers request your data</div>
        </div>
      ) : (
        <div className="agent-exchange-list">
          {exchanges.map((exchange) => (
            <div
              key={exchange.exchange_id}
              className="exchange-item"
              onClick={() => handleExchangeClick(exchange.exchange_id)}
            >
              <div className="exchange-header">
                <div className="exchange-title">
                  Exchange with {exchange.buyer_id}
                </div>
                <div className="exchange-timestamp">
                  {formatDate(exchange.timestamp)}
                </div>
              </div>

              <div className="exchange-details">
                <div className="exchange-detail">
                  <span className="exchange-detail-label">Data:</span>
                  <span className="exchange-detail-value">{exchange.data_type}</span>
                </div>

                <div className="exchange-detail">
                  <span className="exchange-detail-label">Access:</span>
                  <span className="exchange-detail-value">{exchange.access_level.replace('_', ' ')}</span>
                </div>

                <div className="exchange-detail">
                  <span className="exchange-detail-label">Status:</span>
                  <span className={`${exchange.status === 'accepted' ? 'accepted-badge' : 'declined-badge'}`}>
                    {exchange.status}
                  </span>
                </div>

                <div className="exchange-detail">
                  <span className="exchange-detail-label">Compensation:</span>
                  <span className="compensation-tag">{formatCompensation(exchange.compensation)}</span>
                </div>
              </div>

              {exchange.status === 'declined' && exchange.alternative_suggested && (
                <div className="exchange-alternative-hint">
                  Alternative access level suggested
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentExchangeHistory; 