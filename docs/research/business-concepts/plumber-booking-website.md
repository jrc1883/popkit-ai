# Plumber Booking Website - Implementation Plan

**Project**: Local Plumber Website with AI Scheduling & Google Maps SEO
**Research Date**: December 2025
**Status**: Research Complete - Ready for Implementation
**Target Tech Stack**: Next.js 14+ with Supabase + AI Phone Agent

---

## 📋 Executive Summary

This plan outlines a modern, full-featured plumber booking website that combines:
- **Professional Service Site**: Marketing-focused homepage with service showcase
- **AI Phone Answering**: 24/7 automated call handling for appointments
- **Smart Booking System**: Real-time appointment scheduling with conflict detection
- **Google Maps SEO**: Optimized local search presence and booking widgets
- **Backend Intelligence**: Admin dashboard for dispatch, calendar management, and analytics

The solution leverages your ElShaddai infrastructure to build rapidly with proven patterns.

---

## 🎯 Market Analysis (November-December 2025)

### Industry Leaders & Their Approaches

#### 1. **AI Answering Services** (Leading Edge)
- **Eden AI**: Real-time calendar integration, call classification (emergency/routine), 75% reduction in scheduling time
- **Rosie AI**: Human-sounding voice, instant summaries, SMS confirmations
- **Smith.ai**: 24/7 emergency prioritization, lead capture, CRM integration
- **IsOn24**: Voice assistant that learns your business communication style
- **Dialzara**: Emergency response capabilities with SMS integration

**Key Finding**: Home service companies miss ~27% of calls = $1,200 per missed call in lost revenue

#### 2. **Plumbing-Specific Booking Software** (Mature Market)
- **ServiceTitan**: Industry standard with dispatch optimization
- **Housecall Pro**: All-in-one field service management
- **Convin AI**: Intelligent plumber-to-job matching based on location/skills
- **Lunacal**: Zone-based booking, no-show reduction by 30% via reminders

**Key Finding**: AI-powered scheduling speeds up process by 3x and reduces booking errors

#### 3. **Google Maps Integration** (Critical for Local SEO)
- **Google Business Profile Reserve**: Direct booking widget in search results
- **Local Pack Visibility**: Top 3 results generate 70% of plumbing leads
- **2025 Trend**: Comprehensive Local SEO services emerging (Boomcycle, etc.)
- **Best Practice**: Map widget + messaging + service areas + appointment links

### Your Competitive Advantage
Building on ElShaddai gives you:
- Full control over AI voice agent (vs. expensive SaaS)
- Custom booking logic optimized for this plumber's workflow
- Integrated tech stack (no SaaS silo issues)
- Scalable to multiple plumbers later

---

## 🏗️ Recommended Architecture

### Three-Tier System

```
┌─────────────────────────────────────────────┐
│   PUBLIC WEBSITE LAYER (Astro)              │
│   - Marketing homepage                      │
│   - Service pages                           │
│   - Google Maps embedding                   │
│   - Public booking form                     │
│   - SEO optimization                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   APPLICATION LAYER (Next.js 14)            │
│   - Booking system (calendar)               │
│   - Customer CRM                            │
│   - Admin dashboard                         │
│   - API for voice agent                     │
│   - Real-time updates (WebSocket)           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│   DATA & SERVICES LAYER                     │
│   - Supabase PostgreSQL (appointments)      │
│   - Redis (real-time calendar state)        │
│   - AI Voice Agent (Python/Claude)          │
│   - Google Maps API integration             │
│   - Calendar sync (Google Calendar)         │
└─────────────────────────────────────────────┘
```

### Why This Stack?

**Astro for Public Website**
- ✅ Static site generation for SEO perfection
- ✅ Reusable components (align with Portfolio Builder)
- ✅ Minimal JavaScript = blazing fast Google PageSpeed
- ✅ Great for content-focused marketing pages

**Next.js for Web Application**
- ✅ Full-stack (front + back in one repo)
- ✅ Proven pattern in your Genesis app
- ✅ Supabase integration battle-tested
- ✅ WebSocket support for real-time calendar
- ✅ API routes for voice agent communication

**Supabase for Database**
- ✅ PostgreSQL reliability
- ✅ Row-Level Security for multi-tenant later
- ✅ Real-time subscriptions (calendar updates)
- ✅ Auth built-in
- ✅ Already proven in Genesis + Reseller Central

**AI Voice Agent**
- ✅ Use Claude 3.5 Sonnet API (via Anthropic SDK)
- ✅ Python backend (FastAPI) like your aiproxy app
- ✅ Connect to Twilio/Telnyx for phone integration
- ✅ Can use your voice-clone-app infrastructure as reference

---

