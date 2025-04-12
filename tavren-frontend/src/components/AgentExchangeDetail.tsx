import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './agent-exchange.css';

// Define interfaces for our types
interface MockRequest {
  a2a_version: string;
  message_id: string;
  timestamp: string;
  sender: string;
  recipient: string;
  message_type: string;
  content: {
    format: string;
    body: {
      data_type: string;
      access_level: string;
      compensation: number;
    }
  };
  metadata: {
    mcp_context: {
      purpose: string;
    }
  };
}

interface MockResponse {
  a2a_version: string;
  message_id: string;
  timestamp: string;
  sender: string;
  recipient: string;
  message_type: string;
  content: {
    format: string;
    body: {
      request_id: string;
      status: 'accepted' | 'declined';
      reason: string;
      data_payload?: {
        format: string;
        availability: string;
        access_url: string;
      };
      alternative_suggestion?: {
        data_type: string;
        access_level: string;
        estimated_compensation: number;
      };
    }
  };
  metadata: {
    tavren: {
      consent_id: string | null;
      user_trust_score: number;
    }
  };
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
  alternative?: {
    access_level: string;
    compensation: number;
  };
  // These would be populated from separate API calls
  request?: MockRequest;
  response?: MockResponse;
}

const AgentExchangeDetail: React.FC = () => {
  const { exchangeId } = useParams<{ exchangeId: string }>();
  const navigate = useNavigate();
  const [exchange, setExchange] = useState<Exchange | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchExchangeDetail = async () => {
      try {
        setLoading(true);
        
        // In a production environment, this would fetch from the real API
        // For the POC, we'll use mock data
        
        // Mock exchange data with request and response
        const mockExchange: Exchange = {
          exchange_id: 'ex_002',
          timestamp: new Date().toISOString(),
          buyer_id: 'org456',
          data_type: 'location',
          access_level: 'precise_persistent',
          purpose: 'transportation_optimization',
          compensation: 0.85,
          status: 'declined',
          alternative_suggested: true,
          alternative: {
            access_level: 'anonymous_short_term',
            compensation: 0.65
          },
          // Mock request message
          request: {
            a2a_version: '0.1',
            message_id: 'msg_123456',
            timestamp: new Date().toISOString(),
            sender: 'agent:buyer/org456',
            recipient: 'agent:tavren/anon:user1',
            message_type: 'REQUEST',
            content: {
              format: 'application/json',
              body: {
                data_type: 'location',
                access_level: 'precise_persistent',
                compensation: 0.85
              }
            },
            metadata: {
              mcp_context: {
                purpose: 'transportation_optimization'
              }
            }
          },
          // Mock response message
          response: {
            a2a_version: '0.1',
            message_id: 'resp_789012',
            timestamp: new Date().toISOString(),
            sender: 'agent:tavren/anon:user1',
            recipient: 'agent:buyer/org456',
            message_type: 'RESPONSE',
            content: {
              format: 'application/json',
              body: {
                request_id: 'msg_123456',
                status: 'declined',
                reason: "Access level 'precise_persistent' rejected for 'location'",
                alternative_suggestion: {
                  data_type: 'location',
                  access_level: 'anonymous_short_term',
                  estimated_compensation: 0.65
                }
              }
            },
            metadata: {
              tavren: {
                consent_id: null,
                user_trust_score: 85
              }
            }
          }
        };
        
        // Simulate API delay
        setTimeout(() => {
          setExchange(mockExchange);
          setLoading(false);
        }, 500);
        
      } catch (err) {
        console.error('Failed to fetch exchange details:', err);
        setError('Failed to load exchange details. Please try again.');
        setLoading(false);
      }
    };

    if (exchangeId) {
      fetchExchangeDetail();
    } else {
      setError('Exchange ID is missing');
      setLoading(false);
    }
  }, [exchangeId]);

  const handleBack = () => {
    navigate(-1);
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
    return <div className="exchange-detail-container">Loading exchange details...</div>;
  }

  if (error || !exchange) {
    return <div className="exchange-detail-container">{error || 'Exchange not found'}</div>;
  }

  return (
    <div className="exchange-detail-container">
      <div className="exchange-detail-header">
        <div className="exchange-detail-title">
          Exchange with {exchange.buyer_id}
        </div>
        <button onClick={handleBack}>Back to List</button>
      </div>

      <div className="exchange-summary">
        <div className="exchange-detail">
          <span className="exchange-detail-label">Date:</span>
          <span className="exchange-detail-value">{formatDate(exchange.timestamp)}</span>
        </div>
        <div className="exchange-detail">
          <span className="exchange-detail-label">Status:</span>
          <span className={`${exchange.status === 'accepted' ? 'accepted-badge' : 'declined-badge'}`}>
            {exchange.status}
          </span>
        </div>
      </div>

      <div className="exchange-flow">
        {/* Buyer Request */}
        {exchange.request && (
          <div className="message-card message-incoming">
            <div className="message-direction-marker"></div>
            <div className="message-content">
              <div className="message-header">
                <span className="message-sender">{exchange.request.sender}</span>
                <span className="message-type">{exchange.request.message_type}</span>
              </div>
              <div className="message-timestamp">
                {formatDate(exchange.request.timestamp)}
              </div>
              <div className="message-body">
                <div className="message-field data-field">
                  <div className="message-field-label">Data Type:</div>
                  <div className="message-field-value">{exchange.request.content.body.data_type}</div>
                </div>
                <div className="message-field data-field">
                  <div className="message-field-label">Access Level:</div>
                  <div className="message-field-value">{exchange.request.content.body.access_level.replace('_', ' ')}</div>
                </div>
                <div className="message-field data-field">
                  <div className="message-field-label">Compensation:</div>
                  <div className="message-field-value">{formatCompensation(exchange.request.content.body.compensation)}</div>
                </div>
                <div className="message-field data-field">
                  <div className="message-field-label">Purpose:</div>
                  <div className="message-field-value">{exchange.request.metadata.mcp_context.purpose}</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tavren Response */}
        {exchange.response && (
          <div className="message-card message-outgoing">
            <div className="message-direction-marker"></div>
            <div className="message-content">
              <div className="message-header">
                <span className="message-sender">{exchange.response.sender}</span>
                <span className="message-type">{exchange.response.message_type}</span>
              </div>
              <div className="message-timestamp">
                {formatDate(exchange.response.timestamp)}
              </div>
              <div className="message-body">
                <div className={`consent-decision ${exchange.response.content.body.status}`}>
                  <div className="consent-info">
                    <div className={`consent-status consent-${exchange.response.content.body.status}`}>
                      {exchange.response.content.body.status === 'accepted' ? 'Request Accepted' : 'Request Declined'}
                    </div>
                    <div className="consent-reason">{exchange.response.content.body.reason}</div>
                  </div>
                </div>

                {exchange.response.content.body.status === 'accepted' && exchange.response.content.body.data_payload && (
                  <div className="data-payload-details">
                    <div className="message-field">
                      <div className="message-field-label">Data Format:</div>
                      <div className="message-field-value">{exchange.response.content.body.data_payload.format}</div>
                    </div>
                    <div className="message-field">
                      <div className="message-field-label">Availability:</div>
                      <div className="message-field-value">{exchange.response.content.body.data_payload.availability}</div>
                    </div>
                    <div className="message-field">
                      <div className="message-field-label">Access URL:</div>
                      <div className="message-field-value">{exchange.response.content.body.data_payload.access_url}</div>
                    </div>
                  </div>
                )}

                {exchange.response.content.body.status === 'declined' && exchange.response.content.body.alternative_suggestion && (
                  <div className="alternative-suggestion">
                    <div className="alternative-header">Alternative Suggestion</div>
                    <div className="alternative-details">
                      <div className="exchange-detail">
                        <span className="exchange-detail-label">Access Level:</span>
                        <span className="exchange-detail-value">
                          {exchange.response.content.body.alternative_suggestion.access_level.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="exchange-detail">
                        <span className="exchange-detail-label">Compensation:</span>
                        <span className="exchange-detail-value compensation-tag">
                          {formatCompensation(exchange.response.content.body.alternative_suggestion.estimated_compensation)}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentExchangeDetail; 