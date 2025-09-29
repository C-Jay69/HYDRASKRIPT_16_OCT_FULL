import os
import logging
import stripe
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self):
        self.stripe_secret_key = os.environ.get('STRIPE_SECRET_KEY')
        self.stripe_publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY')
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        if self.stripe_secret_key:
            stripe.api_key = self.stripe_secret_key
        
        # Price IDs for each plan (these will need to be created in Stripe Dashboard)
        self.price_ids = {
            'monthly': os.environ.get('STRIPE_MONTHLY_PRICE_ID'),
            'entry-lifetime': os.environ.get('STRIPE_ENTRY_LIFETIME_PRICE_ID'),
            'standard-lifetime': os.environ.get('STRIPE_STANDARD_LIFETIME_PRICE_ID'),
            'pro-lifetime': os.environ.get('STRIPE_PRO_LIFETIME_PRICE_ID'),
            'elite-lifetime': os.environ.get('STRIPE_ELITE_LIFETIME_PRICE_ID')
        }
        
        # Plan configurations
        self.plan_configs = {
            'monthly': {
                'name': 'Monthly Plan',
                'price': 3900,  # $39.00 in cents
                'currency': 'usd',
                'interval': 'month',
                'features': {
                    'books_per_month': 4,
                    'audiobooks_per_month': 2,
                    'ai_image_credits': 40,
                    'marketing_tasks': 100,
                    'book_cover_generator': True,
                    'all_features': True,
                    'priority_support': True,
                    'free_trial': True
                }
            },
            'entry-lifetime': {
                'name': 'Entry Lifetime',
                'price': 9900,  # $99.00 in cents
                'currency': 'usd',
                'interval': None,  # One-time payment
                'features': {
                    'books_per_month': 6,
                    'audiobooks_per_month': 2,
                    'ai_image_credits': 0,  # Not specified in original
                    'marketing_tasks': 100,
                    'book_cover_generator': True,
                    'all_features': True,
                    'priority_support': True,
                    'free_trial': True,
                    'lifetime_updates': True
                }
            },
            'standard-lifetime': {
                'name': 'Standard Lifetime',
                'price': 17900,  # $179.00 in cents
                'currency': 'usd',
                'interval': None,
                'features': {
                    'books_per_month': 8,
                    'audiobooks_per_month': 3,
                    'ai_image_credits': 80,
                    'marketing_tasks': 200,
                    'book_cover_generator': True,
                    'all_features': True,
                    'priority_support': True,
                    'free_trial': True,
                    'lifetime_updates': True
                }
            },
            'pro-lifetime': {
                'name': 'Pro Lifetime',
                'price': 25000,  # $250.00 in cents
                'currency': 'usd',
                'interval': None,
                'features': {
                    'books_per_month': 12,
                    'audiobooks_per_month': 4,
                    'ai_image_credits': 120,
                    'marketing_tasks': 400,
                    'book_cover_generator': True,
                    'all_features': True,
                    'priority_support': True,
                    'onboarding': True,
                    'free_trial': True,
                    'lifetime_updates': True
                }
            },
            'elite-lifetime': {
                'name': 'Elite Lifetime',
                'price': 99700,  # $997.00 in cents
                'currency': 'usd',
                'interval': None,
                'features': {
                    'books_per_month': 100,
                    'audiobooks_per_month': 20,
                    'ai_image_credits': 800,
                    'marketing_tasks': 1000,
                    'book_cover_generator': True,
                    'all_features': True,
                    'priority_support': True,
                    'dedicated_onboarding': True,
                    'exclusive_content': True,
                    'courses_access': True,
                    'free_trial': True,
                    'lifetime_updates': True
                }
            }
        }
    
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured"""
        return bool(self.stripe_secret_key and self.stripe_publishable_key)
    
    async def create_checkout_session(self, plan_id: str, user_id: str, user_email: str, 
                                    success_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create a Stripe checkout session for a specific plan"""
        try:
            if not self.is_configured():
                raise Exception("Stripe is not properly configured")
            
            plan_config = self.plan_configs.get(plan_id)
            if not plan_config:
                raise Exception(f"Invalid plan ID: {plan_id}")
            
            # Create checkout session parameters
            session_params = {
                'payment_method_types': ['card'],
                'customer_email': user_email,
                'line_items': [{
                    'price_data': {
                        'currency': plan_config['currency'],
                        'product_data': {
                            'name': plan_config['name'],
                            'description': f"Manuscriptify {plan_config['name']} - Full access to book generation platform"
                        },
                        'unit_amount': plan_config['price'],
                    },
                    'quantity': 1,
                }],
                'mode': 'subscription' if plan_config['interval'] else 'payment',
                'success_url': success_url + '?session_id={CHECKOUT_SESSION_ID}',
                'cancel_url': cancel_url,
                'metadata': {
                    'user_id': str(user_id),
                    'plan_id': plan_id,
                    'plan_name': plan_config['name']
                }
            }
            
            # Add subscription-specific parameters
            if plan_config['interval']:
                session_params['line_items'][0]['price_data']['recurring'] = {
                    'interval': plan_config['interval']
                }
            
            # Create the session
            session = stripe.checkout.Session.create(**session_params)
            
            return {
                'success': True,
                'session_id': session.id,
                'session_url': session.url,
                'plan_id': plan_id,
                'plan_name': plan_config['name'],
                'amount': plan_config['price']
            }
            
        except Exception as e:
            logger.error(f"Failed to create checkout session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def retrieve_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieve a checkout session by ID"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'success': True,
                'session': {
                    'id': session.id,
                    'payment_status': session.payment_status,
                    'customer_email': session.customer_email,
                    'amount_total': session.amount_total,
                    'currency': session.currency,
                    'metadata': session.metadata
                }
            }
        except Exception as e:
            logger.error(f"Failed to retrieve session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def create_customer_portal_session(self, customer_id: str, return_url: str) -> Dict[str, Any]:
        """Create a customer portal session for subscription management"""
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return {
                'success': True,
                'portal_url': session.url
            }
            
        except Exception as e:
            logger.error(f"Failed to create customer portal session: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            if not self.webhook_secret:
                raise Exception("Webhook secret not configured")
            
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            event_type = event['type']
            event_data = event['data']['object']
            
            logger.info(f"Received Stripe webhook: {event_type}")
            
            # Handle different event types
            if event_type == 'checkout.session.completed':
                return await self._handle_checkout_completed(event_data)
            elif event_type == 'invoice.payment_succeeded':
                return await self._handle_payment_succeeded(event_data)
            elif event_type == 'invoice.payment_failed':
                return await self._handle_payment_failed(event_data)
            elif event_type == 'customer.subscription.deleted':
                return await self._handle_subscription_cancelled(event_data)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {'success': True, 'message': 'Event received but not handled'}
            
        except Exception as e:
            logger.error(f"Webhook handling failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_checkout_completed(self, session_data: Dict) -> Dict[str, Any]:
        """Handle successful checkout completion"""
        try:
            user_id = session_data.get('metadata', {}).get('user_id')
            plan_id = session_data.get('metadata', {}).get('plan_id')
            
            if not user_id or not plan_id:
                raise Exception("Missing user_id or plan_id in session metadata")
            
            # Here you would update the user's subscription in your database
            # For now, we'll just log the event
            logger.info(f"User {user_id} successfully purchased plan {plan_id}")
            
            return {
                'success': True,
                'message': 'Checkout completed successfully',
                'user_id': user_id,
                'plan_id': plan_id
            }
            
        except Exception as e:
            logger.error(f"Failed to handle checkout completion: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_payment_succeeded(self, invoice_data: Dict) -> Dict[str, Any]:
        """Handle successful payment"""
        try:
            customer_id = invoice_data.get('customer')
            subscription_id = invoice_data.get('subscription')
            
            logger.info(f"Payment succeeded for customer {customer_id}, subscription {subscription_id}")
            
            # Update user's subscription status in database
            return {
                'success': True,
                'message': 'Payment processed successfully'
            }
            
        except Exception as e:
            logger.error(f"Failed to handle payment success: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_payment_failed(self, invoice_data: Dict) -> Dict[str, Any]:
        """Handle failed payment"""
        try:
            customer_id = invoice_data.get('customer')
            subscription_id = invoice_data.get('subscription')
            
            logger.warning(f"Payment failed for customer {customer_id}, subscription {subscription_id}")
            
            # Handle failed payment (e.g., send email, update user status)
            return {
                'success': True,
                'message': 'Payment failure handled'
            }
            
        except Exception as e:
            logger.error(f"Failed to handle payment failure: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_subscription_cancelled(self, subscription_data: Dict) -> Dict[str, Any]:
        """Handle subscription cancellation"""
        try:
            customer_id = subscription_data.get('customer')
            subscription_id = subscription_data.get('id')
            
            logger.info(f"Subscription {subscription_id} cancelled for customer {customer_id}")
            
            # Update user's subscription status in database
            return {
                'success': True,
                'message': 'Subscription cancellation handled'
            }
            
        except Exception as e:
            logger.error(f"Failed to handle subscription cancellation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_plan_config(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific plan"""
        return self.plan_configs.get(plan_id)
    
    def get_all_plans(self) -> Dict[str, Any]:
        """Get all available plans"""
        return self.plan_configs
    
    def get_publishable_key(self) -> str:
        """Get Stripe publishable key for frontend"""
        return self.stripe_publishable_key or ""

# Create global instance
stripe_service = StripeService()