## 📁 Proposed Project Structure

```
apps/plumber-booking/
├── web/                          # Astro marketing site
│   ├── src/
│   │   ├── pages/               # Astro pages
│   │   │   ├── index.astro      # Homepage
│   │   │   ├── services/        # Service catalog
│   │   │   ├── about/           # About page
│   │   │   ├── testimonials/    # Social proof
│   │   │   └── blog/            # Local SEO blog
│   │   ├── components/          # Astro components
│   │   │   ├── ServiceCard.astro
│   │   │   ├── PricingTable.astro
│   │   │   ├── ReviewCarousel.astro
│   │   │   ├── MapEmbed.astro
│   │   │   └── BookingWidget.astro
│   │   ├── layouts/
│   │   └── styles/
│   ├── public/                  # Static assets
│   ├── astro.config.mjs
│   └── package.json
│
├── app/                          # Next.js 14 web application
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/          # Login/registration
│   │   │   ├── (admin)/         # Admin dashboard
│   │   │   │   ├── dashboard/   # Overview
│   │   │   │   ├── calendar/    # Schedule management
│   │   │   │   ├── appointments/# View/edit bookings
│   │   │   │   ├── customers/   # CRM
│   │   │   │   └── analytics/   # Performance metrics
│   │   │   ├── api/
│   │   │   │   ├── appointments/POST, GET, PATCH
│   │   │   │   ├── calendar/    # Availability endpoint
│   │   │   │   ├── voice/       # AI voice agent API
│   │   │   │   ├── customers/   # CRM API
│   │   │   │   └── analytics/   # Stats API
│   │   │   ├── booking/         # Public booking page (embedded/modal)
│   │   │   └── layout.tsx
│   │   ├── components/
│   │   │   ├── BookingForm.tsx
│   │   │   ├── Calendar.tsx      # Interactive calendar
│   │   │   ├── ServiceSelector.tsx
│   │   │   ├── TimeSlots.tsx
│   │   │   └── admin/
│   │   │       ├── Dashboard.tsx
│   │   │       ├── ScheduleManager.tsx
│   │   │       └── CustomerList.tsx
│   │   ├── lib/
│   │   │   ├── supabase/
│   │   │   ├── api-client/
│   │   │   ├── voice-agent/     # Communicates with Python service
│   │   │   ├── calendar/        # Conflict detection, availability
│   │   │   └── types.ts         # Shared types
│   │   └── hooks/
│   │       ├── useAppointments.ts
│   │       ├── useCalendar.ts
│   │       └── useVoiceAgent.ts
│   ├── package.json
│   └── next.config.js
│
├── services/                     # Python voice agent
│   ├── app/
│   │   ├── main.py             # FastAPI entry point
│   │   ├── routes/
│   │   │   ├── phone.py        # Phone call handling
│   │   │   ├── scheduling.py   # Appointment logic
│   │   │   └── analytics.py    # Call metrics
│   │   ├── agents/
│   │   │   └── booking_agent.py # Claude AI agent
│   │   ├── services/
│   │   │   ├── supabase_client.py
│   │   │   ├── twilio_client.py
│   │   │   └── calendar_manager.py
│   │   └── models/
│   │       ├── phone_call.py
│   │       └── appointment.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── database/                    # Supabase migrations
│   ├── migrations/
│   │   ├── 001_init_appointments.sql
│   │   ├── 002_add_customers.sql
│   │   ├── 003_add_services.sql
│   │   ├── 004_add_call_logs.sql
│   │   └── 005_add_availability.sql
│   └── seeds/
│       └── demo_data.sql
│
├── docs/                        # Project documentation
│   ├── SETUP.md
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── VOICE_AGENT.md
│   └── DEPLOYMENT.md
│
├── scripts/                     # Automation
│   ├── seed-db.sh
│   ├── setup-voice-agent.sh
│   └── deploy-to-vercel.sh
│
├── package.json                # Monorepo root
├── pnpm-workspace.yaml         # Link to ElShaddai workspaces
└── README.md
```

---

## 🗄️ Database Schema (Supabase PostgreSQL)

### Core Tables

