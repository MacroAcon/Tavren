import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export enum OnboardingStep {
  Introduction = 0,
  Scanning = 1,
  Results = 2,
  Offer = 3,
  Complete = 4
}

interface OnboardingState {
  // Completion status
  isCompleted: boolean;
  setCompleted: (completed: boolean) => void;
  
  // Current step in the onboarding flow
  currentStep: OnboardingStep;
  nextStep: () => void;
  previousStep: () => void;
  goToStep: (step: OnboardingStep) => void;
  
  // Data collected during onboarding
  scanResults: {
    trackerCount: number;
    appCount: number;
    dataCategories: number;
  } | null;
  setScanResults: (results: OnboardingState['scanResults']) => void;
  
  // Reset all onboarding state
  resetOnboarding: () => void;
}

const initialScanResults = {
  trackerCount: 0,
  appCount: 0,
  dataCategories: 0
};

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      // Completion status
      isCompleted: false,
      setCompleted: (completed) => set({ isCompleted: completed }),
      
      // Current step
      currentStep: OnboardingStep.Introduction,
      nextStep: () => 
        set((state) => ({
          currentStep: Math.min(state.currentStep + 1, OnboardingStep.Complete) as OnboardingStep,
          // Mark as completed when reaching the Complete step
          isCompleted: state.currentStep + 1 >= OnboardingStep.Complete ? true : state.isCompleted
        })),
      previousStep: () => 
        set((state) => ({
          currentStep: Math.max(state.currentStep - 1, OnboardingStep.Introduction) as OnboardingStep
        })),
      goToStep: (step) => set({ currentStep: step }),
      
      // Scan results
      scanResults: null,
      setScanResults: (results) => set({ scanResults: results }),
      
      // Reset onboarding
      resetOnboarding: () => 
        set({
          isCompleted: false,
          currentStep: OnboardingStep.Introduction,
          scanResults: null
        })
    }),
    {
      name: 'tavren-onboarding-storage', // localStorage key
      partialize: (state) => ({
        isCompleted: state.isCompleted,
        scanResults: state.scanResults
      }) // Only persist completion status and scan results, not current step
    }
  )
);

// Selector functions
export const selectIsOnboardingCompleted = (state: OnboardingState) => state.isCompleted;
export const selectCurrentStep = (state: OnboardingState) => state.currentStep;
export const selectScanResults = (state: OnboardingState) => state.scanResults; 