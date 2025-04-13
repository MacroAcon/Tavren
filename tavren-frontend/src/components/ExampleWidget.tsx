import React from 'react';
import { YourDataAtWork } from './widgets';

/**
 * Example page that demonstrates the YourDataAtWork widget
 * This component can be used to showcase the widget capabilities
 */
const ExampleWidget: React.FC = () => {
  const handleCtaClick = () => {
    console.log('CTA clicked - this would open more detailed impact view');
    alert('You clicked to see more impact details. This would show a detailed view in the real application.');
  };

  return (
    <div className="example-page">
      <h1>Your Dashboard</h1>
      <p className="subtitle">See how your data helps create value</p>
      
      <div className="dashboard-section">
        <h2>Data Impact</h2>
        <YourDataAtWork 
          onCtaClick={handleCtaClick}
        />
      </div>
      
      <div className="example-controls">
        <h3>Widget Customization Options</h3>
        <p>In a real implementation, this widget would be customized and populated with real data:</p>
        <ul>
          <li>Dynamic impact stories based on user contributions</li>
          <li>Real-time metrics from platform analytics</li>
          <li>Integration with consent management system</li>
          <li>Personalized recommendations for additional impact</li>
        </ul>
      </div>
    </div>
  );
};

export default ExampleWidget; 