```sql
-- Service definitions
CREATE TABLE services (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  description TEXT,
  duration_minutes INTEGER,
  price DECIMAL(10, 2),
  service_category VARCHAR(50)
);

-- Time slots (plumber availability)
CREATE TABLE availability (
  id UUID PRIMARY KEY,
  day_of_week INTEGER (0-6),
  start_time TIME,
  end_time TIME,
  max_appointments INTEGER,
  is_available BOOLEAN,
  created_at TIMESTAMP
);

-- Appointments (bookings)
CREATE TABLE appointments (
  id UUID PRIMARY KEY,
  customer_id UUID,
  service_id UUID,
  scheduled_time TIMESTAMP,
  duration_minutes INTEGER,
  status VARCHAR(50), -- pending, confirmed, completed, cancelled
  notes TEXT,
  phone_number VARCHAR(20),
  email VARCHAR(255),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Customers
CREATE TABLE customers (
  id UUID PRIMARY KEY,
  phone_number VARCHAR(20) UNIQUE,
  email VARCHAR(255),
  name VARCHAR(255),
  address TEXT,
  preferred_time VARCHAR(50),
  notes TEXT,
  created_at TIMESTAMP
);

-- Call logs (from AI voice agent)
CREATE TABLE call_logs (
  id UUID PRIMARY KEY,
  phone_number VARCHAR(20),
  call_duration_seconds INTEGER,
  transcription TEXT,
  appointment_created BOOLEAN,
  appointment_id UUID,
  call_status VARCHAR(50),
  created_at TIMESTAMP
);

-- Services history
CREATE TABLE appointment_history (
  id UUID PRIMARY KEY,
  appointment_id UUID,
  old_status VARCHAR(50),
  new_status VARCHAR(50),
  changed_at TIMESTAMP,
  changed_by VARCHAR(255)
);
```

---

## 🎤 AI Voice Agent Capabilities

### What the Claude-Powered Agent Can Do

**Call Handling**
- ✅ Answer incoming calls with professional greeting
- ✅ Classify calls: new booking, reschedule, cancel, emergency, general inquiry
- ✅ Extract customer information: name, phone, address, service type
- ✅ Handle interruptions gracefully

**Booking Intelligence**
- ✅ Check real-time availability from database
- ✅ Suggest optimal time slots based on service type
- ✅ Detect scheduling conflicts
- ✅ Ask qualifying questions ("What area? How urgent? Any water damage?")
- ✅ Confirm appointment details back to caller

**Special Scenarios**
- ✅ Emergency detection (pipe burst, gas smell) → prioritize & escalate
- ✅ After-hours calls → offer next-day slots or emergency option
- ✅ Existing customer recognition → personalized service
- ✅ Multi-call management (callback if busy)

**Integration Points**
- ✅ Real-time calendar queries to Next.js API
- ✅ Appointment creation in Supabase
- ✅ SMS confirmation to customer
- ✅ Email notification to plumber

### Voice Infrastructure
- **Phone Service**: Twilio or Telnyx (incoming numbers)
- **Voice Provider**: ElevenLabs or Google Cloud (text-to-speech)
- **Speech Recognition**: Deepgram or Google Cloud
- **Backend**: FastAPI + Claude 3.5 Sonnet API
- **Connection**: Webhook from phone service → FastAPI → Claude

---

## 📈 Implementation Phases

### Phase 1: Foundation (Weeks 1-2)
**Deliverable**: Working booking website with manual scheduling

**Tasks**:
1. Set up Supabase database with schema
2. Create Astro marketing website with:
   - Homepage with service showcase
   - About page with testimonials
   - Service pages with descriptions
   - Google Business Profile optimization
3. Create Next.js booking application:
   - Simple appointment form
   - Calendar view showing availability
   - Admin dashboard for schedule management
4. Supabase auth (admin login)
5. Basic email notifications

**Tech Decisions**:
- Database migrations managed in code
- Use Genesis architecture as reference for auth
- Use Portfolio Builder components as model for Astro setup

### Phase 2: AI Voice Agent (Weeks 3-4)
**Deliverable**: 24/7 automated phone answering and scheduling

**Tasks**:
1. Set up Twilio/Telnyx phone number
2. Create FastAPI service with Claude integration
3. Implement voice call handling:
   - Speech-to-text pipeline
   - Claude decision making
   - Text-to-speech responses
4. Create API bridge between voice agent and Next.js
5. Call logging and analytics
6. SMS confirmations

**Tech Decisions**:
- Reuse your voice-clone-app Python infrastructure
- Use Anthropic SDK for Claude
- WebSocket updates for real-time confirmation

### Phase 3: Google Maps & SEO (Week 5)
**Deliverable**: Local search dominance and integrated booking

**Tasks**:
1. Google Business Profile optimization:
   - Complete all fields
   - Add service areas (with map)
   - Enable messaging
   - Upload team photos
2. Google Maps embed in Astro site
3. "Book Now" button in Google Business
4. Local SEO content:
   - City-specific landing pages
   - Service area blog posts
   - Schema markup (LocalBusiness, PlumberService)
5. Google My Business API integration for review imports

### Phase 4: Polish & Analytics (Week 6)
**Deliverable**: Production-ready with insights

