import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';

// Component imports
import Header from '@/components/Header';
import Dashboard from '@/components/Dashboard';
import ProjectCreator from '@/components/ProjectCreator';
import ProjectEditor from '@/components/ProjectEditor';
import ProgressTracker from '@/components/ProgressTracker';
import AdminPanel from '@/components/AdminPanel';
import AuthModal from '@/components/AuthModal';
import { Toaster } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios defaults
axios.defaults.baseURL = BACKEND_URL;

// User context
const UserContext = React.createContext();

// Main App component
function App() {
  const [user, setUser] = useState(null);
  const [showAuth, setShowAuth] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing user session
    const savedUser = localStorage.getItem('manuscriptify_user');
    if (savedUser) {
      const userData = JSON.parse(savedUser);
      setUser(userData);
      // Set default Authorization header for existing user
      if (userData.access_token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${userData.access_token}`;
      }
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('manuscriptify_user', JSON.stringify(userData));
    // Set default Authorization header for all axios requests
    if (userData.access_token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${userData.access_token}`;
    }
    setShowAuth(false);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('manuscriptify_user');
    // Remove Authorization header
    delete axios.defaults.headers.common['Authorization'];
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Manuscriptify...</p>
        </div>
      </div>
    );
  }

  return (
    <UserContext.Provider value={{ user, setUser: handleLogin, logout: handleLogout }}>
      <Router>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
          <Header user={user} onShowAuth={() => setShowAuth(true)} onLogout={handleLogout} />
          
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={user ? <Navigate to="/dashboard" /> : <LandingPage onShowAuth={() => setShowAuth(true)} isAuthenticated={!!user} user={user} />} />
              <Route 
                path="/dashboard" 
                element={user ? <Dashboard /> : <Navigate to="/" />} 
              />
              <Route 
                path="/create" 
                element={user ? <ProjectCreator /> : <Navigate to="/" />} 
              />
              <Route 
                path="/project/:projectId" 
                element={user ? <ProjectEditor /> : <Navigate to="/" />} 
              />
              <Route 
                path="/progress/:projectId" 
                element={user ? <ProgressTracker /> : <Navigate to="/" />} 
              />
              <Route 
                path="/admin" 
                element={user?.subscription_tier === 'admin' ? <AdminPanel /> : <Navigate to="/" />} 
              />
            </Routes>
          </main>

          {showAuth && (
            <AuthModal 
              onClose={() => setShowAuth(false)}
              onLogin={handleLogin}
            />
          )}

          <Toaster position="top-right" richColors />
        </div>
      </Router>
    </UserContext.Provider>
  );
}

