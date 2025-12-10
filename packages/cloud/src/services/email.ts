/**
 * Email Service
 *
 * Part of Issue #133 (Email Notifications)
 * Part of Epic #125 (User Signup & Billing)
 *
 * Sends transactional emails using Resend API.
 */

interface EmailData {
  to: string;
  subject: string;
  html: string;
  text?: string;
}

interface EmailResult {
  success: boolean;
  id?: string;
  error?: string;
}

/**
 * Send an email using Resend API.
 */
export async function sendEmail(
  apiKey: string,
  data: EmailData
): Promise<EmailResult> {
  try {
    const response = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        from: 'PopKit <noreply@popkit.dev>',
        to: data.to,
        subject: data.subject,
        html: data.html,
        text: data.text,
      }),
    });

    const result = await response.json() as { id?: string; message?: string };

    if (!response.ok) {
      return { success: false, error: result.message || 'Failed to send email' };
    }

    return { success: true, id: result.id };
  } catch (error) {
    return { success: false, error: String(error) };
  }
}

// =============================================================================
// EMAIL TEMPLATES
// =============================================================================

const BRAND_COLOR = '#7c3aed';
const FOOTER = `
  <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #e5e7eb; text-align: center; color: #6b7280; font-size: 12px;">
    <p>PopKit - AI-Powered Development Workflows</p>
    <p><a href="https://popkit.dev" style="color: ${BRAND_COLOR};">popkit.dev</a></p>
  </div>
`;

function baseTemplate(content: string): string {
  return `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PopKit</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1f2937; margin: 0; padding: 0; background-color: #f3f4f6;">
  <div style="max-width: 600px; margin: 0 auto; padding: 24px;">
    <div style="background-color: white; border-radius: 8px; padding: 32px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
      <div style="text-align: center; margin-bottom: 24px;">
        <h1 style="font-size: 24px; font-weight: bold; background: linear-gradient(to right, #7c3aed, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">PopKit</h1>
      </div>
      ${content}
      ${FOOTER}
    </div>
  </div>
</body>
</html>
  `.trim();
}

// =============================================================================
// WELCOME EMAIL
// =============================================================================

export interface WelcomeEmailData {
  email: string;
  apiKey: string;
  tier: string;
}

export function generateWelcomeEmail(data: WelcomeEmailData): EmailData {
  const isProTrial = data.tier === 'pro';

  const html = baseTemplate(`
    <h2 style="font-size: 20px; color: #1f2937; margin-bottom: 16px;">Welcome to PopKit!</h2>

    <p>Your account is ready. Here's your API key to unlock ${isProTrial ? 'premium' : ''} features in Claude Code:</p>

    <div style="background-color: #f3f4f6; border-radius: 8px; padding: 16px; margin: 24px 0; font-family: monospace;">
      <code style="word-break: break-all;">${data.apiKey}</code>
    </div>

    <h3 style="font-size: 16px; color: #1f2937; margin-top: 24px;">Getting Started</h3>
    <ol style="color: #4b5563; padding-left: 20px;">
      <li style="margin-bottom: 8px;">Set your API key: <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">export POPKIT_API_KEY=${data.apiKey.slice(0, 12)}...</code></li>
      <li style="margin-bottom: 8px;">Verify setup: <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">/popkit:account status</code></li>
      <li style="margin-bottom: 8px;">Start developing: <code style="background: #f3f4f6; padding: 2px 6px; border-radius: 4px;">/popkit:dev full "Your feature"</code></li>
    </ol>

    ${
      isProTrial
        ? `
    <div style="background-color: #f3e8ff; border-radius: 8px; padding: 16px; margin: 24px 0;">
      <p style="margin: 0; color: #7c3aed;"><strong>Your 14-day Pro trial has started!</strong></p>
      <p style="margin: 8px 0 0; color: #6b7280; font-size: 14px;">You have full access to Power Mode, custom generation, and unlimited patterns.</p>
    </div>
    `
        : ''
    }

    <div style="text-align: center; margin-top: 32px;">
      <a href="https://popkit.dev/dashboard" style="display: inline-block; background-color: ${BRAND_COLOR}; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">Go to Dashboard</a>
    </div>
  `);

  return {
    to: data.email,
    subject: `Welcome to PopKit${isProTrial ? ' Pro Trial' : ''}!`,
    html,
    text: `Welcome to PopKit!\n\nYour API key: ${data.apiKey}\n\nSet it with: export POPKIT_API_KEY=${data.apiKey}\n\nGet started at https://popkit.dev/dashboard`,
  };
}

// =============================================================================
// RECEIPT EMAIL
// =============================================================================

export interface ReceiptEmailData {
  email: string;
  amount: string;
  plan: string;
  renewalDate: string;
  invoiceUrl?: string;
}

