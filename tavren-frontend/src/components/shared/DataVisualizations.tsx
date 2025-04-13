import React from 'react';
import './shared-components.css';

// Mock chart placeholders for visualization components
// In a real app, you'd use a charting library like Chart.js or Recharts

// Common types for all charts
export type ChartSize = 'small' | 'medium' | 'large';
export type ChartLegendPosition = 'top' | 'bottom' | 'left' | 'right' | 'none';

// Base chart props shared across all chart types
interface BaseChartProps {
  title?: string;
  subtitle?: string;
  size?: ChartSize;
  className?: string;
  showLegend?: boolean;
  legendPosition?: ChartLegendPosition;
  height?: number;
  width?: number;
}

// Types for TrustScoreChart
export interface TrustScoreData {
  value: number;
  timestamp: string;
}

interface TrustScoreChartProps extends BaseChartProps {
  data: TrustScoreData[];
  goal?: number;
}

// Types for EarningsChart
export interface EarningsData {
  amount: number;
  timestamp: string;
  category?: string;
}

interface EarningsChartProps extends BaseChartProps {
  data: EarningsData[];
  timeframe?: 'daily' | 'weekly' | 'monthly' | 'yearly';
  showAverage?: boolean;
  currency?: string;
}

// Types for EngagementBarChart
export interface EngagementData {
  label: string;
  value: number;
}

interface EngagementBarChartProps extends BaseChartProps {
  data: EngagementData[];
  valueLabel?: string;
}

// Types for PieChart
export interface PieChartData {
  label: string;
  value: number;
  color?: string;
}

interface PieChartProps extends BaseChartProps {
  data: PieChartData[];
  showValues?: boolean;
  showPercentages?: boolean;
  donut?: boolean;
}

