import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import './mobile-navigation.css';

interface MobileNavigationProps {
  onLogout: () => void;
}

const MobileNavigation: React.FC<MobileNavigationProps> = ({ onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  // Close drawer when route changes
  useEffect(() => {
    setIsOpen(false);
  }, [location.pathname]);

  // Lock body scroll when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const toggleDrawer = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* Mobile Header */}
      <div className="mobile-header">
        <button 
          className="hamburger-button" 
          onClick={toggleDrawer}
          aria-label="Menu"
          aria-expanded={isOpen}
        >
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
        </button>
        <div className="mobile-header-title">Tavren</div>
      </div>

      {/* Navigation Drawer */}
      <div className={`mobile-drawer ${isOpen ? 'open' : ''}`}>
        <div className="drawer-header">
          <div className="drawer-title">Menu</div>
          <button 
            className="drawer-close" 
            onClick={toggleDrawer}
            aria-label="Close menu"
          >
            &times;
          </button>
        </div>

        <nav className="drawer-nav">
          <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
            <span className="nav-icon">🏠</span>
            Dashboard
          </Link>
          <Link to="/offers" className={location.pathname.startsWith('/offers') ? 'active' : ''}>
            <span className="nav-icon">🔍</span>
            Offers
          </Link>
          <Link to="/wallet" className={location.pathname.startsWith('/wallet') ? 'active' : ''}>
            <span className="nav-icon">💰</span>
            Wallet
          </Link>
          <Link to="/profile" className={location.pathname.startsWith('/profile') ? 'active' : ''}>
            <span className="nav-icon">👤</span>
            Profile
          </Link>
          <Link to="/consent" className={location.pathname === '/consent' ? 'active' : ''}>
            <span className="nav-icon">🔐</span>
            Consent
          </Link>
          <Link to="/data-packages" className={location.pathname === '/data-packages' ? 'active' : ''}>
            <span className="nav-icon">📦</span>
            Data Packages
          </Link>
          <Link to="/trust" className={location.pathname === '/trust' ? 'active' : ''}>
            <span className="nav-icon">🔒</span>
            Trust
          </Link>
          <Link to="/agent-interactions" className={location.pathname === '/agent-interactions' ? 'active' : ''}>
            <span className="nav-icon">🤖</span>
            Agents
          </Link>
          <Link to="/agent-exchanges" className={location.pathname.startsWith('/agent-exchanges') ? 'active' : ''}>
            <span className="nav-icon">💬</span>
            Exchanges
          </Link>
        </nav>

        <div className="drawer-footer">
          <button onClick={onLogout} className="logout-button">
            <span className="nav-icon">🚪</span>
            Logout
          </button>
        </div>
      </div>

      {/* Bottom Navigation for quick access */}
      <div className="bottom-nav">
        <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
          <span className="bottom-nav-icon">🏠</span>
          <span className="bottom-nav-label">Home</span>
        </Link>
        <Link to="/offers" className={location.pathname.startsWith('/offers') ? 'active' : ''}>
          <span className="bottom-nav-icon">🔍</span>
          <span className="bottom-nav-label">Offers</span>
        </Link>
        <Link to="/wallet" className={location.pathname.startsWith('/wallet') ? 'active' : ''}>
          <span className="bottom-nav-icon">💰</span>
          <span className="bottom-nav-label">Wallet</span>
        </Link>
        <Link to="/profile" className={location.pathname.startsWith('/profile') ? 'active' : ''}>
          <span className="bottom-nav-icon">👤</span>
          <span className="bottom-nav-label">Profile</span>
        </Link>
      </div>

      {/* Backdrop to close drawer when clicked outside */}
      {isOpen && (
        <div 
          className="drawer-backdrop"
          onClick={toggleDrawer}
          aria-hidden="true"
        ></div>
      )}
    </>
  );
};

export default MobileNavigation; 