**Tasks**:
1. Performance optimization:
   - Astro static generation
   - Next.js caching strategies
   - Database query optimization
2. Admin analytics dashboard:
   - Appointment trends
   - Call metrics
   - No-show analysis
   - Revenue tracking
3. Customer communication:
   - Appointment reminders (SMS + email)
   - Review requests post-appointment
   - Newsletter signup
4. Deployment:
   - Vercel for Next.js app
   - Netlify/Cloudflare Pages for Astro site
   - Railway/Render for FastAPI service
   - Supabase hosting

---

## 🔧 Technical Implementation Details

### Booking Engine (Calendar Conflict Detection)

```typescript
// Core logic for finding available slots
type TimeSlot = { start: Date; end: Date; available: boolean };

async function getAvailableSlots(
  date: Date,
  serviceDuration: number,
  plumberId: string
): Promise<TimeSlot[]> {
  // 1. Get plumber's working hours for that day
  const availability = await supabase
    .from('availability')
    .select('*')
    .eq('day_of_week', date.getDay())
    .eq('plumber_id', plumberId);

  // 2. Get existing appointments
  const appointments = await supabase
    .from('appointments')
    .select('*')
    .eq('status', 'confirmed')
    .gte('scheduled_time', date)
    .lt('scheduled_time', addDays(date, 1));

  // 3. Generate 30-min slots and mark occupied ones
  const slots = generateSlots(availability, serviceDuration);
  return slots.map(slot => ({
    ...slot,
    available: !isConflicting(slot, appointments)
  }));
}

// Voice agent uses this:
// "We have availability at 2 PM or 4:30 PM tomorrow"
```

### Real-Time Calendar Updates (WebSocket)

```typescript
// Admin dashboard sees updates immediately when voice agent books
useEffect(() => {
  const subscription = supabase
    .from('appointments')
    .on('*', (payload) => {
      setAppointments(prev => [...prev, payload.new]);
      // Trigger notification sound/popup
    })
    .subscribe();

  return () => supabase.removeSubscription(subscription);
}, []);
```

### Voice Agent Decision Tree

```python
# FastAPI endpoint receives call, sends to Claude
@app.post("/api/phone/call")
async def handle_call(call: PhoneCall):
    messages = [
        {"role": "user", "content": f"Call from {call.transcription}"}
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=PLUMBER_SYSTEM_PROMPT,
        messages=messages,
        tools=[
            {
                "name": "check_availability",
                "description": "Check plumber's availability",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "service_type": {"type": "string"},
                        "preferred_date": {"type": "string"},
                    }
                }
            },
            {
                "name": "create_appointment",
                "description": "Book the appointment",
                "input_schema": {...}
            }
        ]
    )

    # Claude decides what tool to use based on conversation
    return await execute_tool_decision(response)
```

---

## 💰 Cost Breakdown (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| **Supabase** | ~1K appointments/month | $25-50 |
| **Claude API** | 1000 calls × 3K tokens avg | $150-250 |
| **Twilio** | 1000 incoming minutes | $100-200 |
| **Text-to-Speech** | ElevenLabs (voice agent) | $50-100 |
| **Speech-to-Text** | Deepgram | $50-100 |
| **Vercel** | Next.js hosting | $20 |
| **Netlify** | Astro hosting | $0-20 |
| **Render/Railway** | FastAPI service | $30-50 |
| **Domain + SSL** | Google Domains | $12 |
| **Google Business API** | Reviews, listing data | $0 (free tier) |
| **SMS (optional)** | Twilio SMS | $0.0075/SMS (~$50) |
| **Total** | | **$487-752/month** |

**Note**: This scales well. After plumber's first $5K month, software costs are ~10% of revenue.

---

## 🚀 Deployment Checklist

- [ ] Supabase project created and migrations applied
- [ ] Environment variables configured (Anthropic, Twilio, etc.)
- [ ] Astro site deployed to Netlify/Cloudflare Pages
- [ ] Next.js app deployed to Vercel
- [ ] FastAPI service deployed to Railway/Render
- [ ] Twilio phone number configured
- [ ] Google Business Profile claimed and optimized
- [ ] DNS records pointing to right services
- [ ] SSL certificates installed
- [ ] Monitoring/alerting set up (Sentry for errors)
- [ ] Backup strategy for Supabase
- [ ] Load testing for voice agent
- [ ] Google Analytics and Search Console connected

---

## 🏢 CRITICAL: Multi-Client Architecture & Operations

**Important**: You mentioned "what if I get another client" - this changes everything about how we design the system. Building for a single plumber vs. a multi-plumber platform are fundamentally different architectures. Below is the **production-ready multi-client approach** using proven patterns from your ElShaddai apps.