export function generateReceiptEmail(data: ReceiptEmailData): EmailData {
  const html = baseTemplate(`
    <h2 style="font-size: 20px; color: #1f2937; margin-bottom: 16px;">Payment Received</h2>

    <p>Thank you for your payment! Here are the details:</p>

    <div style="background-color: #f3f4f6; border-radius: 8px; padding: 16px; margin: 24px 0;">
      <table style="width: 100%; border-collapse: collapse;">
        <tr>
          <td style="padding: 8px 0; color: #6b7280;">Plan</td>
          <td style="padding: 8px 0; text-align: right; font-weight: 600;">${data.plan}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #6b7280;">Amount</td>
          <td style="padding: 8px 0; text-align: right; font-weight: 600;">${data.amount}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; color: #6b7280;">Next renewal</td>
          <td style="padding: 8px 0; text-align: right;">${data.renewalDate}</td>
        </tr>
      </table>
    </div>

    ${
      data.invoiceUrl
        ? `
    <div style="text-align: center; margin-top: 24px;">
      <a href="${data.invoiceUrl}" style="color: ${BRAND_COLOR}; text-decoration: none;">View Invoice →</a>
    </div>
    `
        : ''
    }
  `);

  return {
    to: data.email,
    subject: `Payment received - PopKit ${data.plan}`,
    html,
    text: `Payment received for PopKit ${data.plan}\n\nAmount: ${data.amount}\nNext renewal: ${data.renewalDate}`,
  };
}

// =============================================================================
// EXPIRY WARNING EMAIL
// =============================================================================

export interface ExpiryWarningData {
  email: string;
  plan: string;
  expiryDate: string;
  daysLeft: number;
}

export function generateExpiryWarningEmail(data: ExpiryWarningData): EmailData {
  const html = baseTemplate(`
    <h2 style="font-size: 20px; color: #1f2937; margin-bottom: 16px;">Your subscription renews soon</h2>

    <p>Your PopKit ${data.plan} subscription will renew in <strong>${data.daysLeft} days</strong> on ${data.expiryDate}.</p>

    <p style="color: #6b7280;">If you'd like to make changes to your subscription, you can do so from your dashboard.</p>

    <div style="text-align: center; margin-top: 32px;">
      <a href="https://popkit.dev/dashboard" style="display: inline-block; background-color: ${BRAND_COLOR}; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">Manage Subscription</a>
    </div>
  `);

  return {
    to: data.email,
    subject: `Your PopKit ${data.plan} renews in ${data.daysLeft} days`,
    html,
    text: `Your PopKit ${data.plan} subscription renews in ${data.daysLeft} days on ${data.expiryDate}.\n\nManage at: https://popkit.dev/dashboard`,
  };
}

// =============================================================================
// PAYMENT FAILED EMAIL
// =============================================================================

export interface PaymentFailedData {
  email: string;
  plan: string;
  updateUrl: string;
}

export function generatePaymentFailedEmail(data: PaymentFailedData): EmailData {
  const html = baseTemplate(`
    <h2 style="font-size: 20px; color: #dc2626; margin-bottom: 16px;">Payment Failed</h2>

    <p>We couldn't process your payment for PopKit ${data.plan}.</p>

    <p style="color: #6b7280;">Please update your payment method to continue using premium features.</p>

    <div style="text-align: center; margin-top: 32px;">
      <a href="${data.updateUrl}" style="display: inline-block; background-color: #dc2626; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">Update Payment Method</a>
    </div>

    <p style="font-size: 14px; color: #6b7280; margin-top: 24px;">If you believe this is an error, please contact support@popkit.dev.</p>
  `);

  return {
    to: data.email,
    subject: 'Action required: Update your payment method',
    html,
    text: `Payment failed for PopKit ${data.plan}.\n\nUpdate your payment method: ${data.updateUrl}`,
  };
}

// =============================================================================
// CANCELLATION EMAIL
// =============================================================================

export interface CancellationData {
  email: string;
  plan: string;
  endDate: string;
  feedbackUrl?: string;
}

export function generateCancellationEmail(data: CancellationData): EmailData {
  const html = baseTemplate(`
    <h2 style="font-size: 20px; color: #1f2937; margin-bottom: 16px;">We're sorry to see you go</h2>

    <p>Your PopKit ${data.plan} subscription has been cancelled.</p>

    <p>You'll continue to have access to premium features until <strong>${data.endDate}</strong>. After that, your account will revert to the free tier.</p>

    <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; margin: 24px 0;">
      <p style="margin: 0; color: #92400e;"><strong>What you'll lose:</strong></p>
      <ul style="margin: 8px 0 0; padding-left: 20px; color: #92400e;">
        <li>Hosted Redis Power Mode</li>
        <li>Persistent sessions</li>
        <li>Custom MCP generation</li>
        <li>Unlimited pattern access</li>
      </ul>
    </div>

    ${
      data.feedbackUrl
        ? `
    <p style="color: #6b7280;">We'd love to hear your feedback on how we can improve:</p>
    <div style="text-align: center; margin-top: 16px;">
      <a href="${data.feedbackUrl}" style="color: ${BRAND_COLOR}; text-decoration: none;">Share Feedback →</a>
    </div>
    `
        : ''
    }

    <p style="color: #6b7280; margin-top: 24px;">You can resubscribe anytime from your dashboard.</p>
  `);

  return {
    to: data.email,
    subject: 'Your PopKit subscription has been cancelled',
    html,
    text: `Your PopKit ${data.plan} subscription has been cancelled.\n\nYou'll have access until ${data.endDate}.\n\nResubscribe anytime at https://popkit.dev/dashboard`,
  };
}
