import React, { useState, useCallback } from 'react';
import { 
  useOfferStore,
  usePreferencesStore,
  notifyInfo 
} from '../../stores';
import { OfferType, DataCategory } from '../../types/offers';
import './offers.css';

const OfferFilters: React.FC = () => {
  const { filters, updateFilters, clearFilters, fetchOffers } = useOfferStore();
  const minimumTrustTier = usePreferencesStore(state => state.minimumTrustTier);
  
  // Local state for filter form
  const [localFilters, setLocalFilters] = useState({
    types: filters.types || [],
    minPayout: filters.minPayout || 0,
    maxPayout: filters.maxPayout || 1000,
    dataCategories: filters.dataCategories || [],
    minTrustTier: filters.minTrustTier || minimumTrustTier,
    search: filters.search || '',
    tags: filters.tags || []
  });
  
  // Local state for tag input
  const [tagInput, setTagInput] = useState('');
  
  // Handle checkbox change for multi-select filters
  const handleMultiSelectChange = useCallback((
    e: React.ChangeEvent<HTMLInputElement>,
    filterName: 'types' | 'dataCategories'
  ) => {
    const { value, checked } = e.target;
    
    setLocalFilters(prev => {
      if (checked) {
        return {
          ...prev,
          [filterName]: [...prev[filterName], value]
        };
      } else {
        return {
          ...prev,
          [filterName]: prev[filterName].filter(item => item !== value)
        };
      }
    });
  }, []);
  
  // Handle change for number inputs
  const handleNumberChange = useCallback((
    e: React.ChangeEvent<HTMLInputElement>,
    filterName: 'minPayout' | 'maxPayout' | 'minTrustTier'
  ) => {
    const value = parseInt(e.target.value);
    setLocalFilters(prev => ({
      ...prev,
      [filterName]: isNaN(value) ? 0 : value
    }));
  }, []);
  
  // Handle search input change
  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setLocalFilters(prev => ({
      ...prev,
      search: e.target.value
    }));
  }, []);
  
  // Handle tag input
  const handleTagInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setTagInput(e.target.value);
  }, []);
  
  // Add tag when Enter is pressed
  const handleTagKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && tagInput.trim() !== '') {
      e.preventDefault();
      setLocalFilters(prev => ({
        ...prev,
        tags: [...new Set([...prev.tags, tagInput.trim().toLowerCase()])]
      }));
      setTagInput('');
    }
  }, [tagInput]);
  
  // Remove tag
  const handleRemoveTag = useCallback((tag: string) => {
    setLocalFilters(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tag)
    }));
  }, []);
  
  // Apply filters
  const handleApplyFilters = useCallback(() => {
    updateFilters(localFilters);
    fetchOffers(true); // true to reset pagination
    notifyInfo('Filters applied');
  }, [updateFilters, fetchOffers, localFilters]);
  
  // Reset filters
  const handleResetFilters = useCallback(() => {
    clearFilters();
    setLocalFilters({
      types: [],
      minPayout: 0,
      maxPayout: 1000,
      dataCategories: [],
      minTrustTier: minimumTrustTier,
      search: '',
      tags: []
    });
    setTagInput('');
    fetchOffers(true);
    notifyInfo('Filters reset');
  }, [clearFilters, fetchOffers, minimumTrustTier]);
  
  return (
    <div className="offer-filters">
      <h2>Filter Offers</h2>
      
      <div className="filter-section">
        <label className="filter-label">Search</label>
        <input
          type="text"
          className="search-input"
          placeholder="Search offers..."
          value={localFilters.search}
          onChange={handleSearchChange}
        />
      </div>
      
      <div className="filter-section">
        <label className="filter-label">Offer Type</label>
        <div className="checkbox-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              value={OfferType.OneTime}
              checked={localFilters.types.includes(OfferType.OneTime)}
              onChange={e => handleMultiSelectChange(e, 'types')}
            />
            One-time
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              value={OfferType.Subscription}
              checked={localFilters.types.includes(OfferType.Subscription)}
              onChange={e => handleMultiSelectChange(e, 'types')}
            />
            Subscription
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              value={OfferType.Limited}
              checked={localFilters.types.includes(OfferType.Limited)}
              onChange={e => handleMultiSelectChange(e, 'types')}
            />
            Limited Time
          </label>
        </div>
      </div>
      
      <div className="filter-section">
        <label className="filter-label">Payout Range</label>
        <div className="range-inputs">
          <div className="range-input-group">
            <label>Min</label>
            <input
              type="number"
              min="0"
              value={localFilters.minPayout}
              onChange={e => handleNumberChange(e, 'minPayout')}
            />
          </div>
          <div className="range-input-group">
            <label>Max</label>
            <input
              type="number"
              min="0"
              value={localFilters.maxPayout}
              onChange={e => handleNumberChange(e, 'maxPayout')}
            />
          </div>
        </div>
      </div>
      
      <div className="filter-section">
        <label className="filter-label">Data Categories</label>
        <div className="checkbox-group">
          {Object.values(DataCategory).map(category => (
            <label key={category} className="checkbox-label">
              <input
                type="checkbox"
                value={category}
                checked={localFilters.dataCategories.includes(category)}
                onChange={e => handleMultiSelectChange(e, 'dataCategories')}
              />
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </label>
          ))}
        </div>
      </div>
      
      <div className="filter-section">
        <label className="filter-label">Minimum Trust Tier</label>
        <div className="trust-tier-slider">
          <input
            type="range"
            min="1"
            max="5"
            value={localFilters.minTrustTier}
            onChange={e => handleNumberChange(e, 'minTrustTier')}
          />
          <div className="trust-tier-value">
            Tier {localFilters.minTrustTier}+
          </div>
        </div>
      </div>
      
      <div className="filter-section">
        <label className="filter-label">Tags</label>
        <div className="tag-input-container">
          <input
            type="text"
            placeholder="Add tag and press Enter"
            value={tagInput}
            onChange={handleTagInputChange}
            onKeyDown={handleTagKeyDown}
          />
        </div>
        <div className="selected-tags">
          {localFilters.tags.map(tag => (
            <span key={tag} className="selected-tag">
              #{tag}
              <button 
                className="remove-tag" 
                onClick={() => handleRemoveTag(tag)}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>
      
      <div className="filter-actions">
        <button 
          className="secondary-button" 
          onClick={handleResetFilters}
        >
          Reset
        </button>
        <button 
          className="primary-button" 
          onClick={handleApplyFilters}
        >
          Apply Filters
        </button>
      </div>
    </div>
  );
};

export default OfferFilters; 