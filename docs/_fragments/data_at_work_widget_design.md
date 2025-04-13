# Data at Work Widget: Visual Design Spec

## Design Philosophy

The widget uses a clean card-based design with subtle gradients and minimal decorative elements that reinforce trust and transparency. The visual hierarchy guides the user through a narrative of their data's impact while maintaining a light, modern aesthetic.

## Component Structure & Styling

```jsx
// DataAtWorkWidget.jsx - Mobile-first responsive component

import React from 'react';
import './DataAtWorkWidget.css';
import { PulseIcon, ShieldIcon, ArrowRightIcon } from '../icons';

const DataAtWorkWidget = ({ 
  category = 'Health',
  headline = 'Your Data Helped Power 3 Health Innovations This Week',
  subtext = 'Healthcare researchers used anonymous insights to improve patient experience design',
  metrics = [
    { value: '12,450', label: 'Community Members' },
    { value: '83%', label: 'Found Helpful' }
  ],
  privacyReminder = 'All insights are privacy-protected and shared with your permission',
  ctaText = 'See My Impact'
}) => {
  return (
    <div className="data-at-work-card">
      <div className="impact-header">
        <div className="pulse-icon-container">
          <PulseIcon />
        </div>
        <h2>{headline}</h2>
      </div>
      
      <p className="impact-subtext">{subtext}</p>
      
      <div className="metrics-container">
        {metrics.map((metric, index) => (
          <div key={index} className="metric-block">
            <span className="metric-value">{metric.value}</span>
            <span className="metric-label">{metric.label}</span>
          </div>
        ))}
      </div>
      
      <div className="privacy-reminder">
        <ShieldIcon />
        <p>{privacyReminder}</p>
      </div>
      
      <button className="impact-cta">
        <span>{ctaText}</span>
        <ArrowRightIcon />
      </button>
    </div>
  );
};

export default DataAtWorkWidget;
```

```css
/* DataAtWorkWidget.css */

.data-at-work-card {
  background: linear-gradient(145deg, var(--card-bg-light, #ffffff) 0%, var(--card-bg-subtle, #f7f9fc) 100%);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  padding: 24px;
  max-width: 100%;
  margin-bottom: 24px;
  border: 1px solid var(--border-subtle, rgba(0, 0, 0, 0.05));
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

/* Subtle hover effect for desktop */
@media (min-width: 768px) {
  .data-at-work-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.08);
  }
}

.impact-header {
  display: flex;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 14px;
}

.pulse-icon-container {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  color: var(--accent-color, #4361ee);
}

.impact-header h2 {
  font-size: 20px;
  font-weight: 600;
  line-height: 1.3;
  color: var(--text-primary, #1a1a2e);
  margin: 0;
}

.impact-subtext {
  font-size: 16px;
  line-height: 1.5;
  color: var(--text-secondary, #4a4a6a);
  margin-bottom: 24px;
}

.metrics-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.metric-block {
  background-color: var(--card-bg-subtle, rgba(67, 97, 238, 0.05));
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.metric-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--accent-color, #4361ee);
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  color: var(--text-secondary, #4a4a6a);
  line-height: 1.4;
}

.privacy-reminder {
  display: flex;
  align-items: center;
  background-color: var(--trust-bg, rgba(67, 97, 238, 0.08));
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  gap: 12px;
}

.privacy-reminder svg {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  color: var(--trust-accent, #4361ee);
}

.privacy-reminder p {
  font-size: 14px;
  line-height: 1.4;
  color: var(--text-secondary, #4a4a6a);
  margin: 0;
}

.impact-cta {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  background-color: var(--button-bg, #4361ee);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 14px 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s ease;
  gap: 8px;
}

.impact-cta:hover {
  background-color: var(--button-hover, #3a56d4);
}

.impact-cta svg {
  width: 18px;
  height: 18px;
}

/* Desktop Adaptations */
@media (min-width: 768px) {
  .data-at-work-card {
    padding: 32px;
    max-width: 640px;
  }
  
  .impact-header h2 {
    font-size: 22px;
  }
  
  .metrics-container {
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  }
}
```

## Responsive Behavior

### Mobile (<768px)
- Full-width card with vertical flow
- Metrics stack in a 2-column grid where space permits, or 1-column on very small screens
- Compact padding and typography

### Desktop (≥768px)
- Fixed maximum width (640px)
- More generous padding
- Slightly larger typography
- Hover state for the card and buttons

## Visual Elements

1. **Pulse Icon**: A subtle animated pulse or signal icon next to the header represents live data activity without surveillance connotations

2. **Shield Icon**: A simple shield icon reinforces the privacy messaging

3. **Metric Blocks**: Lightly tinted backgrounds with accent-colored numbers create visual separation and highlight the data

4. **Gradient Background**: A subtle gradient adds depth without compromising the clean, minimal aesthetic

5. **Trust Indicators**: The privacy reminder section uses a distinct background color and icon to emphasize security

## Implementation Notes

1. **Theming**
   - All colors use CSS variables for easy theming
   - Primary accent color, text colors, and background colors can be customized
   - Consistent with Tavren's trust-centered design language

2. **Accessibility**
   - Color contrast meets WCAG AA standards
   - Interactive elements have appropriate focus states (not shown in CSS)
   - Text sizes remain readable at all breakpoints

3. **Performance**
   - Lightweight component with minimal dependencies
   - SVG icons keep file size small
   - No heavy animations or visual effects

4. **Future Enhancements**
   - The component structure allows for easy addition of animations
   - Metric blocks could be extended to show trends or mini-charts
   - The expanded "See My Impact" view could use the same visual language with more detailed information 