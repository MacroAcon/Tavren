// Mock data service for the Your Data at Work widget

interface DataImpactCategory {
  id: string;
  name: string;
  description: string;
}

export interface DataImpactMetric {
  value: string;
  label: string;
}

export interface DataImpactData {
  category: DataImpactCategory;
  headline: string;
  subtext: string;
  metrics: DataImpactMetric[];
  privacyReminder: string;
}

const impactCategories: DataImpactCategory[] = [
  {
    id: 'health',
    name: 'Health',
    description: 'Medical research and healthcare improvements'
  },
  {
    id: 'retail',
    name: 'Retail',
    description: 'Shopping experiences and consumer products'
  },
  {
    id: 'transportation',
    name: 'Transportation',
    description: 'Urban planning and mobility services'
  },
  {
    id: 'finance',
    name: 'Finance',
    description: 'Financial services and product development'
  }
];

export const getRandomDataImpact = (): DataImpactData => {
  // Randomly select a category
  const category = impactCategories[Math.floor(Math.random() * impactCategories.length)];
  
  // Configure content based on category
  let headline = '';
  let subtext = '';
  
  switch(category.id) {
    case 'health':
      headline = `Your Data Helped Power 3 Health Innovations This Week`;
      subtext = `Healthcare researchers used anonymous insights to improve patient experience design`;
      break;
    case 'retail':
      headline = `Your Insights Shaped Product Improvements`;
      subtext = `Retailers refined shopping experiences based on community preferences`;
      break;
    case 'transportation':
      headline = `Your Contributions Influenced Transportation Planning`;
      subtext = `Urban planners applied community knowledge to make public spaces more accessible`;
      break;
    case 'finance':
      headline = `Your Data Helped Create More Inclusive Financial Tools`;
      subtext = `Financial services created more inclusive products using collective feedback`;
      break;
  }
  
  // Generate some random metrics
  const communitySize = Math.floor(Math.random() * 20000) + 5000;
  const foundHelpful = Math.floor(Math.random() * 20) + 75; // 75-95%
  
  return {
    category,
    headline,
    subtext,
    metrics: [
      { value: communitySize.toLocaleString(), label: 'Community Members' },
      { value: `${foundHelpful}%`, label: 'Found Helpful' }
    ],
    privacyReminder: 'All insights are privacy-protected and shared with your permission'
  };
};

export const getDataImpactByCategory = (categoryId: string): DataImpactData | null => {
  const category = impactCategories.find(c => c.id === categoryId);
  if (!category) return null;
  
  // Configure content based on category
  let headline = '';
  let subtext = '';
  
  switch(category.id) {
    case 'health':
      headline = `Your Data Helped Power 3 Health Innovations This Week`;
      subtext = `Healthcare researchers used anonymous insights to improve patient experience design`;
      break;
    case 'retail':
      headline = `Your Insights Shaped Product Improvements`;
      subtext = `Retailers refined shopping experiences based on community preferences`;
      break;
    case 'transportation':
      headline = `Your Contributions Influenced Transportation Planning`;
      subtext = `Urban planners applied community knowledge to make public spaces more accessible`;
      break;
    case 'finance':
      headline = `Your Data Helped Create More Inclusive Financial Tools`;
      subtext = `Financial services created more inclusive products using collective feedback`;
      break;
  }
  
  // Generate some random metrics
  const communitySize = Math.floor(Math.random() * 20000) + 5000;
  const foundHelpful = Math.floor(Math.random() * 20) + 75; // 75-95%
  
  return {
    category,
    headline,
    subtext,
    metrics: [
      { value: communitySize.toLocaleString(), label: 'Community Members' },
      { value: `${foundHelpful}%`, label: 'Found Helpful' }
    ],
    privacyReminder: 'All insights are privacy-protected and shared with your permission'
  };
}; 