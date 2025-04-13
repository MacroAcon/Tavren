import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Offer, OfferFilters, OfferFeedState } from '../types/offers';
import { getOffers, getOfferById, getRecommendedOffers } from '../mock/offerService';

interface OfferStoreActions {
  // Getters
  getSelectedOffer: () => Offer | null;
  
  // Actions
  fetchOffers: (resetPage?: boolean) => Promise<void>;
  fetchOfferById: (id: string) => Promise<Offer | null>;
  fetchRecommendedOffers: (userId: string, count?: number) => Promise<Offer[]>;
  setSelectedOffer: (offer: Offer | null) => void;
  updateFilters: (filters: Partial<OfferFilters>) => void;
  clearFilters: () => void;
  rejectOffer: (offerId: string) => void;
  nextPage: () => void;
  resetPage: () => void;
}

type OfferStore = OfferFeedState & OfferStoreActions;

// Define initial state
const initialState: OfferFeedState = {
  offers: [],
  selectedOffer: null,
  filters: {},
  rejectedOfferIds: [],
  loading: false,
  error: null,
  page: 1,
  hasMore: true
};

// Create offer store with Zustand
export const useOfferStore = create<OfferStore>()(
  devtools(
    (set, get) => ({
      ...initialState,

      // Getters
      getSelectedOffer: () => get().selectedOffer,

      // Actions
      fetchOffers: async (resetPage = false) => {
        try {
          set({ loading: true, error: null });
          
          // If resetPage is true, reset to page 1
          if (resetPage) {
            set({ page: 1 });
          }
          
          const { offers, hasMore } = await getOffers(
            get().filters, 
            get().page, 
            10 // Page size
          );
          
          // If page is 1, replace offers. Otherwise, append to existing
          if (get().page === 1) {
            set({ offers, hasMore, loading: false });
          } else {
            set({ 
              offers: [...get().offers, ...offers], 
              hasMore, 
              loading: false 
            });
          }
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch offers', 
            loading: false 
          });
        }
      },

      fetchOfferById: async (id: string) => {
        try {
          set({ loading: true, error: null });
          const offer = await getOfferById(id);
          if (offer) {
            set({ selectedOffer: offer });
          }
          set({ loading: false });
          return offer;
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch offer', 
            loading: false 
          });
          return null;
        }
      },

      fetchRecommendedOffers: async (userId: string, count = 3) => {
        try {
          const recommendations = await getRecommendedOffers(userId, count);
          return recommendations;
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch recommendations' 
          });
          return [];
        }
      },

      setSelectedOffer: (offer: Offer | null) => {
        set({ selectedOffer: offer });
      },

      updateFilters: (filters: Partial<OfferFilters>) => {
        set({ 
          filters: { ...get().filters, ...filters },
          page: 1 // Reset to first page when filters change
        });
      },

      clearFilters: () => {
        set({ filters: {}, page: 1 });
      },

      rejectOffer: (offerId: string) => {
        set({ 
          rejectedOfferIds: [...get().rejectedOfferIds, offerId],
          offers: get().offers.filter(offer => offer.id !== offerId)
        });
      },

      nextPage: () => {
        set({ page: get().page + 1 });
      },

      resetPage: () => {
        set({ page: 1 });
      }
    })
  )
); 