import React from 'react';
import { Link, useLocation } from 'react-router-dom';

function Header({ user, onShowAuth, onLogout }) {
  const location = useLocation();

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">M</span>
            </div>
            <span className="text-2xl font-bold text-gray-900">Manuscriptify</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            {user && (
              <>
                <Link 
                  to="/dashboard" 
                  className={`text-gray-600 hover:text-gray-900 font-medium transition-colors ${
                    location.pathname === '/dashboard' ? 'text-blue-600' : ''
                  }`}
                >
                  Dashboard
                </Link>
                <Link 
                  to="/create" 
                  className={`text-gray-600 hover:text-gray-900 font-medium transition-colors ${
                    location.pathname === '/create' ? 'text-blue-600' : ''
                  }`}
                >
                  Create Project
                </Link>
                {user.subscription_tier === 'admin' && (
                  <Link 
                    to="/admin" 
                    className={`text-gray-600 hover:text-gray-900 font-medium transition-colors ${
                      location.pathname === '/admin' ? 'text-blue-600' : ''
                    }`}
                  >
                    Admin
                  </Link>
                )}
              </>
            )}
          </nav>

          {/* User Actions */}
          <div className="flex items-center space-x-4">
            {user ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 font-semibold text-sm">
                      {user.full_name?.charAt(0) || user.email?.charAt(0)}
                    </span>
                  </div>
                  <span className="text-gray-700 font-medium hidden sm:block">
                    {user.full_name || user.email}
                  </span>
                  <span className="text-xs bg-blue-100 text-blue-600 px-2 py-1 rounded-full">
                    {user.subscription_tier || 'free'}
                  </span>
                </div>
                <button
                  onClick={onLogout}
                  className="text-gray-500 hover:text-gray-700 font-medium transition-colors"
                >
                  Logout
                </button>
              </div>
            ) : (
              <button
                onClick={onShowAuth}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-semibold transition-colors"
                data-testid="login-btn"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;