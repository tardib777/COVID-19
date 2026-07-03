# AI Coach

A small web application that gives you a personal AI coach in four flavors —
fitness, career, productivity, and mindfulness. Pick a coach, chat in the
browser, and get goal-oriented, actionable guidance.

Powered by the [Claude API](https://platform.claude.com/) when an API key is
configured, with a built-in rule-based demo mode so the app runs without one.

## Quick start

```bash
cd ai_coach
pip install -r requirements.txt

# Optional — real AI responses via Claude:
export ANTHROPIC_API_KEY=sk-ant-...

python app.py
```

Then open http://127.0.0.1:5000 in your browser.

Without `ANTHROPIC_API_KEY` the app runs in **demo mode** (a "demo" badge is
shown in the UI) using canned coaching responses, which is handy for trying
the interface or developing offline.

## How it works

| File | Role |
|---|---|
| `app.py` | Flask server: serves the frontend, `GET /api/personas`, `POST /api/chat` |
| `coach.py` | Coach personas (system prompts), Claude client, mock fallback |
| `static/` | Vanilla HTML/CSS/JS chat interface |

The conversation history lives in the browser and is sent in full with every
request (the Claude API is stateless). Each persona is a system prompt that
defines the coach's style: understand the person's situation first, set
small measurable goals, give concrete next steps, and check in on progress.

The Claude integration uses model `claude-opus-4-8` with adaptive thinking.

## API

```
GET  /api/personas
     -> {"mode": "claude"|"mock", "personas": [{key, name, emoji, tagline}, ...]}

POST /api/chat
     {"persona": "fitness", "messages": [{"role": "user", "content": "..."}]}
     -> {"reply": "...", "mode": "claude"|"mock"}
```

Validation errors return HTTP 400 with `{"error": "..."}`; upstream API
failures return HTTP 502 with a user-friendly message.