// Dynamic Pricing Component
function DynamicPricing({ onShowAuth, isAuthenticated, user }) {
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSubscriptionPlans();
  }, []);

  const fetchSubscriptionPlans = async () => {
    try {
      const response = await axios.get('/api/subscription-plans');
      setSubscriptionPlans(response.data);
    } catch (error) {
      console.error('Failed to fetch subscription plans:', error);
      toast.error('Failed to load pricing plans');
    } finally {
      setLoading(false);
    }
  };

  const handlePlanSelection = async (plan) => {
    if (!isAuthenticated) {
      onShowAuth();
      return;
    }

    try {
      const response = await axios.post('/api/payments/create-subscription', {
        plan_id: plan.id
      });
      
      // Redirect to Stripe Checkout
      window.location.href = response.data.checkout_url;
    } catch (error) {
      console.error('Failed to create subscription:', error);
      toast.error('Failed to process payment. Please try again.');
    }
  };

  const formatPlanFeatures = (plan) => {
    // Parse features JSON string if needed with error handling
    let features = {};
    try {
      features = typeof plan.features === 'string' ? JSON.parse(plan.features) : (plan.features || {});
    } catch (error) {
      console.error('Failed to parse plan features:', error);
      features = {};
    }
    const featureList = [];

    if (features.books_per_month) {
      if (features.pick_n_mix_books && features.audiobooks_per_month) {
        featureList.push(`✔️ ${features.books_per_month} Books/month (${features.pick_n_mix_books} Pick n' Mix + ${features.audiobooks_per_month} AudioBook)`);
      } else if (features.audiobooks_per_month) {
        featureList.push(`✅ Generate ${features.books_per_month} Books Monthly + ${features.audiobooks_per_month} Audiobooks`);
      } else {
        featureList.push(`✔️ ${features.books_per_month} Books/month`);
      }
    }

    if (features.ai_image_credits) {
      featureList.push(`✔️ ${features.ai_image_credits} AI image credits/month`);
    }

    if (features.marketing_tasks) {
      featureList.push(`✔️ ${features.marketing_tasks} marketing task generations/month`);
    }

    if (features.book_cover_generator) {
      featureList.push(`✅ Book Cover Generator Access`);
    }

    if (features.all_features || features.lifetime_updates) {
      featureList.push(`✔️ All features unlocked + lifetime updates`);
    }

    if (features.priority_support || features.premium_support) {
      featureList.push(`✔️ Priority support`);
    }

    if (features.onboarding) {
      featureList.push(`✔️ Premium support + 1-on-1 onboarding`);
    }

    if (features.dedicated_onboarding) {
      featureList.push(`✔️ Priority support + dedicated onboarding`);
    }

    if (features.exclusive_content) {
      featureList.push(`✔️ Access to all courses + exclusive content`);
    }

    if (features.free_trial) {
      featureList.push(`✔️ Free 1 Chapter Trial Generation`);
    }

    return featureList;
  };

  const getPlanDisplayInfo = (plan) => {
    const isMonthly = plan.price_monthly && !plan.price_lifetime;
    const isLifetime = plan.price_lifetime && !plan.price_monthly;
    
    let displayInfo = {
      title: plan.name,
      price: isMonthly ? `$${plan.price_monthly}` : `$${plan.price_lifetime}`,
      period: isMonthly ? '/month' : 'one-time',
      buttonText: isMonthly ? 'Start Monthly Plan' : `Get ${plan.name}`,
      isElite: plan.name.includes('Elite'),
      highlighted: plan.name.includes('Standard')
    };

    // Add subtitle and savings info for lifetime plans
    if (isLifetime) {
      let features = {};
      try {
        features = typeof plan.features === 'string' ? JSON.parse(plan.features) : (plan.features || {});
      } catch (error) {
        console.error('Failed to parse plan features for display:', error);
        features = {};
      }
      if (plan.name.includes('Entry')) {
        displayInfo.subtitle = "Just starting out? This is your launchpad.";
        displayInfo.originalPrice = "$560";
        displayInfo.savings = "Save $461!";
      } else if (plan.name.includes('Standard')) {
        displayInfo.subtitle = "The sweet spot for serious creators.";
        displayInfo.originalPrice = "$1,260";
        displayInfo.savings = "Save $1,081!";
      } else if (plan.name.includes('Pro')) {
        displayInfo.subtitle = "For power users who demand more.";
        displayInfo.originalPrice = "$1,961";
        displayInfo.savings = "Save $1,711!";
      } else if (plan.name.includes('Elite')) {
        displayInfo.subtitle = "The ultimate creative powerhouse.";
        displayInfo.originalPrice = "$9,490";
        displayInfo.savings = "Save $8,493!";
      }

      // Add spots info if available
      if (features.spots_left && features.total_spots) {
        displayInfo.spotsLeft = features.spots_left.toString();
        displayInfo.totalSpots = features.total_spots.toString();
        displayInfo.claimed = (features.total_spots - features.spots_left).toString();
      }
    } else if (isMonthly) {
      displayInfo.subtitle = "Perfect for starters or ongoing creators";
      displayInfo.note = "📌 Credits reset monthly. Cancel anytime.";
    }

    return displayInfo;
  };

  if (loading) {
    return (
      <section className="space-y-8 mt-16">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900">Loading Pricing Plans...</h2>
          <div className="mt-8 flex justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        </div>
      </section>
    );
  }

  const monthlyPlans = subscriptionPlans.filter(plan => plan.price_monthly && !plan.price_lifetime);
  const lifetimePlans = subscriptionPlans.filter(plan => plan.price_lifetime && !plan.price_monthly);

  return (
    <section className="space-y-8 mt-16">
      <div className="text-center mb-12">
        <h2 className="text-5xl font-bold text-gray-900 mb-4">🌟 Unlock Lifetime Creativity — Pay Once, Create Forever!</h2>
        <div className="bg-red-100 border border-red-300 rounded-lg p-4 max-w-2xl mx-auto">
          <p className="text-red-800 font-semibold">⚡ Limited Spots Left — Price Increases in 24 Hours!</p>
          <p className="text-red-600">👉 Only 12 lifetime spots remain — Claim yours before they're gone!</p>
        </div>
      </div>

      {/* Monthly Plans */}
      {monthlyPlans.map(plan => {
        const displayInfo = getPlanDisplayInfo(plan);
        return (
          <div key={plan.id} className="max-w-2xl mx-auto mb-16">
            <PricingCard 
              {...displayInfo}
              features={formatPlanFeatures(plan)}
              onClick={() => handlePlanSelection(plan)}
            />
          </div>
        );
      })}

      {/* Lifetime Plans */}
      {lifetimePlans.length > 0 && (
        <>
          <div className="text-center mb-8">
            <h3 className="text-4xl font-bold text-gray-900 mb-2">🎯 LIFETIME PLANS — ONE-TIME PAYMENT, UNLIMITED VALUE</h3>
          </div>
          
          <div className="grid lg:grid-cols-2 xl:grid-cols-4 gap-8 max-w-7xl mx-auto">
            {lifetimePlans.map(plan => {
              const displayInfo = getPlanDisplayInfo(plan);
              return (
                <PricingCard 
                  key={plan.id}
                  {...displayInfo}
                  features={formatPlanFeatures(plan)}
                  onClick={() => handlePlanSelection(plan)}
                />
              );
            })}
          </div>
        </>
      )}

      {/* Call to Action */}
      <div className="bg-gradient-to-r from-red-500 to-purple-600 text-white rounded-xl p-8 max-w-4xl mx-auto mt-16 text-center">
        <h3 className="text-3xl font-bold mb-4">📢 ACT NOW — BEFORE IT'S TOO LATE!</h3>
        <p className="text-xl mb-4">"This offer disappears forever when spots run out!"</p>
        <p className="text-lg mb-6">🔥 Price increases in 48 hours!</p>
        <button 
          onClick={onShowAuth}
          className="bg-white text-purple-600 px-8 py-4 rounded-lg font-bold text-xl hover:bg-gray-100 transition-colors"
        >
          👉 Secure Your Spot → Get Lifetime Access
        </button>
      </div>
    </section>
  );
}

