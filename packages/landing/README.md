# PopKit Landing Page

Marketing site, signup, login, and dashboard for PopKit Cloud.

## Stack

- **Framework**: Astro
- **Styling**: Tailwind CSS
- **Hosting**: Cloudflare Pages

## Development

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Deployment

The site is deployed to Cloudflare Pages:

```bash
# Build
npm run build

# Deploy (requires wrangler CLI and login)
npx wrangler pages deploy dist --project-name=popkit-landing
```

## Pages

| Path | Description |
|------|-------------|
| `/` | Marketing page with pricing |
| `/signup` | User registration |
| `/login` | User login |
| `/dashboard` | Account management |
| `/success` | Post-signup/checkout confirmation |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PUBLIC_API_URL` | PopKit Cloud API URL |
| `SITE_URL` | Production site URL (for sitemap, etc.) |

## Connecting to Cloud API

All authentication and data fetching goes through the PopKit Cloud API at `https://popkit-cloud-api.joseph-cannon.workers.dev`.

Endpoints used:
- `POST /v1/auth/signup` - Create account
- `POST /v1/auth/login` - Login
- `GET /v1/auth/me` - Get user info
- `GET /v1/account/keys` - List API keys
- `POST /v1/account/keys` - Create API key
- `GET /v1/usage/summary` - Usage statistics
- `GET /v1/billing/portal` - Stripe billing portal URL
