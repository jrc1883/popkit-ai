import { getRedis } from '../services/redis';
/**
 * Billing Routes - Stripe Integration
 *
 * Part of Issue #130 (Stripe Checkout Integration)
 * Parent: Epic #125 (User Signup & Billing)
 */

import { Hono } from 'hono';
import Stripe from 'stripe';
import type { Env, Variables, UserData, Tier } from '../types';
import {
  sendEmail,
  generateReceiptEmail,
  generatePaymentFailedEmail,
  generateCancellationEmail,
} from '../services/email';

const billing = new Hono<{ Bindings: Env; Variables: Variables }>();

// =============================================================================
// HELPERS
// =============================================================================

/**
 * Get Stripe client.
 */
function getStripe(env: Env): Stripe {
  if (!env.STRIPE_SECRET_KEY) {
    throw new Error('Stripe not configured');
  }
  return new Stripe(env.STRIPE_SECRET_KEY);
}

/**
 * Get price ID for a tier.
 */
function getPriceId(env: Env, tier: 'pro' | 'team'): string {
  if (tier === 'pro') {
    if (!env.STRIPE_PRICE_PRO) throw new Error('Pro price not configured');
    return env.STRIPE_PRICE_PRO;
  }
  if (!env.STRIPE_PRICE_TEAM) throw new Error('Team price not configured');
  return env.STRIPE_PRICE_TEAM;
}

/**
 * Map Stripe status to tier.
 */
function getTierFromSubscription(status: string, priceId: string, env: Env): Tier {
  if (status !== 'active' && status !== 'trialing') {
    return 'free';
  }
  if (priceId === env.STRIPE_PRICE_TEAM) return 'team';
  if (priceId === env.STRIPE_PRICE_PRO) return 'pro';
  return 'free';
}

// =============================================================================
// ROUTES
// =============================================================================

/**
 * POST /v1/billing/checkout
 *
 * Create a Stripe Checkout session for upgrading.
 * Requires session token or API key auth.
 */
billing.post('/checkout', async (c) => {
  // COMING SOON: Billing is not yet accepting customers
  // Remove this block when ready to launch
  return c.json(
    {
      error: 'Billing coming soon',
      message: 'PopKit Pro and Team plans are not yet available. Join the waitlist at https://popkit.dev',
      comingSoon: true,
      waitlistUrl: 'https://popkit.dev/waitlist',
    },
    503 // Service Unavailable
  );

  /* Uncomment when ready to accept customers
  const stripe = getStripe(c.env);
  const redis = getRedis(c);

  // Get user from auth
  const apiKey = c.get('apiKey');
  if (!apiKey) {
    return c.json({ error: 'Authentication required' }, 401);
  }

  // Get user data
  const userJson = await redis.get<string>(`popkit:user:${apiKey.userId}`);
  if (!userJson) {
    return c.json({ error: 'User not found' }, 404);
  }
  const user: UserData = JSON.parse(userJson);

  // Parse request
  const body = await c.req.json<{ plan: 'pro' | 'team'; successUrl?: string; cancelUrl?: string }>();
  const plan = body.plan || 'pro';

  if (plan !== 'pro' && plan !== 'team') {
    return c.json({ error: 'Invalid plan. Must be "pro" or "team"' }, 400);
  }

  // Create or get Stripe customer
  let customerId = user.stripeCustomerId;

  if (!customerId) {
    const customer = await stripe.customers.create({
      email: user.email,
      metadata: {
        popkitUserId: user.id,
      },
    });
    customerId = customer.id;

    // Save customer ID
    user.stripeCustomerId = customerId;
    user.updatedAt = new Date().toISOString();
    await redis.set(`popkit:user:${user.id}`, JSON.stringify(user));
  }

  // Create checkout session
  const session = await stripe.checkout.sessions.create({
    customer: customerId,
    mode: 'subscription',
    line_items: [
      {
        price: getPriceId(c.env, plan),
        quantity: 1,
      },
    ],
    success_url: body.successUrl || 'https://popkit.dev/success?session_id={CHECKOUT_SESSION_ID}',
    cancel_url: body.cancelUrl || 'https://popkit.dev/pricing',
    metadata: {
      popkitUserId: user.id,
      plan,
    },
  });

  return c.json({
    checkoutUrl: session.url,
    sessionId: session.id,
  });
  */
});

/**
 * POST /v1/billing/webhook
 *
 * Handle Stripe webhook events.
 * This endpoint is public but verifies webhook signatures.
 */