// Landing Page Component
function LandingPage({ onShowAuth, isAuthenticated, user }) {
  return (
    <div className="text-center space-y-12">
      {/* Hero Section */}
      <section className="space-y-6">
        <h1 className="text-6xl font-bold text-gray-900 leading-tight">
          Transform Your Ideas Into
          <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent"> 
            Professional Books
          </span>
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
          Manuscriptify uses AI to help you create stunning ebooks, audiobooks, novels, kids books, and coloring books 
          from your ideas or existing content. No technical skills required.
        </p>
        <div className="flex gap-4 justify-center">
          <button 
            onClick={onShowAuth}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-colors"
            data-testid="get-started-btn"
          >
            Get Started Free
          </button>
          <button className="border-2 border-gray-300 hover:bg-gray-50 text-gray-700 px-8 py-4 rounded-lg text-lg font-semibold transition-colors">
            Watch Demo
          </button>
        </div>
      </section>

      {/* Features Grid */}
      <section className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mt-16">
        <FeatureCard 
          icon="📚"
          title="AI Book Generation"
          description="Transform prompts or uploaded content into professionally structured books"
        />
        <FeatureCard 
          icon="🎧"
          title="Audiobook Creation"
          description="Convert your text to high-quality audio with multiple voice options"
        />
        <FeatureCard 
          icon="🎨"
          title="Cover Art Generation"
          description="Create stunning book covers with AI-powered artwork"
        />
        <FeatureCard 
          icon="🌍"
          title="Multi-Language Support"
          description="Support for 6 languages with automatic translation"
        />
      </section>

      {/* Genre Categories */}
      <section className="space-y-8 mt-16">
        <h2 className="text-4xl font-bold text-gray-900">Create Any Type of Book</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <GenreCard 
            title="E-books"
            description="Professional non-fiction books, guides, and educational content"
            specs="75-150 pages • 6x9 format"
            color="bg-blue-500"
          />
          <GenreCard 
            title="Novels"
            description="Fiction stories with compelling characters and narrative"
            specs="100-250 pages • 6x9 format"
            color="bg-purple-500"
          />
          <GenreCard 
            title="Kids Stories"
            description="Illustrated children's books with engaging artwork"
            specs="Up to 25 pages • 8x10 format"
            color="bg-green-500"
          />
          <GenreCard 
            title="Coloring Books"
            description="Black & white illustrations perfect for coloring"
            specs="20 pages • 8x10 format"
            color="bg-orange-500"
          />
        </div>
      </section>

      {/* Dynamic Pricing Section */}
      <DynamicPricing 
        onShowAuth={onShowAuth} 
        isAuthenticated={isAuthenticated} 
        user={user} 
      />
    </div>
  );
}

