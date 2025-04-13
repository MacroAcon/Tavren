import { 
  Offer, 
  OfferType, 
  OfferStatus, 
  DataCategory, 
  DataAccessLevel,
  OfferFilters 
} from '../types/offers';

// Mock buyers with varying trust tiers
const mockBuyers = [
  {
    id: 'buyer1',
    name: 'DataCorp Analytics',
    trustTier: 4,
    description: 'Market research and consumer insights company',
    logo: 'https://placehold.co/100x100?text=DC',
    industry: 'Market Research'
  },
  {
    id: 'buyer2',
    name: 'HealthTrack Research',
    trustTier: 5,
    description: 'Medical research organization focused on health outcomes',
    logo: 'https://placehold.co/100x100?text=HTR',
    industry: 'Healthcare'
  },
  {
    id: 'buyer3',
    name: 'Urban Mobility Systems',
    trustTier: 3,
    description: 'Transportation optimization and urban planning',
    logo: 'https://placehold.co/100x100?text=UMS',
    industry: 'Transportation'
  },
  {
    id: 'buyer4',
    name: 'Consumer Preference AI',
    trustTier: 2,
    description: 'AI-powered consumer preference prediction',
    logo: 'https://placehold.co/100x100?text=CPA',
    industry: 'Artificial Intelligence'
  },
  {
    id: 'buyer5',
    name: 'Financial Behavior Insights',
    trustTier: 4,
    description: 'Financial service optimization and customer insights',
    logo: 'https://placehold.co/100x100?text=FBI',
    industry: 'Financial Services'
  }
];

// Generate a set of mock offers
export const mockOffers: Offer[] = [
  // Health data offers
  {
    id: 'offer1',
    title: 'Monthly Fitness Tracking Insights',
    description: 'Share your fitness tracking data to help improve health recommendation algorithms. Your data will help researchers understand patterns in physical activity.',
    type: OfferType.Subscription,
    status: OfferStatus.Active,
    payout: {
      amount: 25,
      currency: 'USD'
    },
    duration: {
      value: 1,
      unit: 'months'
    },
    expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
    buyer: mockBuyers[1],
    dataRequests: [
      {
        category: DataCategory.Medical,
        accessLevel: DataAccessLevel.Basic,
        description: 'Steps, heart rate, and sleep data',
        required: true
      },
      {
        category: DataCategory.Demographics,
        accessLevel: DataAccessLevel.Basic,
        description: 'Age range and general location',
        required: true
      }
    ],
    tags: ['health', 'fitness', 'research'],
    matchScore: 85
  },
  // Consumer preferences offer
  {
    id: 'offer2',
    title: 'Shopping Preferences Survey',
    description: 'One-time survey about your shopping habits and preferences to improve retail experiences.',
    type: OfferType.OneTime,
    status: OfferStatus.Active,
    payout: {
      amount: 15,
      currency: 'USD'
    },
    duration: {
      value: 7,
      unit: 'days'
    },
    expiresAt: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(), // 14 days from now
    createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
    buyer: mockBuyers[0],
    dataRequests: [
      {
        category: DataCategory.Preferences,
        accessLevel: DataAccessLevel.Comprehensive,
        description: 'Shopping preferences and habits',
        required: true
      },
      {
        category: DataCategory.Demographics,
        accessLevel: DataAccessLevel.Basic,
        description: 'Age, income range, and location',
        required: true
      }
    ],
    tags: ['retail', 'shopping', 'preferences'],
    matchScore: 72
  },
  // Financial data offer
  {
    id: 'offer3',
    title: 'Financial Services Research',
    description: 'Share anonymized financial transaction patterns to help improve financial services.',
    type: OfferType.Limited,
    status: OfferStatus.Active,
    payout: {
      amount: 50,
      currency: 'USD'
    },
    duration: {
      value: 3,
      unit: 'months'
    },
    expiresAt: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days from now
    createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
    buyer: mockBuyers[4],
    dataRequests: [
      {
        category: DataCategory.Financial,
        accessLevel: DataAccessLevel.Extended,
        description: 'Transaction categories and patterns (no account numbers or identifying details)',
        required: true
      }
    ],
    tags: ['financial', 'research', 'banking'],
    matchScore: 65
  },
  // Transportation and location data
  {
    id: 'offer4',
    title: 'Urban Mobility Study',
    description: 'Help improve city transportation by sharing your anonymized commute patterns.',
    type: OfferType.Limited,
    status: OfferStatus.Active,
    payout: {
      amount: 30,
      currency: 'USD'
    },
    duration: {
      value: 2,
      unit: 'weeks'
    },
    expiresAt: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(), // 10 days from now
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
    buyer: mockBuyers[2],
    dataRequests: [
      {
        category: DataCategory.Location,
        accessLevel: DataAccessLevel.Extended,
        description: 'Daily travel patterns and transportation methods',
        required: true
      },
      {
        category: DataCategory.Demographics,
        accessLevel: DataAccessLevel.Basic,
        description: 'Age range and household information',
        required: false
      }
    ],
    tags: ['transportation', 'urban', 'commuting'],
    matchScore: 78
  },
  // AI research with preferences
  {
    id: 'offer5',
    title: 'AI Recommendation Improvement',
    description: 'Help train AI to better understand content preferences across entertainment platforms.',
    type: OfferType.Subscription,
    status: OfferStatus.Active,
    payout: {
      amount: 20,
      currency: 'USD'
    },
    duration: {
      value: 1,
      unit: 'months'
    },
    expiresAt: new Date(Date.now() + 20 * 24 * 60 * 60 * 1000).toISOString(), // 20 days from now
    createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), // 5 days ago
    buyer: mockBuyers[3],
    dataRequests: [
      {
        category: DataCategory.Preferences,
        accessLevel: DataAccessLevel.Comprehensive,
        description: 'Entertainment preferences, viewing habits, and content interactions',
        required: true
      },
      {
        category: DataCategory.Behaviors,
        accessLevel: DataAccessLevel.Extended,
        description: 'App usage patterns related to entertainment',
        required: false
      }
    ],
    tags: ['AI', 'entertainment', 'preferences'],
    matchScore: 92
  },
  // Professional data offer
  {
    id: 'offer6',
    title: 'Workplace Productivity Research',
    description: 'Contribute to research on improving workplace productivity and satisfaction.',
    type: OfferType.OneTime,
    status: OfferStatus.Active,
    payout: {
      amount: 40,
      currency: 'USD'
    },
    duration: {
      value: 1,
      unit: 'weeks'
    },
    expiresAt: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(), // 15 days from now
    createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
    buyer: mockBuyers[0],
    dataRequests: [
      {
        category: DataCategory.Professional,
        accessLevel: DataAccessLevel.Extended,
        description: 'Work patterns, tools usage, and productivity metrics',
        required: true
      }
    ],
    tags: ['professional', 'productivity', 'workplace'],
    matchScore: 68
  }
];