billing.post('/webhook', async (c) => {
  const stripe = getStripe(c.env);
  const redis = getRedis(c);

  // Get raw body for signature verification
  const rawBody = await c.req.text();
  const signature = c.req.header('stripe-signature');

  if (!signature || !c.env.STRIPE_WEBHOOK_SECRET) {
    return c.json({ error: 'Missing signature or webhook secret' }, 400);
  }

  // Verify webhook signature
  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(rawBody, signature, c.env.STRIPE_WEBHOOK_SECRET);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    return c.json({ error: 'Invalid signature' }, 400);
  }

  // Handle events
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      const userId = session.metadata?.popkitUserId;
      const plan = session.metadata?.plan as 'pro' | 'team' | undefined;

      if (userId && plan) {
        // Get user
        const userJson = await redis.get<string>(`popkit:user:${userId}`);
        if (userJson) {
          const user: UserData = JSON.parse(userJson);

          // Update tier
          user.tier = plan;
          user.stripeSubscriptionId = session.subscription as string;
          user.updatedAt = new Date().toISOString();

          await redis.set(`popkit:user:${userId}`, JSON.stringify(user));

          // Update API key tiers
          const userKeys = await redis.smembers<string[]>(`popkit:user:${userId}:keys`);
          for (const key of userKeys || []) {
            const keyDataJson = await redis.hget<string>('popkit:keys', key);
            if (keyDataJson) {
              const keyData = typeof keyDataJson === 'string' ? JSON.parse(keyDataJson) : keyDataJson;
              keyData.tier = plan;
              await redis.hset('popkit:keys', { [key]: JSON.stringify(keyData) });
            }
          }

          console.log(`User ${userId} upgraded to ${plan}`);

          // Send receipt email
          if (c.env.RESEND_API_KEY) {
            const amount = plan === 'pro' ? '$9.00' : '$29.00';
            const renewalDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString(
              'en-US',
              { month: 'long', day: 'numeric', year: 'numeric' }
            );
            const receiptEmail = generateReceiptEmail({
              email: user.email,
              amount,
              plan: plan.charAt(0).toUpperCase() + plan.slice(1),
              renewalDate,
            });
            sendEmail(c.env.RESEND_API_KEY, receiptEmail).catch((err) => {
              console.error('Failed to send receipt email:', err);
            });
          }
        }
      }
      break;
    }

    case 'customer.subscription.updated': {
      const subscription = event.data.object as Stripe.Subscription;
      const customerId = subscription.customer as string;

      // Find user by Stripe customer ID
      // Note: In production, you'd want an index for this
      const customer = await stripe.customers.retrieve(customerId);
      if (customer.deleted) break;

      const userId = customer.metadata?.popkitUserId;
      if (!userId) break;

      const userJson = await redis.get<string>(`popkit:user:${userId}`);
      if (!userJson) break;

      const user: UserData = JSON.parse(userJson);
      const priceId = subscription.items.data[0]?.price?.id;

      if (priceId) {
        const newTier = getTierFromSubscription(subscription.status, priceId, c.env);
        user.tier = newTier;
        user.updatedAt = new Date().toISOString();
        await redis.set(`popkit:user:${userId}`, JSON.stringify(user));

        // Update API key tiers
        const userKeys = await redis.smembers<string[]>(`popkit:user:${userId}:keys`);
        for (const key of userKeys || []) {
          const keyDataJson = await redis.hget<string>('popkit:keys', key);
          if (keyDataJson) {
            const keyData = typeof keyDataJson === 'string' ? JSON.parse(keyDataJson) : keyDataJson;
            keyData.tier = newTier;
            await redis.hset('popkit:keys', { [key]: JSON.stringify(keyData) });
          }
        }

        console.log(`User ${userId} subscription updated to ${newTier}`);
      }
      break;
    }

    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription;
      const customerId = subscription.customer as string;

      const customer = await stripe.customers.retrieve(customerId);
      if (customer.deleted) break;

      const userId = customer.metadata?.popkitUserId;
      if (!userId) break;

      const userJson = await redis.get<string>(`popkit:user:${userId}`);
      if (!userJson) break;

      const user: UserData = JSON.parse(userJson);
      user.tier = 'free';
      user.stripeSubscriptionId = undefined;
      user.updatedAt = new Date().toISOString();
      await redis.set(`popkit:user:${userId}`, JSON.stringify(user));

      // Update API key tiers to free
      const userKeys = await redis.smembers<string[]>(`popkit:user:${userId}:keys`);
      for (const key of userKeys || []) {
        const keyDataJson = await redis.hget<string>('popkit:keys', key);
        if (keyDataJson) {
          const keyData = typeof keyDataJson === 'string' ? JSON.parse(keyDataJson) : keyDataJson;
          keyData.tier = 'free';
          await redis.hset('popkit:keys', { [key]: JSON.stringify(keyData) });
        }
      }

      console.log(`User ${userId} subscription cancelled, downgraded to free`);

      // Send cancellation email
      if (c.env.RESEND_API_KEY) {
        // Access current_period_end via type assertion (Stripe types don't include all properties)
        const periodEnd = (subscription as unknown as { current_period_end: number }).current_period_end;
        const endDate = new Date(periodEnd * 1000).toLocaleDateString(
          'en-US',
          { month: 'long', day: 'numeric', year: 'numeric' }
        );
        // Use the plan that was cancelled, not current tier (which is now 'free')
        const cancellationEmail = generateCancellationEmail({
          email: user.email,
          plan: 'Pro', // subscription was cancelled, so we know it was a paid plan
          endDate,
        });
        sendEmail(c.env.RESEND_API_KEY, cancellationEmail).catch((err) => {
          console.error('Failed to send cancellation email:', err);
        });
      }
      break;
    }

    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      console.warn(`Payment failed for customer ${invoice.customer}`);

      // Send payment failed email
      if (c.env.RESEND_API_KEY && invoice.customer) {
        const customerId = invoice.customer as string;
        const customer = await stripe.customers.retrieve(customerId);
        if (!customer.deleted && customer.email) {
          // Create billing portal session for update
          const portalSession = await stripe.billingPortal.sessions.create({
            customer: customerId,
            return_url: 'https://popkit.dev/dashboard',
          });

          const paymentFailedEmail = generatePaymentFailedEmail({
            email: customer.email,
            plan: 'Pro',
            updateUrl: portalSession.url,
          });
          sendEmail(c.env.RESEND_API_KEY, paymentFailedEmail).catch((err) => {
            console.error('Failed to send payment failed email:', err);
          });
        }
      }
      break;
    }

    default:
      console.log(`Unhandled event type: ${event.type}`);
  }

  return c.json({ received: true });
});