// Feature Card Component
function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

// Genre Card Component
function GenreCard({ title, description, specs, color }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <div className={`w-12 h-12 ${color} rounded-lg mb-4 flex items-center justify-center text-white text-2xl font-bold`}>
        {title.charAt(0)}
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 mb-3">{description}</p>
      <p className="text-sm text-gray-500 font-medium">{specs}</p>
    </div>
  );
}

// Enhanced Pricing Card Component
function PricingCard({ 
  title, subtitle, price, originalPrice, savings, period, features, buttonText, 
  highlighted, isElite, spotsLeft, totalSpots, claimed, note, onClick 
}) {
  return (
    <div className={`p-6 rounded-xl border-2 relative ${
      highlighted 
        ? 'border-blue-500 bg-blue-50' 
        : isElite
        ? 'border-purple-500 bg-gradient-to-b from-purple-50 to-pink-50'
        : 'border-gray-200 bg-white'
    } hover:shadow-lg transition-all transform hover:-translate-y-1`}>
      
      {/* Most Popular Badge */}
      {highlighted && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">
            Most Popular
          </span>
        </div>
      )}

      {/* Elite Badge */}
      {isElite && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <span className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-1 rounded-full text-sm font-medium">
            ⭐ ELITE
          </span>
        </div>
      )}

      {/* Savings Badge */}
      {savings && (
        <div className="absolute -top-2 -right-2">
          <span className="bg-red-500 text-white px-3 py-1 rounded-full text-xs font-bold transform rotate-12">
            {savings}
          </span>
        </div>
      )}

      <div className="text-center mb-6">
        <h3 className={`text-xl font-bold mb-1 ${isElite ? 'text-purple-600' : 'text-gray-900'}`}>
          {title}
        </h3>
        {subtitle && (
          <p className="text-sm text-gray-600 italic mb-3">"{subtitle}"</p>
        )}
        
        <div className="flex items-baseline justify-center mb-2">
          <span className={`text-3xl font-bold ${
            highlighted ? 'text-blue-600' : isElite ? 'text-purple-600' : 'text-gray-900'
          }`}>{price}</span>
          <span className="text-gray-500 ml-1 text-sm">{period}</span>
        </div>

        {originalPrice && (
          <div className="text-center">
            <span className="text-gray-400 line-through text-sm">Was {originalPrice}</span>
          </div>
        )}

        {/* Spots Left Indicator */}
        {spotsLeft && (
          <div className="bg-red-100 border border-red-300 rounded-lg p-2 mt-3">
            <p className="text-red-800 text-xs font-semibold">
              ⏳ {spotsLeft} spots left at this price — {claimed} of {totalSpots} claimed!
            </p>
          </div>
        )}
      </div>

      <ul className="space-y-2 mb-6">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start text-sm text-gray-700">
            <span className="text-green-500 mr-2 flex-shrink-0 mt-0.5">✓</span>
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      {note && (
        <div className="text-xs text-gray-600 mb-4 p-2 bg-gray-50 rounded">
          {note}
        </div>
      )}

      <button 
        onClick={onClick}
        className={`w-full py-3 px-6 rounded-lg font-bold transition-all transform hover:scale-105 ${
          highlighted
            ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg'
            : isElite
            ? 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg'
            : 'bg-gray-900 hover:bg-gray-800 text-white'
        }`}
      >
        {buttonText}
      </button>
    </div>
  );
}

export { UserContext };
export default App;