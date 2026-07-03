"""Flask server for the AI Coach application."""

from flask import Flask, jsonify, request, send_from_directory

from coach import COACH_PERSONAS, CoachError, get_coach

app = Flask(__name__, static_folder="static", static_url_path="/static")
coach = get_coach()

MAX_MESSAGES = 100
MAX_MESSAGE_CHARS = 4000


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/personas")
def personas():
    return jsonify(
        {
            "mode": coach.mode,
            "personas": [
                {
                    "key": key,
                    "name": p["name"],
                    "emoji": p["emoji"],
                    "tagline": p["tagline"],
                }
                for key, p in COACH_PERSONAS.items()
            ],
        }
    )


@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    persona_key = body.get("persona")
    if persona_key not in COACH_PERSONAS:
        return jsonify({"error": f"Unknown persona: {persona_key!r}"}), 400

    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        return jsonify({"error": "'messages' must be a non-empty list."}), 400
    if len(messages) > MAX_MESSAGES:
        return jsonify({"error": "Conversation too long — start a new session."}), 400
    for m in messages:
        if (
            not isinstance(m, dict)
            or m.get("role") not in ("user", "assistant")
            or not isinstance(m.get("content"), str)
            or not m["content"].strip()
        ):
            return (
                jsonify(
                    {
                        "error": "Each message needs a 'role' of user/assistant "
                        "and non-empty string 'content'."
                    }
                ),
                400,
            )
        if len(m["content"]) > MAX_MESSAGE_CHARS:
            return jsonify({"error": "Message too long."}), 400
    if messages[-1]["role"] != "user":
        return jsonify({"error": "The last message must be from the user."}), 400

    try:
        reply = coach.reply(persona_key, messages)
    except CoachError as e:
        return jsonify({"error": str(e)}), 502

    return jsonify({"reply": reply, "mode": coach.mode})


if __name__ == "__main__":
    print(f"AI Coach running in {coach.mode!r} mode on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000)