// Trust Score Line Chart
export const TrustScoreChart: React.FC<TrustScoreChartProps> = ({
  data,
  title = 'Trust Score Trend',
  subtitle,
  size = 'medium',
  className = '',
  showLegend = true,
  legendPosition = 'bottom',
  height,
  width,
  goal
}) => {
  // Calculate chart dimensions based on size
  const getChartSize = () => {
    switch (size) {
      case 'small': return { h: height || 150, w: width || 300 };
      case 'medium': return { h: height || 250, w: width || 500 };
      case 'large': return { h: height || 350, w: width || 700 };
      default: return { h: height || 250, w: width || 500 };
    }
  };

  const { h, w } = getChartSize();

  // Find max and min values for scaling
  const maxValue = Math.max(...data.map(item => item.value), goal || 0);
  const minValue = Math.min(...data.map(item => item.value));
  
  // Calculate positions for line chart (simplified)
  const chartPoints = data.map((point, index) => {
    const x = (index / (data.length - 1 || 1)) * (w - 60) + 30;
    const y = h - 40 - ((point.value - minValue) / (maxValue - minValue || 1)) * (h - 80);
    return { x, y, value: point.value, timestamp: point.timestamp };
  });
  
  // Generate a path for the line
  const linePath = chartPoints.length > 1 
    ? `M ${chartPoints.map(p => `${p.x},${p.y}`).join(' L ')}`
    : '';

  return (
    <div className={`chart-container ${className}`} style={{ width: w }}>
      {title && <h3 className="chart-title">{title}</h3>}
      {subtitle && <p className="chart-subtitle">{subtitle}</p>}
      
      <svg width={w} height={h} className="chart trust-score-chart">
        {/* Y Axis */}
        <line x1="30" y1="20" x2="30" y2={h-20} stroke="#ccc" strokeWidth="1" />
        
        {/* X Axis */}
        <line x1="30" y1={h-20} x2={w-30} y2={h-20} stroke="#ccc" strokeWidth="1" />
        
        {/* Goal Line if provided */}
        {goal && (
          <>
            <line 
              x1="30" 
              y1={h - 40 - ((goal - minValue) / (maxValue - minValue || 1)) * (h - 80)} 
              x2={w-30} 
              y2={h - 40 - ((goal - minValue) / (maxValue - minValue || 1)) * (h - 80)} 
              stroke="#ff6b6b" 
              strokeWidth="1" 
              strokeDasharray="5,5" 
            />
            <text 
              x={w-40} 
              y={h - 45 - ((goal - minValue) / (maxValue - minValue || 1)) * (h - 80)} 
              fontSize="12" 
              fill="#ff6b6b"
            >
              Goal
            </text>
          </>
        )}
        
        {/* Line for the chart */}
        {linePath && (
          <path 
            d={linePath} 
            fill="none" 
            stroke="#0066cc" 
            strokeWidth="2" 
          />
        )}
        
        {/* Data points */}
        {chartPoints.map((point, i) => (
          <g key={i} className="data-point">
            <circle 
              cx={point.x} 
              cy={point.y} 
              r="4" 
              fill="#0066cc" 
            />
            {/* Tooltip would go here in a real implementation */}
          </g>
        ))}
        
        {/* Y Axis Labels */}
        <text x="10" y="30" fontSize="12" textAnchor="middle">{maxValue}</text>
        <text x="10" y={h-20} fontSize="12" textAnchor="middle">{minValue}</text>
        
        {/* X Axis Labels - just show first and last for simplicity */}
        {data.length > 0 && (
          <>
            <text x="30" y={h-5} fontSize="10" textAnchor="middle">
              {new Date(data[0].timestamp).toLocaleDateString()}
            </text>
            {data.length > 1 && (
              <text x={w-30} y={h-5} fontSize="10" textAnchor="middle">
                {new Date(data[data.length-1].timestamp).toLocaleDateString()}
              </text>
            )}
          </>
        )}
      </svg>
      
      {showLegend && (
        <div className={`chart-legend legend-${legendPosition}`}>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#0066cc' }}></span>
            <span className="legend-label">Trust Score</span>
          </div>
          {goal && (
            <div className="legend-item">
              <span className="legend-color" style={{ backgroundColor: '#ff6b6b' }}></span>
              <span className="legend-label">Goal</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Weekly Earnings Graph
export const EarningsChart: React.FC<EarningsChartProps> = ({
  data,
  title = 'Earnings Over Time',
  subtitle,
  size = 'medium',
  className = '',
  showLegend = true,
  legendPosition = 'bottom',
  height,
  width,
  timeframe = 'weekly',
  showAverage = false,
  currency = '$'
}) => {
  // Calculate chart dimensions based on size
  const getChartSize = () => {
    switch (size) {
      case 'small': return { h: height || 150, w: width || 300 };
      case 'medium': return { h: height || 250, w: width || 500 };
      case 'large': return { h: height || 350, w: width || 700 };
      default: return { h: height || 250, w: width || 500 };
    }
  };

  const { h, w } = getChartSize();

  // Group data by category if it exists
  const categories = [...new Set(data.map(item => item.category || 'default'))];
  
  // Find max value for scaling
  const maxValue = Math.max(...data.map(item => item.amount));
  
  // Calculate bar width and spacing
  const barWidth = ((w - 60) / data.length) * 0.8;
  const barSpacing = ((w - 60) / data.length) * 0.2;
  
  // Calculate average if needed
  const average = showAverage 
    ? data.reduce((sum, item) => sum + item.amount, 0) / data.length 
    : 0;

  return (
    <div className={`chart-container ${className}`} style={{ width: w }}>
      {title && <h3 className="chart-title">{title}</h3>}
      {subtitle && <p className="chart-subtitle">{subtitle}</p>}
      
      <svg width={w} height={h} className="chart earnings-chart">
        {/* Y Axis */}
        <line x1="40" y1="20" x2="40" y2={h-40} stroke="#ccc" strokeWidth="1" />
        
        {/* X Axis */}
        <line x1="40" y1={h-40} x2={w-20} y2={h-40} stroke="#ccc" strokeWidth="1" />
        
        {/* Average Line if enabled */}
        {showAverage && (
          <>
            <line 
              x1="40" 
              y1={h - 40 - (average / maxValue) * (h - 60)} 
              x2={w-20} 
              y2={h - 40 - (average / maxValue) * (h - 60)} 
              stroke="#ff9800" 
              strokeWidth="1" 
              strokeDasharray="5,5" 
            />
            <text 
              x={w-50} 
              y={h - 45 - (average / maxValue) * (h - 60)} 
              fontSize="12" 
              fill="#ff9800"
            >
              Avg: {currency}{average.toFixed(2)}
            </text>
          </>
        )}
        
        {/* Bars for each data point */}
        {data.map((item, index) => {
          const x = 40 + index * (barWidth + barSpacing);
          const barHeight = (item.amount / maxValue) * (h - 60);
          const y = h - 40 - barHeight;
          
          return (
            <g key={index} className="bar-group">
              <rect 
                x={x} 
                y={y} 
                width={barWidth} 
                height={barHeight} 
                fill="#4caf50" 
              />
              <text 
                x={x + barWidth/2} 
                y={y - 5} 
                fontSize="10" 
                textAnchor="middle"
                fill="#333"
              >
                {currency}{item.amount}
              </text>
              <text 
                x={x + barWidth/2} 
                y={h-25} 
                fontSize="10" 
                textAnchor="middle" 
                transform={`rotate(-45, ${x + barWidth/2}, ${h-25})`}
              >
                {new Date(item.timestamp).toLocaleDateString()}
              </text>
            </g>
          );
        })}
        
        {/* Y Axis Labels */}
        <text x="20" y="30" fontSize="12" textAnchor="middle">{currency}{maxValue}</text>
        <text x="20" y={h-40} fontSize="12" textAnchor="middle">{currency}0</text>
      </svg>
      
      {showLegend && categories.length > 1 && (
        <div className={`chart-legend legend-${legendPosition}`}>
          {categories.map(category => (
            <div key={category} className="legend-item">
              <span className="legend-color" style={{ backgroundColor: category === 'default' ? '#4caf50' : '#2196f3' }}></span>
              <span className="legend-label">{category}</span>
            </div>
          ))}
          {showAverage && (
            <div className="legend-item">
              <span className="legend-line" style={{ backgroundColor: '#ff9800' }}></span>
              <span className="legend-label">Average</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Offer Engagement Bar Chart
export const EngagementBarChart: React.FC<EngagementBarChartProps> = ({
  data,
  title = 'Engagement Metrics',
  subtitle,
  size = 'medium',
  className = '',
  showLegend = false,
  height,
  width,
  valueLabel = 'Count'
}) => {
  // Calculate chart dimensions based on size
  const getChartSize = () => {
    switch (size) {
      case 'small': return { h: height || 150, w: width || 300 };
      case 'medium': return { h: height || 250, w: width || 500 };
      case 'large': return { h: height || 350, w: width || 700 };
      default: return { h: height || 250, w: width || 500 };
    }
  };

  const { h, w } = getChartSize();
  
  // Find max value for scaling
  const maxValue = Math.max(...data.map(item => item.value));
  
  // Calculate bar height and spacing
  const barHeight = ((h - 60) / data.length) * 0.7;
  const barSpacing = ((h - 60) / data.length) * 0.3;

  return (
    <div className={`chart-container ${className}`} style={{ width: w }}>
      {title && <h3 className="chart-title">{title}</h3>}
      {subtitle && <p className="chart-subtitle">{subtitle}</p>}
      
      <svg width={w} height={h} className="chart engagement-chart">
        {/* Y Axis */}
        <line x1="120" y1="20" x2="120" y2={h-20} stroke="#ccc" strokeWidth="1" />
        
        {/* X Axis */}
        <line x1="120" y1={h-20} x2={w-20} y2={h-20} stroke="#ccc" strokeWidth="1" />
        
        {/* Bars for each data point */}
        {data.map((item, index) => {
          const y = 20 + index * (barHeight + barSpacing);
          const barWidth = (item.value / maxValue) * (w - 160);
          
          return (
            <g key={index} className="bar-group">
              <rect 
                x={120} 
                y={y} 
                width={barWidth} 
                height={barHeight} 
                fill="#2196f3" 
              />
              <text 
                x={120 + barWidth + 5} 
                y={y + barHeight/2 + 5} 
                fontSize="12" 
                fill="#333"
              >
                {item.value}
              </text>
              <text 
                x={110} 
                y={y + barHeight/2 + 5} 
                fontSize="12" 
                textAnchor="end" 
                fill="#333"
              >
                {item.label}
              </text>
            </g>
          );
        })}
        
        {/* X Axis Labels */}
        <text x={w/2} y={h-5} fontSize="12" textAnchor="middle">{valueLabel}</text>
        <text x="120" y={h-5} fontSize="12" textAnchor="middle">0</text>
        <text x={w-20} y={h-5} fontSize="12" textAnchor="middle">{maxValue}</text>
      </svg>
    </div>
  );
};

// Pie/Donut Chart
export const PieChart: React.FC<PieChartProps> = ({
  data,
  title = 'Distribution',
  subtitle,
  size = 'medium',
  className = '',
  showLegend = true,
  legendPosition = 'right',
  height,
  width,
  showValues = true,
  showPercentages = true,
  donut = false
}) => {
  // Calculate chart dimensions based on size
  const getChartSize = () => {
    switch (size) {
      case 'small': return { h: height || 200, w: width || 200 };
      case 'medium': return { h: height || 300, w: width || 300 };
      case 'large': return { h: height || 400, w: width || 400 };
      default: return { h: height || 300, w: width || 300 };
    }
  };

  const { h, w } = getChartSize();
  
  // Default colors if not provided
  const defaultColors = [
    '#2196f3', '#4caf50', '#ff9800', '#f44336', '#9c27b0', 
    '#3f51b5', '#00bcd4', '#009688', '#8bc34a', '#ffeb3b'
  ];
  
  // Calculate total for percentages
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  // Create pie segments
  let startAngle = 0;
  const radius = Math.min(w, h) / 2 - 10;
  const innerRadius = donut ? radius * 0.6 : 0;
  const centerX = w / 2;
  const centerY = h / 2;
  
  const segments = data.map((item, index) => {
    const percentage = (item.value / total) * 100;
    const angle = (percentage / 100) * 2 * Math.PI;
    const endAngle = startAngle + angle;
    
    // Calculate SVG arc path
    const x1 = centerX + radius * Math.cos(startAngle);
    const y1 = centerY + radius * Math.sin(startAngle);
    const x2 = centerX + radius * Math.cos(endAngle);
    const y2 = centerY + radius * Math.sin(endAngle);
    
    const largeArcFlag = angle > Math.PI ? 1 : 0;
    
    let path;
    
    if (donut) {
      // For donut chart
      const innerX1 = centerX + innerRadius * Math.cos(startAngle);
      const innerY1 = centerY + innerRadius * Math.sin(startAngle);
      const innerX2 = centerX + innerRadius * Math.cos(endAngle);
      const innerY2 = centerY + innerRadius * Math.sin(endAngle);
      
      path = `
        M ${x1} ${y1}
        A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}
        L ${innerX2} ${innerY2}
        A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${innerX1} ${innerY1}
        Z
      `;
    } else {
      // For pie chart
      path = `
        M ${centerX} ${centerY}
        L ${x1} ${y1}
        A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}
        Z
      `;
    }
    
    // Calculate label position
    const labelAngle = startAngle + angle / 2;
    const labelRadius = radius * 0.7;
    const labelX = centerX + labelRadius * Math.cos(labelAngle);
    const labelY = centerY + labelRadius * Math.sin(labelAngle);
    
    const segment = {
      path,
      color: item.color || defaultColors[index % defaultColors.length],
      label: item.label,
      value: item.value,
      percentage,
      labelX,
      labelY
    };
    
    startAngle = endAngle;
    return segment;
  });

  return (
    <div className={`chart-container ${className}`} style={{ width: w }}>
      {title && <h3 className="chart-title">{title}</h3>}
      {subtitle && <p className="chart-subtitle">{subtitle}</p>}
      
      <div className="pie-chart-wrapper" style={{ display: 'flex', flexDirection: 'row' }}>
        <svg width={w} height={h} className="chart pie-chart">
          {segments.map((segment, i) => (
            <g key={i}>
              <path 
                d={segment.path} 
                fill={segment.color} 
                stroke="#fff" 
                strokeWidth="1"
              />
              {(showValues || showPercentages) && data.length <= 5 && (
                <text 
                  x={segment.labelX} 
                  y={segment.labelY} 
                  fontSize="12" 
                  fill="#fff" 
                  textAnchor="middle"
                >
                  {showValues && showPercentages 
                    ? `${segment.value} (${segment.percentage.toFixed(1)}%)`
                    : showValues 
                      ? segment.value 
                      : `${segment.percentage.toFixed(1)}%`
                  }
                </text>
              )}
            </g>
          ))}
          
          {donut && (
            <circle cx={centerX} cy={centerY} r={innerRadius} fill="#fff" />
          )}
        </svg>
        
        {showLegend && (
          <div className={`chart-legend legend-${legendPosition}`}>
            {segments.map((segment, i) => (
              <div key={i} className="legend-item">
                <span className="legend-color" style={{ backgroundColor: segment.color }}></span>
                <span className="legend-label">
                  {segment.label}
                  {showPercentages && ` (${segment.percentage.toFixed(1)}%)`}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Export the chart components
export default {
  TrustScoreChart,
  EarningsChart,
  EngagementBarChart,
  PieChart
}; 