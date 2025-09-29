import React, { useState } from 'react';
import { Check, Star, Zap, Crown, Sparkles, Loader2 } from 'lucide-react';
import { useStripe } from '../hooks/useStripe';
import { toast } from 'sonner';

function Pricing({ onSelectPlan, user }) {
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [processingPlan, setProcessingPlan] = useState(null);
  const { createCheckoutSession, loading, error, clearError } = useStripe();

  const plans = [
    {
      id: 'monthly',
      name: 'Monthly Plan',
      price: 39,
      period: 'month',
      description: 'Perfect for starters or ongoing creators',
      icon: <Zap className="w-6 h-6" />,
      color: 'blue',
      features: [
        'Generate 4 Books Monthly',
        'Choose any mix: E-Books, Novels, Kids\' Storybooks, or Coloring Books',
        'Plus: Generate 2 Audiobooks (separate from the 4 books)',
        'Book Cover Generator Access',
        '40 AI Image Credits/month',
        '100 Marketing Task Generations/month',
        'All Features Unlocked',
        'Priority Support & Lifetime Updates',
        'Free 1 Chapter Trial Available'
      ],
      note: 'Credits reset monthly. Cancel anytime.',
      popular: false
    },
    {
      id: 'entry-lifetime',
      name: 'Entry Lifetime',
      price: 99,
      originalPrice: 560,
      period: 'lifetime',
      description: 'Just starting out? This is your launchpad.',
      icon: <Star className="w-6 h-6" />,
      color: 'green',
      features: [
        '6 Books/month (4 Pick n\' Mix + 2 AudioBook)',
        '100 marketing task generations/month',
        'All features unlocked + lifetime updates',
        'Access to all features',
        'Premium support',
        'Free 1 Chapter Trial Generation'
      ],
      spotsLeft: 11,
      totalSpots: 70,
      claimed: 59,
      popular: false
    },
    {
      id: 'standard-lifetime',
      name: 'Standard Lifetime',
      price: 179,
      originalPrice: 1260,
      period: 'lifetime',
      description: 'The sweet spot for serious creators.',
      icon: <Crown className="w-6 h-6" />,
      color: 'purple',
      features: [
        '8 Books/month (5 Pick n\' Mix + 3 AudioBook)',
        '80 AI image credits/month',
        '200 marketing task generations/month',
        'All features unlocked + lifetime updates',
        'Access to all features',
        'Priority support',
        'Free 1 Chapter Trial Generation'
      ],
      spotsLeft: 21,
      totalSpots: 75,
      claimed: 54,
      popular: true
    },
    {
      id: 'pro-lifetime',
      name: 'Pro Lifetime',
      price: 250,
      originalPrice: 1961,
      period: 'lifetime',
      description: 'For power users who demand more.',
      icon: <Sparkles className="w-6 h-6" />,
      color: 'indigo',
      features: [
        '12 Books/month (8 Pick n\' Mix & 4 AudioBook)',
        '120 AI image credits/month',
        '400 marketing task generations/month',
        'All features unlocked + lifetime updates',
        'Access to all features',
        'Premium support + 1-on-1 onboarding',
        'Free 1 Chapter Trial Generation'
      ],
      spotsLeft: 13,
      totalSpots: 75,
      claimed: 62,
      popular: false
    },
    {
      id: 'elite-lifetime',
      name: 'Elite Lifetime',
      price: 997,
      originalPrice: 9490,
      period: 'lifetime',
      description: 'The ultimate creative powerhouse.',
      icon: <Crown className="w-6 h-6" />,
      color: 'yellow',
      features: [
        '100 Books/month (80 Pick n\' Mix & 20 AudioBooks) — MASSIVE!',
        '800 AI image credits/month',
        '1,000 marketing task generations/month — UNSTOPPABLE!',
        'All features unlocked + lifetime updates',
        'Access to all courses + exclusive content',
        'Priority support + dedicated onboarding',
        'Free 1 Chapter Trial Generation'
      ],
      spotsLeft: 7,
      totalSpots: 75,
      claimed: 67,
      popular: false
    }
  ];

  const getColorClasses = (color, variant = 'primary') => {
    const colors = {
      blue: {
        primary: 'bg-blue-600 hover:bg-blue-700 text-white',
        secondary: 'bg-blue-50 text-blue-600 border-blue-200',
        accent: 'text-blue-600',
        gradient: 'from-blue-500 to-blue-600'
      },
      green: {
        primary: 'bg-green-600 hover:bg-green-700 text-white',
        secondary: 'bg-green-50 text-green-600 border-green-200',
        accent: 'text-green-600',
        gradient: 'from-green-500 to-green-600'
      },
      purple: {
        primary: 'bg-purple-600 hover:bg-purple-700 text-white',
        secondary: 'bg-purple-50 text-purple-600 border-purple-200',
        accent: 'text-purple-600',
        gradient: 'from-purple-500 to-purple-600'
      },
      indigo: {
        primary: 'bg-indigo-600 hover:bg-indigo-700 text-white',
        secondary: 'bg-indigo-50 text-indigo-600 border-indigo-200',
        accent: 'text-indigo-600',
        gradient: 'from-indigo-500 to-indigo-600'
      },
      yellow: {
        primary: 'bg-yellow-500 hover:bg-yellow-600 text-white',
        secondary: 'bg-yellow-50 text-yellow-600 border-yellow-200',
        accent: 'text-yellow-600',
        gradient: 'from-yellow-400 to-yellow-500'
      }
    };
    return colors[color][variant];
  };

  const handleSelectPlan = async (plan) => {
    if (!user) {
      toast.error('Please sign in to select a plan');
      return;
    }

    setSelectedPlan(plan.id);
    setProcessingPlan(plan.id);
    clearError();

    try {
      const currentUrl = window.location.origin;
      const successUrl = `${currentUrl}/payment/success`;
      const cancelUrl = `${currentUrl}/pricing`;

      await createCheckoutSession(plan.id, successUrl, cancelUrl);
      
      if (onSelectPlan) {
        onSelectPlan(plan);
      }
    } catch (err) {
      toast.error(error || 'Failed to start checkout process');
      console.error('Checkout error:', err);
    } finally {
      setProcessingPlan(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-12">
      <div className="container mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            🌟 Unlock Lifetime Creativity — Pay Once, Create Forever!
          </h1>
          <p className="text-xl text-red-600 font-semibold mb-2">
            Limited Spots Left — Price Increases in 24 Hours!
          </p>
          <div className="inline-flex items-center bg-red-100 text-red-800 px-4 py-2 rounded-full text-sm font-medium">
            🔥 Price increases in 48 hours!
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6 mb-12">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`relative bg-white rounded-2xl shadow-lg border-2 transition-all duration-300 hover:shadow-xl hover:scale-105 ${
                plan.popular ? 'border-purple-500 ring-4 ring-purple-100' : 'border-gray-200'
              } ${selectedPlan === plan.id ? 'ring-4 ring-blue-100 border-blue-500' : ''}`}
            >
              {/* Popular Badge */}
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white px-4 py-1 rounded-full text-sm font-semibold">
                    Most Popular
                  </div>
                </div>
              )}

              <div className="p-6">
                {/* Plan Header */}
                <div className="text-center mb-6">
                  <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-r ${getColorClasses(plan.color, 'gradient')} text-white mb-4`}>
                    {plan.icon}
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <p className="text-gray-600 text-sm mb-4">{plan.description}</p>
                  
                  {/* Price */}
                  <div className="mb-4">
                    <div className="flex items-center justify-center">
                      <span className="text-3xl font-bold text-gray-900">${plan.price}</span>
                      {plan.period === 'month' && (
                        <span className="text-gray-600 ml-1">/month</span>
                      )}
                    </div>
                    {plan.originalPrice && (
                      <div className="text-center mt-1">
                        <span className="text-gray-500 line-through text-sm">${plan.originalPrice}</span>
                        <span className={`ml-2 text-sm font-semibold ${getColorClasses(plan.color, 'accent')}`}>
                          Save ${plan.originalPrice - plan.price}!
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Spots Left */}
                  {plan.spotsLeft && (
                    <div className="mb-4">
                      <div className="text-sm text-red-600 font-semibold mb-2">
                        ⏳ {plan.spotsLeft} spots left at this price
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-red-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${(plan.claimed / plan.totalSpots) * 100}%` }}
                        ></div>
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {plan.claimed} of {plan.totalSpots} claimed
                      </div>
                    </div>
                  )}
                </div>

                {/* Features */}
                <div className="space-y-3 mb-6">
                  {plan.features.map((feature, index) => (
                    <div key={index} className="flex items-start">
                      <Check className={`w-5 h-5 ${getColorClasses(plan.color, 'accent')} mr-3 mt-0.5 flex-shrink-0`} />
                      <span className="text-sm text-gray-700">{feature}</span>
                    </div>
                  ))}
                </div>

                {/* Note */}
                {plan.note && (
                  <div className="text-xs text-gray-500 mb-4 p-2 bg-gray-50 rounded">
                    📌 {plan.note}
                  </div>
                )}

                {/* CTA Button */}
                <button
                  onClick={() => handleSelectPlan(plan)}
                  disabled={processingPlan === plan.id || loading}
                  className={`w-full py-3 px-4 rounded-lg font-semibold transition-all duration-300 ${
                    processingPlan === plan.id || loading 
                      ? 'bg-gray-400 cursor-not-allowed' 
                      : getColorClasses(plan.color, 'primary')
                  } transform hover:scale-105 disabled:hover:scale-100 flex items-center justify-center`}
                >
                  {processingPlan === plan.id ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      Processing...
                    </>
                  ) : !user ? (
                    'Sign In to Purchase'
                  ) : (
                    plan.period === 'lifetime' ? 'Get Lifetime Access' : 'Start Monthly Plan'
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Why Choose Us Section */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">⚡ Why Choose Us?</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Check className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">No Hidden Fees</h3>
              <p className="text-sm text-gray-600">Pay once, use forever (for lifetime plans)</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Zap className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Auto Reset Credits</h3>
              <p className="text-sm text-gray-600">Monthly credits reset automatically — never lose unused credits</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Star className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">New Features Included</h3>
              <p className="text-sm text-gray-600">Get every upgrade we launch</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Sparkles className="w-6 h-6 text-red-600" />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Urgent Scarcity</h3>
              <p className="text-sm text-gray-600">Prices rise soon, spots are vanishing!</p>
            </div>
          </div>
        </div>

        {/* Final CTA */}
        <div className="text-center bg-gradient-to-r from-red-500 to-red-600 text-white rounded-2xl p-8">
          <h2 className="text-3xl font-bold mb-4">📢 ACT NOW — BEFORE IT'S TOO LATE!</h2>
          <p className="text-xl mb-6">"This offer disappears forever when spots run out!"</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button className="bg-white text-red-600 px-8 py-3 rounded-lg font-bold text-lg hover:bg-gray-100 transition-colors">
              👉 Slide to secure your spot → Get Lifetime Access
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Pricing;
