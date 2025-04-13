import React, { useState } from 'react';
import { Card, Button, Dialog } from '../shared';
import { TrustScoreExplainer, CompensationModel } from './index';
import './education.css';

/**
 * Helper component to add a "Learn More" button that opens an educational component in a dialog
 */
interface LearnMoreButtonProps {
  topic: 'trust-score' | 'compensation';
  buttonText?: string;
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'small' | 'medium' | 'large';
}

export const LearnMoreButton: React.FC<LearnMoreButtonProps> = ({
  topic,
  buttonText = 'Learn More',
  variant = 'outline',
  size = 'small'
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleOpen = () => setIsOpen(true);
  const handleClose = () => setIsOpen(false);

  const getTitle = () => {
    switch (topic) {
      case 'trust-score':
        return 'Understanding Trust Scores';
      case 'compensation':
        return 'How Compensation Works';
      default:
        return 'Learn More';
    }
  };

  const getContent = () => {
    switch (topic) {
      case 'trust-score':
        return <TrustScoreExplainer />;
      case 'compensation':
        return <CompensationModel />;
      default:
        return null;
    }
  };

  return (
    <>
      <Button 
        variant={variant} 
        onClick={handleOpen}
        className={size === 'small' ? 'button-small' : size === 'large' ? 'button-large' : ''}
      >
        {buttonText}
      </Button>

      <Dialog
        isOpen={isOpen}
        onClose={handleClose}
        title={getTitle()}
        className="education-dialog"
      >
        {getContent()}
      </Dialog>
    </>
  );
};

/**
 * Educational tooltip to be embedded in other components
 */
interface EducationalTooltipProps {
  children: React.ReactNode;
  topic: 'trust-score' | 'compensation';
  position?: 'top' | 'bottom' | 'left' | 'right';
}

export const EducationalTooltip: React.FC<EducationalTooltipProps> = ({
  children,
  topic,
  position = 'top'
}) => {
  // This is a placeholder for a tooltip component that would display a short explanation
  // A real implementation would use a tooltip library or a custom tooltip component
  return (
    <div className="education-tooltip" title={`Click to learn more about ${topic}`}>
      {children}
      <LearnMoreButton topic={topic} buttonText="?" size="small" variant="outline" />
    </div>
  );
};

/**
 * Educational card to be embedded in other components
 */
interface EducationalCardProps {
  topic: 'trust-score' | 'compensation';
  showButton?: boolean;
}

export const EducationalCard: React.FC<EducationalCardProps> = ({
  topic,
  showButton = true
}) => {
  const getContent = () => {
    switch (topic) {
      case 'trust-score':
        return {
          title: 'Trust Score',
          description: 'Your trust score affects the offers you receive and the compensation you earn.',
          icon: '🛡️'
        };
      case 'compensation':
        return {
          title: 'Compensation Model',
          description: 'Learn how your data contributions are valued and how to maximize your earnings.',
          icon: '💰'
        };
      default:
        return {
          title: 'Learn More',
          description: 'Click to learn more about this topic.',
          icon: '📚'
        };
    }
  };

  const content = getContent();

  return (
    <Card className="education-card">
      <div className="education-metric">
        <div className="education-metric-icon">{content.icon}</div>
        <div>
          <h3 className="education-metric-title">{content.title}</h3>
        </div>
      </div>
      <p>{content.description}</p>
      {showButton && (
        <div style={{ marginTop: '1rem' }}>
          <LearnMoreButton 
            topic={topic} 
            variant="primary"
            size="medium"
          />
        </div>
      )}
    </Card>
  );
};

/**
 * Mini educational banner to be shown at relevant points in the app
 */
interface EducationalMinibannerProps {
  topic: 'trust-score' | 'compensation';
  dismissable?: boolean;
}

export const EducationalMinibanner: React.FC<EducationalMinibannerProps> = ({
  topic,
  dismissable = true
}) => {
  const [isDismissed, setIsDismissed] = useState(false);

  if (isDismissed) return null;

  const getContent = () => {
    switch (topic) {
      case 'trust-score':
        return {
          title: 'Your Trust Score Matters',
          description: 'Higher trust scores lead to better offers and increased compensation.',
          icon: '🛡️'
        };
      case 'compensation':
        return {
          title: 'Maximize Your Earnings',
          description: 'Learn how to increase your data compensation by up to 30%.',
          icon: '💰'
        };
      default:
        return {
          title: 'Learn More',
          description: 'Click to learn more about this topic.',
          icon: '📚'
        };
    }
  };

  const content = getContent();

  return (
    <div 
      style={{
        padding: '0.75rem 1rem',
        backgroundColor: 'var(--highlight-bg)',
        color: 'var(--highlight-color)',
        borderRadius: '4px',
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem'
      }}
    >
      <div>{content.icon}</div>
      <div style={{ flex: 1 }}>
        <strong>{content.title}:</strong> {content.description}
      </div>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        <LearnMoreButton 
          topic={topic} 
          variant="secondary"
          size="small"
        />
        {dismissable && (
          <Button 
            variant="outline" 
            onClick={() => setIsDismissed(true)}
            className="button-small"
          >
            ✕
          </Button>
        )}
      </div>
    </div>
  );
}; 