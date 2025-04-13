import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useOfferStore } from '../../stores';
import './offers.css';
import OfferCard from './OfferCard';
import LoadingState from '../shared/LoadingState';
import ErrorState from '../shared/ErrorState';

const OffersPage: React.FC = () => {
  const { 
    offers, 
    isLoading, 
    error, 
    fetchOffers,
    applyFilters,
    clearFilters
  } = useOfferStore();

  // Mobile filter collapse state
  const [filtersCollapsed, setFiltersCollapsed] = useState(window.innerWidth < 768);

  // Filter states
  const [searchQuery, setSearchQuery] = useState('');
  const [offerTypes, setOfferTypes] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [minPayout, setMinPayout] = useState<number | ''>('');
  const [maxPayout, setMaxPayout] = useState<number | ''>('');
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [sortOrder, setSortOrder] = useState('newest');

  useEffect(() => {
    fetchOffers().catch(err => console.error('Failed to fetch offers:', err));
  }, [fetchOffers]);

  // Handle window resize events to set initial collapse state
  useEffect(() => {
    const handleResize = () => {
      setFiltersCollapsed(window.innerWidth < 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleOfferTypeChange = (type: string) => {
    setOfferTypes(prev => {
      if (prev.includes(type)) {
        return prev.filter(t => t !== type);
      } else {
        return [...prev, type];
      }
    });
  };

  const handleCategoryChange = (category: string) => {
    setCategories(prev => {
      if (prev.includes(category)) {
        return prev.filter(c => c !== category);
      } else {
        return [...prev, category];
      }
    });
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags(prev => [...prev, tagInput.trim()]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tag: string) => {
    setTags(prev => prev.filter(t => t !== tag));
  };

  const handleTagInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  const handleFilter = () => {
    applyFilters({
      searchQuery,
      offerTypes,
      categories,
      minPayout: minPayout === '' ? undefined : minPayout,
      maxPayout: maxPayout === '' ? undefined : maxPayout,
      tags,
      sortOrder
    });
  };

  const handleClear = () => {
    setSearchQuery('');
    setOfferTypes([]);
    setCategories([]);
    setMinPayout('');
    setMaxPayout('');
    setTags([]);
    setSortOrder('newest');
    clearFilters();
  };

  const toggleFilters = () => {
    setFiltersCollapsed(!filtersCollapsed);
  };

  if (isLoading) {
    return <LoadingState message="Loading offers..." />;
  }

  if (error) {
    return <ErrorState 
      message={`Error loading offers: ${error}`} 
      onRetry={fetchOffers}
    />;
  }

  return (
    <div className="offers-page">
      <h1>Data Offers</h1>
      <p className="offers-description">
        Browse available data sharing opportunities from trusted partners. 
        Find offers that match your privacy preferences and compensation requirements.
      </p>

      <div className="offers-container">
        <aside className="offers-sidebar">
          {/* Mobile filter toggle button */}
          <button 
            className="filter-collapse-toggle"
            onClick={toggleFilters}
            aria-expanded={!filtersCollapsed}
          >
            <span>Filters</span>
            <span className="toggle-icon">{filtersCollapsed ? '▼' : '▲'}</span>
          </button>
          
          <div className="offer-filters" data-collapsed={filtersCollapsed}>
            <h2>Filter Offers</h2>
            
            <div className="filter-section">
              <label className="filter-label">Search</label>
              <input 
                type="text" 
                className="search-input" 
                placeholder="Search offers..."
                value={searchQuery}
                onChange={handleSearchChange}
              />
            </div>
            
            <div className="filter-section">
              <label className="filter-label">Offer Type</label>
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input 
                    type="checkbox"
                    checked={offerTypes.includes('one_time')}
                    onChange={() => handleOfferTypeChange('one_time')}
                  />
                  One-time
                </label>
                <label className="checkbox-label">
                  <input 
                    type="checkbox"
                    checked={offerTypes.includes('subscription')}
                    onChange={() => handleOfferTypeChange('subscription')}
                  />
                  Subscription
                </label>
                <label className="checkbox-label">
                  <input 
                    type="checkbox"
                    checked={offerTypes.includes('limited')}
                    onChange={() => handleOfferTypeChange('limited')}
                  />
                  Limited Time
                </label>
              </div>
            </div>
            
            <div className="filter-section">
              <label className="filter-label">Data Categories</label>
              <div className="checkbox-group">
                <label className="checkbox-label">
                  <input 
                    type="checkbox"
                    checked={categories.includes('location')}
                    onChange={() => handleCategoryChange('location')}
                  />
                  Location
                </label>
                <label className="checkbox-label">
                  <input 
                    type="checkbox"
                    checked={categories.includes('browsing')}
                    onChange={() => handleCategoryChange('browsing')}
                  />
                  Browsing History
                </label>
                <label className="checkbox-label">
                  <input 
                    type="checkbox"
                    checked={categories.includes('purchase')}
                    onChange={() => handleCategoryChange('purchase')}
                  />
                  Purchase History
                </label>
                <label className="checkbox-label">
                  <input 
                    type="checkbox"
                    checked={categories.includes('demographic')}
                    onChange={() => handleCategoryChange('demographic')}
                  />
                  Demographic
                </label>
                <label className="checkbox-label">
                  <input 
                    type="checkbox"
                    checked={categories.includes('app_usage')}
                    onChange={() => handleCategoryChange('app_usage')}
                  />
                  App Usage
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
                    value={minPayout}
                    onChange={(e) => setMinPayout(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    min="0"
                    step="0.01"
                  />
                </div>
                <div className="range-input-group">
                  <label>Max</label>
                  <input 
                    type="number"
                    value={maxPayout}
                    onChange={(e) => setMaxPayout(e.target.value === '' ? '' : parseFloat(e.target.value))}
                    min="0"
                    step="0.01"
                  />
                </div>
              </div>
            </div>
            
            <div className="filter-section">
              <label className="filter-label">Tags</label>
              <div className="tag-input-container">
                <input 
                  type="text"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyDown={handleTagInputKeyDown}
                  placeholder="Add tags..."
                />
                <button onClick={handleAddTag}>Add</button>
              </div>
              
              {tags.length > 0 && (
                <div className="selected-tags">
                  {tags.map(tag => (
                    <div key={tag} className="selected-tag">
                      <span>{tag}</span>
                      <button className="remove-tag" onClick={() => handleRemoveTag(tag)}>×</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <div className="filter-section">
              <label className="filter-label">Sort By</label>
              <select
                className="sort-select"
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value)}
              >
                <option value="newest">Newest First</option>
                <option value="oldest">Oldest First</option>
                <option value="highest_pay">Highest Payout</option>
                <option value="lowest_pay">Lowest Payout</option>
                <option value="best_match">Best Match</option>
              </select>
            </div>
            
            <div className="filter-actions">
              <button onClick={handleFilter} className="btn-primary">Apply Filters</button>
              <button onClick={handleClear} className="btn-secondary">Clear All</button>
            </div>
          </div>
        </aside>
        
        <main className="offers-main">
          <div className="offer-feed">
            {offers.length === 0 ? (
              <div className="no-offers">
                <h3>No offers found</h3>
                <p>Try adjusting your filters to see more offers.</p>
              </div>
            ) : (
              <div className="offer-grid">
                {offers.map(offer => (
                  <Link to={`/offers/${offer.id}`} key={offer.id} style={{ textDecoration: 'none' }}>
                    <OfferCard offer={offer} />
                  </Link>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
};

export default OffersPage; 