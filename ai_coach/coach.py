"""Coach engine: personas, Claude-backed coach, and a rule-based mock fallback."""

import os
import random

COACH_PERSONAS = {
    "fitness": {
        "name": "Coach Max",
        "emoji": "💪",
        "tagline": "Fitness & health — workouts, nutrition, habits",
        "system": (
            "You are Coach Max, an experienced, upbeat fitness and health coach. "
            "You help people build sustainable exercise and nutrition habits. "
            "Coaching style: start by understanding the person's current fitness level, "
            "constraints (time, equipment, injuries), and goals before prescribing anything. "
            "Give concrete, actionable steps — specific exercises, sets, reps, and simple meal "
            "guidelines — rather than generic advice. Set small, measurable weekly goals and "
            "check in on them. Be encouraging but honest: call out unrealistic expectations. "
            "You are not a doctor; recommend professional medical advice for pain, injuries, "
            "or health conditions. Keep replies conversational and reasonably short — this is "
            "a chat, not an essay. Ask at most one or two questions per reply."
        ),
    },
    "career": {
        "name": "Coach Dana",
        "emoji": "🚀",
        "tagline": "Career growth — interviews, skills, direction",
        "system": (
            "You are Coach Dana, a sharp and supportive career coach. "
            "You help with career direction, job searches, interview preparation, resume "
            "feedback, negotiation, and skill development. "
            "Coaching style: clarify the person's situation and goal first (role, industry, "
            "experience level, timeline). Give direct, practical advice with concrete next "
            "steps — e.g. exact resume bullet rewrites, sample interview answers using the "
            "STAR method, or a 30-day learning plan. Be honest about trade-offs and market "
            "realities rather than just cheerleading. Keep replies conversational and focused; "
            "ask at most one or two questions per reply."
        ),
    },
    "productivity": {
        "name": "Coach Sam",
        "emoji": "⚡",
        "tagline": "Productivity — focus, planning, accountability",
        "system": (
            "You are Coach Sam, a pragmatic productivity and accountability coach. "
            "You help people plan their days, beat procrastination, and follow through on "
            "goals. Coaching style: break big goals into small, scheduled next actions. "
            "Recommend simple systems (time-blocking, the two-minute rule, weekly reviews) "
            "only when they fit the person's actual problem — diagnose before prescribing. "
            "Hold the person accountable: ask what they committed to last time and whether "
            "they did it, without guilt-tripping. Prefer one small change over a full system "
            "overhaul. Keep replies short and actionable; ask at most one or two questions "
            "per reply."
        ),
    },
    "mindfulness": {
        "name": "Coach Ren",
        "emoji": "🌿",
        "tagline": "Mindfulness — stress, balance, well-being",
        "system": (
            "You are Coach Ren, a calm and grounded mindfulness and well-being coach. "
            "You help people manage stress, build mindfulness habits, and find better "
            "work-life balance. Coaching style: listen first and reflect back what you hear "
            "before offering techniques. Suggest small, concrete practices — a two-minute "
            "breathing exercise, a short walk, a wind-down routine — matched to the person's "
            "situation. Avoid clinical claims: you are a coach, not a therapist, and you "
            "encourage professional help for anxiety, depression, or crisis situations. "
            "Keep replies warm, brief, and free of jargon; ask at most one or two questions "
            "per reply."
        ),
    },
}


class CoachError(Exception):
    """Raised when a coach backend cannot produce a reply."""


class ClaudeCoach:
    """Coach backed by the Claude API via the official anthropic SDK."""

    mode = "claude"

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic()
        return self._client

    def reply(self, persona_key, messages):
        import anthropic

        persona = COACH_PERSONAS[persona_key]
        try:
            response = self.client.messages.create(
                model="claude-opus-4-8",
                max_tokens=16000,
                thinking={"type": "adaptive"},
                system=persona["system"],
                messages=messages,
            )
        except anthropic.AuthenticationError:
            raise CoachError(
                "The configured ANTHROPIC_API_KEY was rejected. "
                "Check the key and restart the server."
            )
        except anthropic.RateLimitError:
            raise CoachError(
                "The Claude API is rate-limiting requests right now. "
                "Please wait a moment and try again."
            )
        except anthropic.APIConnectionError:
            raise CoachError(
                "Could not reach the Claude API. Check your network connection."
            )
        except anthropic.APIStatusError as e:
            raise CoachError(f"The Claude API returned an error ({e.status_code}).")

        text = next((b.text for b in response.content if b.type == "text"), "")
        if not text:
            raise CoachError("The model returned an empty reply. Please try again.")
        return text


class MockCoach:
    """Keyword-based canned coach so the app works without an API key."""

    mode = "mock"

    _OPENERS = {
        "fitness": (
            "Great to have you here! Before we build a plan, tell me: how many days a "
            "week can you realistically train, and do you have access to a gym or just "
            "bodyweight at home?"
        ),
        "career": (
            "Happy to help with your career! To point you in the right direction: what "
            "role are you in now, and what would you like to be doing in 12 months?"
        ),
        "productivity": (
            "Let's get you unstuck. What's the one task you've been putting off the "
            "longest, and what usually derails you when you try to start it?"
        ),
        "mindfulness": (
            "I'm glad you're taking a moment for yourself. What's been weighing on you "
            "most this week — work, sleep, or something else?"
        ),
    }

    _KEYWORD_REPLIES = [
        (
            ("goal", "plan", "want to", "how do i", "help me"),
            "That's a solid goal. Let's make it concrete: what would success look like "
            "in 4 weeks, in one sentence? Once we have that, we'll break it into one "
            "small action you can take this week.",
        ),
        (
            ("tired", "stress", "overwhelm", "anxious", "burnout"),
            "That sounds heavy — thanks for being honest about it. When things pile up, "
            "shrink the scope: pick the single smallest step that would make today 1% "
            "better. What could that be for you?",
        ),
        (
            ("stuck", "procrastinat", "motivat", "lazy", "can't start"),
            "Motivation follows action, not the other way around. Try the two-minute "
            "rule: commit to just two minutes of the task, permission to stop after. "
            "Which task will you try it on today?",
        ),
        (
            ("did it", "done", "finished", "completed", "progress"),
            "Excellent work — that's real progress, and it counts. What made it work "
            "this time? Let's lock that in and pick the next small step.",
        ),
        (
            ("thank", "thanks"),
            "Any time — that's what I'm here for. Same time next check-in? Remember: "
            "small steps, done consistently, beat big plans done occasionally.",
        ),
    ]

    _FALLBACKS = [
        "Tell me more about that — what's the outcome you're hoping for, and what's "
        "the biggest thing standing in the way?",
        "Got it. If we picked one small, specific action you could finish before "
        "tomorrow, what would it be?",
        "Interesting — and how does that connect to the bigger goal you have in mind? "
        "Let's make sure our next step moves you toward it.",
    ]

    def reply(self, persona_key, messages):
        user_turns = [m for m in messages if m["role"] == "user"]
        last = user_turns[-1]["content"].lower() if user_turns else ""

        if len(user_turns) <= 1:
            return self._OPENERS[persona_key]
        for keywords, response in self._KEYWORD_REPLIES:
            if any(k in last for k in keywords):
                return response
        return random.choice(self._FALLBACKS)


def get_coach():
    """Return the Claude-backed coach when a key is configured, else the mock."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return ClaudeCoach()
    return MockCoach()
