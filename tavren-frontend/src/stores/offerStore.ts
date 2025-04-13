import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Offer, OfferFilters, OfferFeedState } from '../types/offers';
import apiClient from '../utils/apiClient';

interface OfferStoreActions {
  // Getters
  getSelectedOffer: () => Offer | null;
  
  // Actions
  fetchOffers: (resetPage?: boolean) => Promise<void>;
  fetchOfferById: (id: string) => Promise<Offer | null>;
  fetchRecommendedOffers: (userId: string, count?: number) => Promise<Offer[]>;
  acceptOffer: (offerId: string) => Promise<boolean>;
  setSelectedOffer: (offer: Offer | null) => void;
  updateFilters: (filters: Partial<OfferFilters>) => void;
  clearFilters: () => void;
  rejectOffer: (offerId: string) => Promise<boolean>;
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
          
          const params = {
            ...get().filters,
            page: get().page,
            limit: 10
          };
          
          const response = await apiClient.get<{
            offers: Offer[],
            pagination: {
              totalCount: number,
              page: number,
              pageSize: number,
              hasMore: boolean
            }
          }>('/offers', { params });
          
          // If page is 1, replace offers. Otherwise, append to existing
          if (get().page === 1) {
            set({ 
              offers: response.offers, 
              hasMore: response.pagination.hasMore, 
              loading: false 
            });
          } else {
            set({ 
              offers: [...get().offers, ...response.offers], 
              hasMore: response.pagination.hasMore, 
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
          const offer = await apiClient.get<Offer>(`/offers/${id}`);
          set({ selectedOffer: offer, loading: false });
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
          const params = { count };
          const recommendations = await apiClient.get<Offer[]>('/offers/recommended', { params });
          return recommendations;
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch recommendations' 
          });
          return [];
        }
      },
      
      acceptOffer: async (offerId: string) => {
        try {
          set({ loading: true });
          const response = await apiClient.post<{ success: boolean }>(`/offers/${offerId}/accept`);
          set({ loading: false });
          return response.success;
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to accept offer',
            loading: false
          });
          return false;
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

      rejectOffer: async (offerId: string) => {
        try {
          await apiClient.post<{ success: boolean }>(`/offers/${offerId}/reject`);
          
          set({ 
            rejectedOfferIds: [...get().rejectedOfferIds, offerId],
            offers: get().offers.filter(offer => offer.id !== offerId)
          });
          return true;
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to reject offer' 
          });
          return false;
        }
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