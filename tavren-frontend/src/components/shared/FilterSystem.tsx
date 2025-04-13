import React, { useState, useEffect, useRef } from 'react';
import './shared-components.css';

// Types for filter options
export type FilterOption = {
  id: string;
  label: string;
  value: string;
};

export type FilterGroup = {
  id: string;
  label: string;
  type: 'dropdown' | 'tags' | 'radio';
  options: FilterOption[];
  multiSelect?: boolean;
};

export type FilterConfig = {
  groups: FilterGroup[];
};

export type FilterSelections = {
  [groupId: string]: string[] | string | null;
};

interface FilterSystemProps {
  filters: FilterGroup[];
  onFilterChange: (filterId: string, selectedValues: string[]) => void;
  activeFilters?: Record<string, string[]>;
  className?: string;
}

const FilterSystem: React.FC<FilterSystemProps> = ({
  filters,
  onFilterChange,
  activeFilters = {},
  className = '',
}) => {
  const [selectedFilters, setSelectedFilters] = useState<Record<string, string[]>>(activeFilters);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const dropdownRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    setSelectedFilters(activeFilters);
  }, [activeFilters]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (openDropdown && dropdownRefs.current[openDropdown] && 
          !dropdownRefs.current[openDropdown]?.contains(event.target as Node)) {
        setOpenDropdown(null);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [openDropdown]);

  const toggleDropdown = (filterId: string) => {
    setOpenDropdown(openDropdown === filterId ? null : filterId);
  };

  const toggleOption = (filterId: string, optionValue: string, multiSelect: boolean = false) => {
    setSelectedFilters(prevFilters => {
      const currentSelected = prevFilters[filterId] || [];
      let newSelected: string[];
      
      if (multiSelect) {
        // For multi-select, toggle the option
        newSelected = currentSelected.includes(optionValue)
          ? currentSelected.filter(v => v !== optionValue)
          : [...currentSelected, optionValue];
      } else {
        // For single-select, replace the selection
        newSelected = currentSelected.includes(optionValue) ? [] : [optionValue];
      }
      
      // Call the parent's filter change handler
      onFilterChange(filterId, newSelected);
      
      return {
        ...prevFilters,
        [filterId]: newSelected
      };
    });
    
    // Close dropdown after selection for better UX (except for multi-select)
    if (!multiSelect) {
      setOpenDropdown(null);
    }
  };

  const removeTag = (filterId: string, optionValue: string) => {
    setSelectedFilters(prevFilters => {
      const newSelected = (prevFilters[filterId] || []).filter(v => v !== optionValue);
      
      // Call the parent's filter change handler
      onFilterChange(filterId, newSelected);
      
      return {
        ...prevFilters,
        [filterId]: newSelected
      };
    });
  };

  const renderFilterContent = (filter: FilterGroup) => {
    const selected = selectedFilters[filter.id] || [];
    
    switch (filter.type) {
      case 'dropdown':
        return (
          <div 
            className="filter-dropdown"
            ref={el => (dropdownRefs.current[filter.id] = el)}
          >
            <button 
              className="filter-dropdown-toggle"
              onClick={() => toggleDropdown(filter.id)}
              aria-expanded={openDropdown === filter.id}
              aria-haspopup="listbox"
            >
              {filter.label} {selected.length > 0 && `(${selected.length})`}
              <span className="filter-dropdown-arrow">▼</span>
            </button>
            {openDropdown === filter.id && (
              <div className="filter-dropdown-menu" role="listbox">
                {filter.options.map(option => (
                  <div 
                    key={option.id}
                    className={`filter-dropdown-item ${selected.includes(option.value) ? 'selected' : ''}`}
                    onClick={() => toggleOption(filter.id, option.value, filter.multiSelect)}
                    role="option"
                    aria-selected={selected.includes(option.value)}
                  >
                    {filter.multiSelect && (
                      <span className="filter-checkbox">
                        {selected.includes(option.value) ? '✓' : ''}
                      </span>
                    )}
                    {option.label}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
        
      case 'tags':
        return (
          <div className="filter-tags-container">
            <span className="filter-tags-label">{filter.label}:</span>
            <div className="filter-tags-options">
              {filter.options.map(option => (
                <div 
                  key={option.id} 
                  className={`filter-tag ${selected.includes(option.value) ? 'selected' : ''}`}
                  onClick={() => toggleOption(filter.id, option.value, true)}
                >
                  {option.label}
                </div>
              ))}
            </div>
          </div>
        );
        
      case 'radio':
        return (
          <div className="filter-radio-group">
            <span className="filter-radio-label">{filter.label}:</span>
            <div className="filter-radio-options">
              {filter.options.map(option => (
                <label key={option.id} className="filter-radio-option">
                  <input
                    type="radio"
                    name={filter.id}
                    checked={selected.includes(option.value)}
                    onChange={() => toggleOption(filter.id, option.value)}
                  />
                  <span className="filter-radio-text">{option.label}</span>
                </label>
              ))}
            </div>
          </div>
        );
        
      default:
        return null;
    }
  };

  const renderActiveFilters = () => {
    const activeFilterCount = Object.values(selectedFilters).reduce(
      (count, values) => count + values.length, 0
    );
    
    if (activeFilterCount === 0) return null;
    
    return (
      <div className="active-filters">
        <div className="active-filters-header">
          <span>Active filters:</span>
          <button 
            className="clear-all-filters"
            onClick={() => {
              // Clear all filters
              const emptyFilters: Record<string, string[]> = {};
              filters.forEach(filter => {
                emptyFilters[filter.id] = [];
                onFilterChange(filter.id, []);
              });
              setSelectedFilters(emptyFilters);
            }}
          >
            Clear all
          </button>
        </div>
        <div className="active-filter-tags">
          {filters.map(filter => {
            const selected = selectedFilters[filter.id] || [];
            if (selected.length === 0) return null;
            
            return selected.map(value => {
              const option = filter.options.find(opt => opt.value === value);
              if (!option) return null;
              
              return (
                <div key={`${filter.id}-${value}`} className="active-filter-tag">
                  <span className="active-filter-name">{filter.label}: {option.label}</span>
                  <button 
                    className="remove-filter"
                    onClick={() => removeTag(filter.id, value)}
                    aria-label={`Remove ${option.label} filter`}
                  >
                    ✕
                  </button>
                </div>
              );
            });
          })}
        </div>
      </div>
    );
  };
  
  return (
    <div className={`filter-system ${className}`}>
      <div className="filter-controls">
        {filters.map(filter => (
          <div key={filter.id} className="filter-group">
            {renderFilterContent(filter)}
          </div>
        ))}
      </div>
      {renderActiveFilters()}
    </div>
  );
};

export default FilterSystem; 