### A. Multi-Tenancy Model

Your system should support multiple independent plumber shops from day one. Here's how:

#### Organization Structure (From Consensus App Pattern)

Each plumber/shop = **Organization** with:
- Unique database tenant context
- Independent customers, appointments, billing
- Role-based access (owner, plumber, customer)
- Isolated data via Row-Level Security (RLS)

```sql
-- Core multi-tenant table
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,              -- "Joe's Plumbing"
  owner_id UUID NOT NULL REFERENCES auth.users(id),
  business_type VARCHAR(50),               -- "plumbing" (for later expansion)
  address TEXT,
  phone_number VARCHAR(20),
  service_areas TEXT[], -- ["Downtown", "Suburbs", "West Side"]
  logo_url TEXT,
  website_url TEXT,
  billing_plan VARCHAR(50),                -- "free", "starter", "pro", "enterprise"
  max_plumbers INTEGER DEFAULT 1,          -- Limits per tier
  max_monthly_bookings INTEGER DEFAULT 1000,
  features JSONB,                          -- {"ai_voice": true, "sms": true}
  stripe_customer_id VARCHAR(255),         -- For payments
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- User-Organization relationship (many-to-many)
CREATE TABLE user_organization_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  role VARCHAR(50) NOT NULL,               -- "owner", "plumber", "admin"
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(user_id, organization_id)
);

-- Invitations for adding team members
CREATE TABLE organization_invitations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  email VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,               -- "plumber", "admin"
  token VARCHAR(255) UNIQUE NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',    -- "pending", "accepted", "expired"
  expires_at TIMESTAMPTZ DEFAULT now() + INTERVAL '7 days',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Appointments are now scoped to organization
CREATE TABLE appointments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  customer_id UUID REFERENCES customers(id),
  plumber_id UUID REFERENCES auth.users(id),
  service_id UUID REFERENCES services(id),
  scheduled_time TIMESTAMPTZ NOT NULL,
  duration_minutes INTEGER NOT NULL,
  status VARCHAR(50) DEFAULT 'pending',    -- "pending", "confirmed", "completed", "cancelled"
  notes TEXT,
  phone_number VARCHAR(20) NOT NULL,       -- Customer contact
  email VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Customers (scoped per organization)
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  name VARCHAR(255) NOT NULL,
  phone_number VARCHAR(20) NOT NULL,
  email VARCHAR(255),
  address TEXT,
  notes TEXT,
  repeat_customer BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(organization_id, phone_number)   -- Phone unique per org
);
```

### B. Row-Level Security (RLS) Enforcement