/**
 * GET /v1/billing/portal
 *
 * Get a Stripe Customer Portal URL for managing subscription.
 */
billing.get('/portal', async (c) => {
  const stripe = getStripe(c.env);
  const redis = getRedis(c);

  // Get user from auth
  const apiKey = c.get('apiKey');
  if (!apiKey) {
    return c.json({ error: 'Authentication required' }, 401);
  }

  // Get user data
  const userJson = await redis.get<string>(`popkit:user:${apiKey.userId}`);
  if (!userJson) {
    return c.json({ error: 'User not found' }, 404);
  }
  const user: UserData = JSON.parse(userJson);

  if (!user.stripeCustomerId) {
    return c.json({ error: 'No billing account found. Please upgrade first.' }, 400);
  }

  // Create portal session
  const portalSession = await stripe.billingPortal.sessions.create({
    customer: user.stripeCustomerId,
    return_url: 'https://popkit.dev/dashboard',
  });

  return c.json({
    portalUrl: portalSession.url,
  });
});

/**
 * GET /v1/billing/subscription
 *
 * Get current subscription status.
 */
billing.get('/subscription', async (c) => {
  const stripe = getStripe(c.env);
  const redis = getRedis(c);

  // Get user from auth
  const apiKey = c.get('apiKey');
  if (!apiKey) {
    return c.json({ error: 'Authentication required' }, 401);
  }

  // Get user data
  const userJson = await redis.get<string>(`popkit:user:${apiKey.userId}`);
  if (!userJson) {
    return c.json({ error: 'User not found' }, 404);
  }
  const user: UserData = JSON.parse(userJson);

  // If no subscription, return free tier
  if (!user.stripeSubscriptionId) {
    return c.json({
      tier: user.tier,
      status: 'none',
      currentPeriodEnd: null,
    });
  }

  // Get subscription details from Stripe
  try {
    const subscription = await stripe.subscriptions.retrieve(user.stripeSubscriptionId);
    const periodEnd = (subscription as unknown as { current_period_end: number }).current_period_end;
    const cancelAt = (subscription as unknown as { cancel_at_period_end: boolean }).cancel_at_period_end;
    return c.json({
      tier: user.tier,
      status: subscription.status,
      currentPeriodEnd: periodEnd ? new Date(periodEnd * 1000).toISOString() : null,
      cancelAtPeriodEnd: cancelAt,
    });
  } catch {
    return c.json({
      tier: user.tier,
      status: 'unknown',
      currentPeriodEnd: null,
    });
  }
});

export default billing;
