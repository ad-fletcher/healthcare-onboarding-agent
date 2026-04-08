# Healthcare Onboarding Agent

A voice-based AI health interview agent built with [LiveKit Agents](https://docs.livekit.io/agents/), OpenAI GPT-4.1, and Convex. The agent conducts structured, multi-phase health profile interviews via real-time voice conversation.

## What It Does

When a user joins a LiveKit room, the agent (Dr. Jordan) greets them and routes them to the appropriate interview phase based on their existing progress. It collects responses, validates inputs, logs everything to a Convex database, and generates data visualizations comparing answers to aggregate population distributions.

**4 interview phases:**

| Phase | Focus | Fields |
|-------|-------|--------|
| 1 | Demographics & background | Age, life stage, living arrangement, location, education, career, financial stability, social connection, health confidence, life satisfaction |
| 2 | Risk tolerance | 8 risk-related fields |
| 3 | Vitality & perspective | 10 vitality/outlook fields |
| 4 | Medical profile | 8 medical history fields |

## Architecture

```
main.py
├── ConsentCollector        # Greets user, fetches phase progress, routes to correct phase
├── helpers/
│   ├── phase1.py           # Phase 1 agent (demographics)
│   ├── phase2.py           # Phase 2 agent (risk tolerance)
│   ├── phase3.py           # Phase 3 agent (vitality)
│   ├── phase4.py           # Phase 4 agent (medical profile)
│   ├── convex_utils.py     # Convex API helpers (read/write user data, visualizations)
│   ├── prompts.py          # System prompt strings per phase
│   ├── data.py             # Aggregate population data for comparisons
│   ├── shared_types.py     # MySessionInfo dataclass
│   └── assistantLong.py    # (unused legacy)
```

**Flow:**

1. Participant joins LiveKit room with `clerk_id` and `interviewId` in metadata
2. `ConsentCollector` fetches user metadata from Convex via Clerk ID
3. Checks phase progress and routes to the earliest incomplete phase
4. Phase agent collects fields one at a time via voice, validates, and writes each to Convex
5. On completion, renders a visualization and ends the room

## Tech Stack

| Concern | Library |
|---------|---------|
| Real-time voice | LiveKit Agents 1.0.13 |
| LLM | OpenAI GPT-4.1 |
| Speech-to-text | Deepgram nova-3 (multilingual) |
| Text-to-speech | Cartesia |
| Voice activity detection | Silero VAD |
| Noise cancellation | LiveKit BVC |
| Backend / database | Convex |
| Auth | Clerk |
| Deployment | Fly.io |

## Setup

### Prerequisites

- Python 3.11+
- A [LiveKit](https://livekit.io) project (cloud or self-hosted)
- [Convex](https://convex.dev) project with user and interview tables
- [Clerk](https://clerk.com) for user authentication
- OpenAI, Deepgram, and Cartesia API keys

### Install

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env.local` file:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
CARTESIA_API_KEY=your_cartesia_key
CONVEX_URL=https://your-project.convex.cloud
```

### Run Locally

```bash
python main.py dev
```

The agent connects to LiveKit as a worker and waits for participants to join. A health check server starts on port `8082`.

## Deployment (Fly.io)

Requires [Fly CLI](https://fly.io/docs/hands-on/install-flyctl/) and a Fly.io account.

**First deploy:**

```bash
fly launch
fly secrets set LIVEKIT_URL=... LIVEKIT_API_KEY=... LIVEKIT_API_SECRET=... OPENAI_API_KEY=... DEEPGRAM_API_KEY=... CARTESIA_API_KEY=... CONVEX_URL=...
fly deploy
```

**Subsequent deploys:**

```bash
fly deploy
```

The `fly.toml` is already configured with a health check on `/healthz` at port 8082.

## How Participants Join

Participants must join the LiveKit room with the following metadata (JSON-encoded):

```json
{
  "clerk_id": "user_xxxx",
  "interviewId": "interview_xxxx"
}
```

These are used to look up the user's existing progress and associate responses with the correct interview record in Convex.
