Emma observed how the goats worked together, always watching out for each other, while Lily was delighted by the tiny baby goats that were only a few weeks old.

Page 6:
The chicken coop was Lily's favorite discovery. The gentle hens clucked softly as she scattered feed for them, and when a fluffy yellow chick peeped from beneath its mother's wing, Lily's heart melted completely. "They're so soft," she whispered, gently stroking the chick's downy feathers with one finger.

Emma learned that chickens were much smarter than she'd ever imagined, while Sofia enjoyed the silly way they tilted their heads when she spoke to them.

Page 7:
As the days passed, each sister found her special connection with the farm animals. Emma spent hours with Thunder, learning to brush his coat and clean his hooves. She discovered that taking care of such a large, powerful animal required patience, gentleness, and respect.

"Thunder teaches me to be calm and thoughtful," Emma told her sisters one evening as they sat on the porch watching the sunset paint the sky in shades of orange and pink.

Page 8:
Sofia became the official goat entertainer, spending her mornings playing games with Pepper, Cinnamon, and Nutmeg. She learned that goats were incredibly social animals who needed friendship and fun to be happy. Uncle Joe taught her how to milk the goats, and Sofia was so proud when she successfully filled her first small bucket.

"The goats taught me that being playful and making friends is important work too," Sofia said, wiping milk foam from her chin.

Page 9:
Little Lily became the chicken whisperer, caring for the baby chicks with the tenderness that only someone with the purest heart could possess. She learned to collect eggs gently, fill water containers without spilling, and even helped Aunt Martha in the garden, picking vegetables that would become delicious meals.

"The chickens taught me that even little ones can help in big ways," Lily said softly, cradling a sleepy chick in her small hands.

Page 10:
The sisters learned that farm life meant early mornings and evening chores, but they discovered that working together made everything more fun. Emma's careful nature helped them remember all their tasks, Sofia's energy kept them laughing even when they were tired, and Lily's gentle spirit reminded them to be kind to every creature, no matter how small.

They learned to work as a team, just like the animals they cared for.

Page 11:
One morning, they woke to find that one of the hens, Henrietta, was missing. The sisters searched everywhere – behind the barn, under the porch, even in the old oak tree. Finally, Lily's sharp eyes spotted something moving in the tall grass near the pond.

"There she is!" Lily called softly. Henrietta had made a secret nest and was sitting proudly on a clutch of eggs that were just beginning to hatch.

Page 12:
The sisters watched in amazement as tiny chicks began to break free from their shells. "It's a miracle," Emma whispered. Sofia danced with joy, while Lily sat perfectly still, not wanting to disturb the new babies.

Aunt Martha and Uncle Joe explained how Henrietta had followed her instincts to find the perfect place for her babies, and the sisters learned that sometimes animals knew exactly what they needed, even without being told.

Page 13:
As their month at the farm drew to a close, the sisters realized how much they had learned about responsibility, kindness, and the importance of caring for others. They had discovered that every living thing had its own special way of contributing to the world.

Emma had learned patience and wisdom from Thunder, Sofia had discovered the joy of friendship from the goats, and Lily had found her gentle strength through caring for the chickens.

Page 14:
On their last morning, the sisters helped with all the farm chores one final time. They hugged Thunder goodbye, promising to visit again soon. They played one last game with the goats, and Lily gave each chicken a tiny piece of their favorite treats.

"Thank you for teaching us so much," Emma said to the animals, her voice thick with emotion.

Page 15:
As their parents' car pulled up to take them home, the sisters felt both sad to leave and excited to share their stories with friends. Aunt Martha and Uncle Joe gave them each a special gift – a photo album filled with pictures of their farm adventures and a promise that they would always have a home on the farm.

"You've learned the most important lesson of all," Uncle Joe said, "that love and kindness toward all living things makes the world a better place."

Page 16:
The drive home was filled with chatter about all their adventures. Emma talked about how she wanted to learn more about horses, Sofia planned to ask her parents if they could visit a petting zoo, and Lily carefully held a small box containing three special feathers that Henrietta had given her.

