# Stripe Integration Testing Guide

## Overview
This guide will help you test the complete Stripe payment integration for Manuscriptify.

## Prerequisites

### 1. Environment Setup
Create a `.env` file in the `backend` directory with your Stripe keys:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=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
STRIPE_PUBLISHABLE_KEY=pk_live_51QLMqlR2vdu0rh1pmJMIWuMCvD9bh3vVINpTPhPyKrwyDhJDEQRoH0SuoMb1WgjrEuMZcFOseqnggmjpXToEX2pD005Wa8L14u
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE

# Add other required environment variables...
```

### 2. Create Stripe Products and Prices
Run the setup script to create products in your Stripe account:

```bash
cd backend
python setup_stripe_products.py
```

This will create:
- Monthly Plan ($39/month)
- Entry Lifetime ($99 one-time)
- Standard Lifetime ($179 one-time)
- Pro Lifetime ($250 one-time)
- Elite Lifetime ($997 one-time)

### 3. Set Up Webhook Endpoint
1. Go to [Stripe Dashboard > Webhooks](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Set endpoint URL to: `https://your-domain.com/api/stripe/webhook`
4. Select these events:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
5. Copy the webhook signing secret and add it to your `.env` file

## Testing Steps

### 1. Frontend Testing

#### Access the Pricing Page
1. Start your frontend application
2. Navigate to `/pricing`
3. Verify all 5 pricing plans are displayed correctly
4. Check that plan features, prices, and "spots left" counters are showing

#### User Authentication Flow
1. Try clicking a plan button without being logged in
2. Verify you get a "Please sign in to select a plan" message
3. Sign in to your account
4. Try clicking a plan button again

#### Payment Flow
1. Click on any plan button while logged in
2. Verify the button shows "Processing..." with a loading spinner
3. You should be redirected to Stripe Checkout
4. Complete the payment using Stripe's test card numbers (if in test mode)

### 2. Backend API Testing

#### Test Stripe Configuration Endpoint
```bash
curl -X GET http://localhost:8000/api/stripe/config
```

Expected response:
```json
{
  "publishable_key": "pk_live_...",
  "plans": {
    "monthly": { ... },
    "entry-lifetime": { ... },
    ...
  }
}
```

#### Test Checkout Session Creation
```bash
curl -X POST http://localhost:8000/api/stripe/create-checkout-session \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "plan_id": "monthly",
    "success_url": "http://localhost:3000/payment/success",
    "cancel_url": "http://localhost:3000/pricing"
  }'
```

### 3. Payment Success Page Testing

#### Test Success Flow
1. Complete a payment through Stripe Checkout
2. Verify you're redirected to `/payment/success?session_id=cs_...`
3. Check that the success page shows:
   - Payment confirmation
   - Plan details
   - Amount paid
   - Next steps
   - Action buttons

#### Test Session Retrieval
The success page should automatically fetch and display session details.

### 4. Webhook Testing

#### Using Stripe CLI (Recommended)
1. Install [Stripe CLI](https://stripe.com/docs/stripe-cli)
2. Login: `stripe login`
3. Forward events to your local server:
   ```bash
   stripe listen --forward-to localhost:8000/api/stripe/webhook
   ```
4. Trigger test events:
   ```bash
   stripe trigger checkout.session.completed
   ```

#### Manual Testing
1. Complete a real payment
2. Check your server logs for webhook events
3. Verify the webhook endpoint responds with `{"status": "success"}`

## Test Scenarios

### Scenario 1: Monthly Subscription
1. Select Monthly Plan ($39/month)
2. Complete payment
3. Verify recurring subscription is created in Stripe
4. Check webhook handles `checkout.session.completed`

### Scenario 2: Lifetime Purchase
1. Select any Lifetime plan
2. Complete payment
3. Verify one-time payment is processed
4. Check user's subscription status is updated

### Scenario 3: Payment Failure
1. Use a declined test card
2. Verify user is returned to pricing page
3. Check error handling and user feedback

### Scenario 4: Webhook Security
1. Send a webhook request without proper signature
2. Verify it's rejected with 400 error
3. Send with correct signature and verify it's processed

## Debugging Tips

### Common Issues

1. **"Stripe is not properly configured" error**
   - Check your `.env` file has all required Stripe keys
   - Verify keys are correctly formatted (no extra spaces)

2. **"Invalid plan ID" error**
   - Run the setup script to create products
   - Verify price IDs in your `.env` file match Stripe Dashboard

3. **Webhook signature verification fails**
   - Check webhook secret is correctly set
   - Verify webhook endpoint URL is accessible
   - Check Stripe CLI forwarding is working

4. **Payment button doesn't work**
   - Check browser console for JavaScript errors
   - Verify user is authenticated
   - Check network tab for API call failures

### Logging
Check server logs for detailed error messages:
```bash
tail -f backend/logs/app.log
```

## Security Considerations

### Production Checklist
- [ ] Use live Stripe keys (not test keys)
- [ ] Verify webhook endpoint is HTTPS
- [ ] Implement proper error handling
- [ ] Add rate limiting to payment endpoints
- [ ] Log all payment events for audit
- [ ] Test with real payment amounts
- [ ] Verify tax handling (if applicable)
- [ ] Test subscription management flows

### Test Mode vs Live Mode
- Test mode: Use `sk_test_...` and `pk_test_...` keys
- Live mode: Use `sk_live_...` and `pk_live_...` keys (current setup)
- Never mix test and live keys

## Support

If you encounter issues:
1. Check Stripe Dashboard for payment logs
2. Review server logs for detailed errors
3. Use Stripe CLI for webhook debugging
4. Test with Stripe's test card numbers first

## Next Steps

After successful testing:
1. Set up production webhook endpoints
2. Configure subscription management
3. Implement user subscription status updates
4. Add billing portal access for customers
5. Set up automated email receipts
6. Configure tax handling if required
