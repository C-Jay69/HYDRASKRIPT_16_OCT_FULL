import { useState, useEffect } from 'react';
import axios from 'axios';

export const useStripe = () => {
  const [stripeConfig, setStripeConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStripeConfig();
  }, []);

  const fetchStripeConfig = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/stripe/config');
      setStripeConfig(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch Stripe config:', err);
      setError('Failed to load payment configuration');
    } finally {
      setLoading(false);
    }
  };

  const createCheckoutSession = async (planId, successUrl, cancelUrl) => {
    try {
      setLoading(true);
      const response = await axios.post('/api/stripe/create-checkout-session', {
        plan_id: planId,
        success_url: successUrl,
        cancel_url: cancelUrl
      });

      if (response.data.success) {
        // Redirect to Stripe Checkout
        window.location.href = response.data.session_url;
        return response.data;
      } else {
        throw new Error(response.data.error || 'Failed to create checkout session');
      }
    } catch (err) {
      console.error('Failed to create checkout session:', err);
      setError(err.response?.data?.detail || err.message || 'Payment initialization failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const retrieveSession = async (sessionId) => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/stripe/session/${sessionId}`);
      
      if (response.data.success) {
        return response.data.session;
      } else {
        throw new Error(response.data.error || 'Failed to retrieve session');
      }
    } catch (err) {
      console.error('Failed to retrieve session:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to retrieve payment session');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const createCustomerPortalSession = async (customerId, returnUrl) => {
    try {
      setLoading(true);
      const response = await axios.post('/api/stripe/create-portal-session', {
        customer_id: customerId,
        return_url: returnUrl
      });

      if (response.data.success) {
        // Redirect to Stripe Customer Portal
        window.location.href = response.data.portal_url;
        return response.data;
      } else {
        throw new Error(response.data.error || 'Failed to create portal session');
      }
    } catch (err) {
      console.error('Failed to create portal session:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to access billing portal');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return {
    stripeConfig,
    loading,
    error,
    createCheckoutSession,
    retrieveSession,
    createCustomerPortalSession,
    clearError: () => setError(null)
  };
};