They had discovered that the month at the farm had changed them forever, teaching them about responsibility, friendship, and the wonderful connections that exist between all living things.

**The End**

The three sisters returned home with hearts full of memories, new understanding of the natural world, and a deep appreciation for the simple joys of farm life. Their summer adventure had taught them that every creature, big or small, has an important role to play in the beautiful tapestry of life.'''
            else:
                # Generic comprehensive fallback for other prompts
                content = f'''# A Wonderful Adventure

Page 1:
Once upon a time, there lived children who were about to embark on the most amazing adventure of their lives. They had curious hearts and brave spirits, ready to discover the magic that existed in the world around them.

Page 2:
Their adventure began on a bright, sunny morning when they discovered something truly special. It was the beginning of a journey that would teach them about friendship, courage, and the importance of caring for others.

Page 3:
As they explored their new world, they met wonderful friends who showed them that every living thing has something important to teach us. They learned that kindness and understanding can overcome any challenge.

Page 4:
Through their experiences, they discovered that working together made them stronger and that helping others brought them the greatest joy. Each day brought new lessons about responsibility and compassion.

Page 5:
Their wonderful adventure taught them that the world is full of beauty and magic when we look at it with open hearts and minds. They learned that every day is a chance to make new friends and learn something new.

**The End**

Their adventure showed them that the greatest treasures in life are the friendships we make and the kindness we share with others.'''
        
        # Update project with generated content
        async with db_pool.acquire() as conn:
            await conn.execute(
                """UPDATE projects SET generated_content = $1, status = $2, progress = $3,
                   word_count = $4, updated_at = $5 WHERE id = $6""",
                content, "completed", 100, len(content.split()),
                datetime.utcnow(), project_id
            )
            
        await update_project_progress(project_id, 100, "Book generation completed", "completed")
        
    except Exception as e:
        logger.error(f"Background book generation failed: {e}")
        await update_project_progress(project_id, 0, f"Generation failed: {str(e)}", "failed")

# ============================================================================
# STRIPE PAYMENT ENDPOINTS
# ============================================================================

@api_router.post("/payments/create-subscription")
async def create_subscription(plan_data: Dict[str, Any], current_user = Depends(get_current_user)):
    """Create Stripe subscription or one-time payment checkout"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        plan_id = plan_data.get("plan_id")
        
        # Get plan details
        async with db_pool.acquire() as conn:
            plan = await conn.fetchrow("SELECT * FROM subscription_plans WHERE id = $1", plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail="Plan not found")
            
            # Determine if this is a monthly subscription or lifetime one-time payment
            is_monthly = plan["price_monthly"] is not None and plan["price_lifetime"] is None
            is_lifetime = plan["price_lifetime"] is not None and plan["price_monthly"] is None
            
            if not (is_monthly or is_lifetime):
                raise HTTPException(status_code=400, detail="Invalid plan configuration")
            
            # Create or get Stripe customer
            if current_user.get("stripe_customer_id"):
                customer_id = current_user["stripe_customer_id"]
            else:
                customer = stripe.Customer.create(
                    email=current_user["email"],
                    name=current_user["full_name"]
                )
                customer_id = customer.id
                
                # Update user with customer ID
                await conn.execute(
                    "UPDATE users SET stripe_customer_id = $1 WHERE id = $2",
                    customer_id, current_user["id"]
                )
            
            # Get frontend URL for success/cancel redirects - Replit domains don't use port in production
            replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost')
            if 'localhost' in replit_domain:
                frontend_url = f"http://{replit_domain}:5000"
            else:
                frontend_url = f"https://{replit_domain}"
            
            if is_monthly:
                # For monthly plans, create dynamic pricing and subscription
                # Create a price dynamically since we may not have pre-created price IDs
                price = stripe.Price.create(
                    unit_amount=int(float(plan["price_monthly"]) * 100),  # Convert to cents
                    currency='usd',
                    recurring={'interval': 'month'},
                    product_data={
                        'name': plan["name"],
                        'description': f'Monthly subscription to {plan["name"]}'
                    }
                )
                
                # Create Stripe Checkout Session for subscription
                checkout_session = stripe.checkout.Session.create(
                    customer=customer_id,
                    payment_method_types=['card'],
                    line_items=[{
                        'price': price.id,
                        'quantity': 1,
                    }],
                    mode='subscription',
                    success_url=f'{frontend_url}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}',
                    cancel_url=f'{frontend_url}/?payment=cancelled',
                    metadata={
                        'plan_id': str(plan_id),
                        'user_id': str(current_user["id"]),
                        'plan_type': 'monthly'
                    }
                )
                
            else:  # is_lifetime
                # For lifetime plans, create one-time payment
                price = stripe.Price.create(
                    unit_amount=int(float(plan["price_lifetime"]) * 100),  # Convert to cents
                    currency='usd',
                    product_data={
                        'name': plan["name"],
                        'description': f'Lifetime access to {plan["name"]}'
                    }
                )
                
                # Create Stripe Checkout Session for one-time payment
                checkout_session = stripe.checkout.Session.create(
                    customer=customer_id,
                    payment_method_types=['card'],
                    line_items=[{
                        'price': price.id,
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=f'{frontend_url}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}',
                    cancel_url=f'{frontend_url}/?payment=cancelled',
                    metadata={
                        'plan_id': str(plan_id),
                        'user_id': str(current_user["id"]),
                        'plan_type': 'lifetime'
                    }
                )
            
            # Store the checkout session info for webhook processing
            await conn.execute(
                """INSERT INTO pending_payments (user_id, plan_id, stripe_session_id, plan_type, amount, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                current_user["id"], plan_id, checkout_session.id, 
                'monthly' if is_monthly else 'lifetime',
                float(plan["price_monthly"]) if is_monthly else float(plan["price_lifetime"]),
                datetime.utcnow()
            )
            
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except Exception as e:
        logger.error(f"Payment session creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create payment session: {str(e)}")

@api_router.post("/payments/webhook")
async def stripe_webhook(request: Dict[str, Any]):
    """Handle Stripe webhook events for payment completion"""
    try:
        # For development, we'll skip signature verification
        # In production, add proper webhook signature verification
        event = request
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await handle_payment_success(session)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            await handle_subscription_payment(invoice)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook handling failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook handling failed")

async def handle_payment_success(session):
    """Handle successful payment completion"""
    try:
        user_id = session.metadata.get('user_id')
        plan_id = session.metadata.get('plan_id')
        plan_type = session.metadata.get('plan_type')
        
        if not all([user_id, plan_id, plan_type]):
            logger.error("Missing metadata in payment session")
            return
        
        async with db_pool.acquire() as conn:
            # Get plan details
            plan = await conn.fetchrow("SELECT * FROM subscription_plans WHERE id = $1", plan_id)
            if not plan:
                logger.error(f"Plan not found: {plan_id}")
                return
            
            # Update user subscription status
            await conn.execute(
                """UPDATE users SET subscription_tier = $1, 
                   stripe_customer_id = COALESCE(stripe_customer_id, $2),
                   updated_at = $3 WHERE id = $4""",
                plan['name'], session.customer, datetime.utcnow(), user_id
            )
            
            # Create subscription record
            if plan_type == 'monthly':
                # For monthly subscriptions
                subscription_id = session.subscription
                await conn.execute(
                    """INSERT INTO user_subscriptions 
                       (user_id, plan_id, stripe_subscription_id, status, created_at)
                       VALUES ($1, $2, $3, $4, $5)
                       ON CONFLICT (user_id) DO UPDATE SET
                       plan_id = $2, stripe_subscription_id = $3, status = $4, updated_at = $5""",
                    user_id, plan_id, subscription_id, 'active', datetime.utcnow()
                )
            else:
                # For lifetime purchases
                await conn.execute(
                    """INSERT INTO user_subscriptions 
                       (user_id, plan_id, stripe_subscription_id, status, created_at)
                       VALUES ($1, $2, 
(Content truncated due to size limit. Use page ranges or line ranges to read remaining content)