// Mock API functions to simulate backend calls
export const getOffers = (filters?: OfferFilters, page: number = 1, limit: number = 10): Promise<{ offers: Offer[], hasMore: boolean }> => {
  return new Promise((resolve) => {
    // Simulate network delay
    setTimeout(() => {
      let filteredOffers = [...mockOffers];
      
      // Apply filters if provided
      if (filters) {
        if (filters.types && filters.types.length > 0) {
          filteredOffers = filteredOffers.filter(offer => 
            filters.types!.includes(offer.type)
          );
        }
        
        if (filters.minPayout !== undefined) {
          filteredOffers = filteredOffers.filter(offer => 
            offer.payout.amount >= filters.minPayout!
          );
        }
        
        if (filters.maxPayout !== undefined) {
          filteredOffers = filteredOffers.filter(offer => 
            offer.payout.amount <= filters.maxPayout!
          );
        }
        
        if (filters.dataCategories && filters.dataCategories.length > 0) {
          filteredOffers = filteredOffers.filter(offer => 
            offer.dataRequests.some(req => 
              filters.dataCategories!.includes(req.category)
            )
          );
        }
        
        if (filters.minTrustTier !== undefined) {
          filteredOffers = filteredOffers.filter(offer => 
            offer.buyer.trustTier >= filters.minTrustTier!
          );
        }
        
        if (filters.search) {
          const searchLower = filters.search.toLowerCase();
          filteredOffers = filteredOffers.filter(offer => 
            offer.title.toLowerCase().includes(searchLower) || 
            offer.description.toLowerCase().includes(searchLower) ||
            offer.tags.some(tag => tag.toLowerCase().includes(searchLower))
          );
        }
        
        if (filters.tags && filters.tags.length > 0) {
          filteredOffers = filteredOffers.filter(offer => 
            filters.tags!.some(tag => offer.tags.includes(tag))
          );
        }
      }
      
      // Sort by match score (if available) or creation date
      filteredOffers.sort((a, b) => {
        if (a.matchScore && b.matchScore) {
          return b.matchScore - a.matchScore;
        }
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
      });
      
      // Paginate
      const startIndex = (page - 1) * limit;
      const endIndex = startIndex + limit;
      const paginatedOffers = filteredOffers.slice(startIndex, endIndex);
      
      resolve({
        offers: paginatedOffers,
        hasMore: endIndex < filteredOffers.length
      });
    }, 500); // Simulate 500ms delay
  });
};

export const getOfferById = (id: string): Promise<Offer | null> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const offer = mockOffers.find(o => o.id === id) || null;
      resolve(offer);
    }, 300);
  });
};

export const getRecommendedOffers = (userId: string, count: number = 3): Promise<Offer[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Sort by match score and take the top 'count'
      const recommended = [...mockOffers]
        .sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0))
        .slice(0, count);
      
      resolve(recommended);
    }, 300);
  });
}; 