Database enforces tenant isolation at the SQL level (can't accidentally expose data):

```sql
-- Users can only see their organization's data
CREATE POLICY "Users can only view their organization's appointments" ON appointments
  FOR SELECT USING (
    organization_id IN (
      SELECT organization_id FROM user_organization_roles
      WHERE user_id = auth.uid()
    )
  );

CREATE POLICY "Users can only create in their organization" ON appointments
  FOR INSERT WITH CHECK (
    organization_id IN (
      SELECT organization_id FROM user_organization_roles
      WHERE user_id = auth.uid()
    )
  );

-- Customers can only view their own appointments
CREATE POLICY "Customers can view own appointments" ON appointments
  FOR SELECT USING (
    email = auth.jwt() ->> 'email'  -- Customer auth via email
    OR phone_number = current_setting('request.headers')::jsonb ->> 'x-customer-phone'
  );
```

### C. Authentication for Different User Types

Your system needs **multiple auth flows**:

#### 1. **Plumber Shop Owner/Admin Auth** (NextAuth.js)

```typescript
// /app/api/auth/[...nextauth]/route.ts
import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";
import CredentialsProvider from "next-auth/providers/credentials";

export const authConfig = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
    CredentialsProvider({
      name: "Email/Password",
      async authorize(credentials) {
        // Verify plumber credentials against auth.users
        const user = await verifyPlumberCredentials(
          credentials.email,
          credentials.password
        );
        return user; // { id, email, name }
      },
    }),
  ],
  callbacks: {
    async session({ session, token }) {
      // Add organization context to session
      session.user.organizationId = token.organizationId;
      session.user.role = token.role;
      return session;
    },
    async jwt({ token, user }) {
      if (user) {
        // Fetch user's organization on login
        const org = await getFirstOrganization(user.id);
        token.organizationId = org?.id;
        token.role = org?.role;
      }
      return token;
    },
  },
  session: {
    strategy: "jwt",
    maxAge: 30 * 24 * 60 * 60, // 30 days
    updateAge: 24 * 60 * 60,   // Refresh every 24h
  },
};
```

#### 2. **Customer Auth** (Phone + Email Verification)

```typescript
// /app/api/auth/customer/route.ts
export async function POST(request: Request) {
  const { phone, email } = await request.json();

  // 1. Send OTP via SMS
  const otp = generateOTP();
  await sendSMS(phone, `Your verification code: ${otp}`);

  // 2. Store OTP (valid for 10 minutes)
  await redis.set(`otp:${phone}`, otp, "EX", 600);

  return Response.json({
    message: "OTP sent",
    requiresVerification: true
  });
}

// /app/api/auth/customer/verify-otp/route.ts
export async function POST(request: Request) {
  const { phone, otp } = await request.json();

  const storedOtp = await redis.get(`otp:${phone}`);
  if (storedOtp !== otp) throw new Error("Invalid OTP");

  // 3. Create JWT token valid for 7 days
  const token = jwt.sign(
    { phone, email, type: "customer" },
    process.env.JWT_SECRET,
    { expiresIn: "7 days" }
  );

  return Response.json({ token });
}
```

**This allows customers to:**
- Book appointments without creating an account
- Access their booking with just a phone # or email
- Receive SMS updates without managing passwords

### D. API Authorization with Multi-Tenant Wrapper

Reuse Genesis `withFamilyAuth` pattern, adapted for organizations:

```typescript
// /lib/api/withOrgAuth.ts
export function withOrgAuth(
  source: 'query' | 'body' | 'params' = 'query',
  handler: (
    request: Request,
    context: {
      organizationId: string;
      userId: string;
      role: 'owner' | 'plumber' | 'admin';
      supabase: SupabaseClient;
    }
  ) => Promise<Response>
) {
  return async (request: Request, { params }) => {
    // 1. Get user from session
    const session = await auth();
    if (!session?.user?.id) {
      return createErrorResponse('UNAUTHORIZED', 'Not authenticated', 401);
    }

    // 2. Extract organizationId based on source
    let organizationId = '';
    if (source === 'query') {
      organizationId = new URL(request.url).searchParams.get('org_id') || '';
    } else if (source === 'body') {
      const body = await request.json();
      organizationId = body.organization_id;
    }

    // 3. Verify user belongs to this organization
    const userRole = await getUserOrganizationRole(
      session.user.id,
      organizationId
    );
    if (!userRole) {
      return createErrorResponse('FORBIDDEN', 'Not member of organization', 403);
    }

    // 4. Create tenant-scoped Supabase client
    const supabase = createTenantClient(organizationId);

    // 5. Call handler with context
    return handler(request, {
      organizationId,
      userId: session.user.id,
      role: userRole,
      supabase,
    });
  };
}

// Usage in API route:
export const POST = withOrgAuth('body', async (request, { organizationId, userId, supabase }) => {
  const body = await request.json();

  // organizationId is verified, safe to use
  const { error, data } = await supabase
    .from('appointments')
    .insert({
      organization_id: organizationId,
      ...body
    });

  return createSuccessResponse(data);
});
```

### E. Customer Login & Dashboard

Customers get a simple "My Appointment" page:

```typescript
// /app/customer/appointments/page.tsx
export default async function CustomerAppointments() {
  // Customer auth: phone + OTP token in URL
  const token = searchParams.get('token');
  const decoded = jwt.verify(token, process.env.JWT_SECRET);

  // Query their appointments by phone
  const appointments = await supabase
    .from('appointments')
    .select('*')
    .eq('phone_number', decoded.phone)
    .order('scheduled_time', { ascending: true });

  return (
    <div>
      {appointments.map(appt => (
        <div key={appt.id}>
          <h3>{appt.scheduled_time}</h3>
          <p>Status: {appt.status}</p>
          <button onClick={() => handleReschedule(appt.id)}>
            Reschedule
          </button>
          <button onClick={() => handleCancel(appt.id)}>
            Cancel
          </button>
        </div>
      ))}
    </div>
  );
}
```

### F. Billing & Feature Management

```typescript
// /lib/billing/plans.ts
export const BILLING_PLANS = {
  free: {
    price: 0,
    maxPlumbers: 1,
    maxMonthlyBookings: 50,
    features: {
      ai_voice: false,      // No AI answering
      sms_reminders: false,
      google_calendar_sync: false,
      team_management: false,
      analytics: false,
    },
  },
  starter: {
    price: 29,
    maxPlumbers: 2,
    maxMonthlyBookings: 200,
    features: {
      ai_voice: true,       // AI voice answering
      sms_reminders: true,
      google_calendar_sync: true,
      team_management: false,
      analytics: false,
    },
  },
  professional: {
    price: 79,
    maxPlumbers: 5,
    maxMonthlyBookings: 1000,
    features: {
      ai_voice: true,
      sms_reminders: true,
      google_calendar_sync: true,
      team_management: true,    // Add team members
      analytics: true,          // Advanced reporting
    },
  },
};

// Check if feature enabled in middleware
export function hasFeature(org: Organization, feature: string): boolean {
  const plan = BILLING_PLANS[org.billing_plan];
  return plan.features[feature] === true;
}

// Usage:
if (hasFeature(org, 'ai_voice')) {
  // Show AI voice configuration UI
}
```

### G. Admin Dashboard Navigation

Each shop owner sees only their data:

```typescript
// /app/dashboard/layout.tsx
export default async function DashboardLayout({ children }) {
  const session = await auth();
  const org = await getOrganization(session.user.organizationId);

  return (
    <div>
      <Sidebar>
        <NavItem href="/dashboard" icon={Home}>Dashboard</NavItem>
        <NavItem href="/dashboard/appointments" icon={Calendar}>
          Appointments
        </NavItem>
        <NavItem href="/dashboard/customers" icon={Users}>
          Customers
        </NavItem>
        <NavItem href="/dashboard/team" icon={Users}>
          Team ({org.plumbers.length}/{BILLING_PLANS[org.billing_plan].maxPlumbers})
        </NavItem>
        <NavItem href="/dashboard/settings" icon={Settings}>
          Settings
        </NavItem>

        {hasFeature(org, 'analytics') && (
          <NavItem href="/dashboard/analytics" icon={BarChart3}>
            Analytics
          </NavItem>
        )}
      </Sidebar>

      <Content>{children}</Content>
    </div>
  );
}
```

### H. Team Management for Multi-Plumber Shops

```typescript
// /app/api/organizations/[orgId]/members/route.ts
export const POST = withOrgAuth(async (request, { organizationId, role, supabase }) => {
  // Only owners can add team members
  if (role !== 'owner') {
    throw new ForbiddenError('Only owners can add team members');
  }

  const { email, newRole } = await request.json();

  // 1. Create invitation token
  const token = generateSecureToken();
  await supabase.from('organization_invitations').insert({
    organization_id: organizationId,
    email,
    role: newRole,
    token,
  });

  // 2. Send invitation email
  await sendEmail(email, {
    subject: 'You are invited to join our plumbing team',
    body: `Click here to accept: ${process.env.APP_URL}/join?token=${token}`,
  });

  return createSuccessResponse({ invited: true });
});

// Accept invitation flow
export const POST = async (request: Request) => {
  const { token, password } = await request.json();

  // 1. Look up invitation
  const invitation = await supabase
    .from('organization_invitations')
    .select('*')
    .eq('token', token)
    .single();

  if (!invitation) throw new Error('Invalid invitation');
  if (new Date() > new Date(invitation.expires_at)) {
    throw new Error('Invitation expired');
  }

  // 2. Create user account
  const { user } = await auth.createUser({
    email: invitation.email,
    password, // Plumber chooses their password
  });

  // 3. Assign to organization
  await supabase.from('user_organization_roles').insert({
    user_id: user.id,
    organization_id: invitation.organization_id,
    role: invitation.role,
  });

  // 4. Mark invitation accepted
  await supabase
    .from('organization_invitations')
    .update({ status: 'accepted' })
    .eq('id', invitation.id);

  return createSuccessResponse({ joined: true });
};
```

### I. Single vs. Multi-Client Decision Matrix

| Scenario | Recommended Approach | Setup Time |
|----------|-------------------|-----------|
| **Single plumber client forever** | Simplified: skip multi-tenancy, single Org in DB | 1 week |
| **Might get more clients later** | Build multi-tenant from day 1 (recommended) | 2 weeks |
| **Want SaaS product** | Full multi-tenant + marketplace | 4+ weeks |

**My recommendation**: Build the multi-tenant version from day one. It only takes 1-2 extra weeks but gives you unlimited scalability. Once one plumber succeeds, you can sell to others.

### J. Project Structure with Multi-Client Support

```
plumber-booking/
├── packages/
│   ├── booking-types/
│   │   ├── organizations.ts     # From Consensus pattern
│   │   ├── auth.ts             # Multi-user auth types
│   │   ├── appointments.ts
│   │   ├── billing.ts
│   │   └── customers.ts
│   ├── booking-api/
│   │   ├── withOrgAuth.ts       # Multi-tenant middleware
│   │   ├── OrganizationService.ts
│   │   ├── AuthService.ts
│   │   └── BillingService.ts
│   └── booking-ui/
│       ├── AppointmentForm.tsx
│       ├── CustomerDashboard.tsx
│       └── AdminDashboard.tsx
│
├── apps/
│   ├── web/                     # Astro marketing (shared)
│   ├── plumber-app/             # Next.js admin app
│   │   ├── src/app/dashboard/
│   │   ├── src/app/api/organizations/
│   │   ├── src/app/api/appointments/
│   │   └── src/lib/auth/ (copy from Genesis)
│   ├── customer-app/            # React customer portal (optional)
│   │   ├── src/pages/appointments/
│   │   └── src/components/
│   └── voice-service/           # Python FastAPI
│       ├── app/routes/
│       └── app/services/
│
└── database/
    ├── migrations/
    │   ├── 001_organizations.sql
    │   ├── 002_user_roles.sql
    │   ├── 003_appointments.sql
    │   ├── 004_invitations.sql
    │   └── 005_billing.sql
    └── seeds/
```

### K. Copied Code from ElShaddai Apps

Ready-to-adapt files:

| File | Source | Destination | Changes |
|------|--------|-------------|---------|
| `auth.ts` | Genesis | plumber-app/src/ | Add org context |
| `withFamilyAuth.ts` | Genesis | packages/booking-api/withOrgAuth.ts | Rename & org params |
| `organizations.sql` | Consensus | database/migrations/ | Adapt fields |
| `rbac.ts` | Genesis | packages/booking-api/ | Add plumber roles |
| `error-handler.ts` | Genesis | packages/booking-api/ | Use as-is |
| `UserContext.tsx` | Runtheworld | customer-app/src/contexts/ | Adapt for customers |

---

## 🎯 Success Metrics (First 90 Days)

| Metric | Target | How to Measure |
|--------|--------|---|
| **Google Local Pack** | Top 5 in local area | Google Search Console |
| **Appointment Bookings** | 50+ per month | Supabase queries |
| **Phone Answer Rate** | >90% of calls answered | Call logs analytics |
| **Booking Completion** | >80% calls → booked | Compare calls vs appointments |
| **Website Traffic** | 500+ visitors/month | Google Analytics |
| **Page Load Speed** | <2 seconds | Google PageSpeed |
| **Mobile Conversion** | >5% of visitors | Conversion tracking |
| **Customer Retention** | >40% repeat | CRM database |

---

## 🔐 Security & Compliance

### Data Protection
- Row-Level Security on all Supabase tables
- PCI compliance for payment info (if adding later)
- GDPR-compliant data retention (90 days for call logs)
- Encrypted customer phone numbers in database

### Voice Security
- Twilio call encryption (TLS)
- API key rotation for Anthropic
- Rate limiting on booking API
- CAPTCHA on public form to prevent abuse

### Monitoring
- Sentry for error tracking
- CloudWatch for infrastructure
- Call quality monitoring (dropped calls)
- Daily backup verification

---

## 🛠️ Tools & Libraries (Reusable from ElShaddai)

| Component | From | Reusable |
|-----------|------|----------|
| **Astro Components** | Portfolio Builder | ✅ Service cards, pricing tables, testimonials |
| **Next.js Setup** | Genesis | ✅ Auth patterns, Supabase integration, API routes |
| **Database Schema** | Reseller Central | ✅ Customer/order structure, call logs like order tracking |
| **Voice Agent** | voice-clone-app | ✅ Python FastAPI structure, speech pipeline |
| **WebSocket Updates** | OPTIMUS | ✅ Real-time dashboard updates pattern |
| **Admin UI** | Optimus | ✅ Dashboard layout, data tables, charts |

---

## 🎓 Next Steps

1. **Review this plan** - Does it align with your vision?
2. **Decide on phone provider** - Twilio vs Telnyx vs Vonage?
3. **Decide on voice output** - ElevenLabs vs Google Cloud?
4. **Set up local dev environment** for Supabase
5. **Create Astro project** in ElShaddai monorepo
6. **Build Phase 1** - Get booking website working before voice

---

## 📚 Industry References

- [The Google Maps Playbook for Plumbing (2025)](https://www.plumberseo.net/the-google-maps-playbook-how-plumbing-hvac-companies-can-dominate-local-search-in-2025/)
- [ServiceTitan Google Business Profile Guide](https://www.servicetitan.com/blog/plumbing-google-business-profile)
- [Convin AI - Plumbing Scheduling](https://convin.ai/blog/appointment-bookings-plumbers-services)
- [Eden AI Plumber Solution](https://ringeden.com/blog/best-ai-receptionist-for-plumbers)
- [Best Plumbing Dispatch Software 2025](https://nextbillion.ai/blog/best-plumbing-dispatch-software)

---

**Questions?** Let's discuss:
- Phone provider preference
- Feature prioritization
- Timeline and resource constraints
- Integration with existing plumber's tools (QuickBooks, etc.)
