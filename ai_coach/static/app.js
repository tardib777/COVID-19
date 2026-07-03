const pickerView = document.getElementById("picker-view");
const chatView = document.getElementById("chat-view");
const personaList = document.getElementById("persona-list");
const modeBadge = document.getElementById("mode-badge");
const chatModeBadge = document.getElementById("chat-mode-badge");
const messagesEl = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

let currentPersona = null; // {key, name, emoji, tagline}
let history = [];          // [{role, content}]

async function init() {
  try {
    const res = await fetch("/api/personas");
    const data = await res.json();
    if (data.mode === "mock") modeBadge.hidden = false;
    for (const p of data.personas) {
      const card = document.createElement("button");
      card.className = "persona-card";
      card.innerHTML = `
        <span class="emoji"></span>
        <span><strong></strong><small></small></span>`;
      card.querySelector(".emoji").textContent = p.emoji;
      card.querySelector("strong").textContent = p.name;
      card.querySelector("small").textContent = p.tagline;
      card.addEventListener("click", () => openChat(p, data.mode));
      personaList.appendChild(card);
    }
  } catch {
    personaList.textContent = "Could not load coaches — is the server running?";
  }
}

function openChat(persona, mode) {
  currentPersona = persona;
  history = [];
  messagesEl.innerHTML = "";
  document.getElementById("chat-emoji").textContent = persona.emoji;
  document.getElementById("chat-name").textContent = persona.name;
  document.getElementById("chat-tagline").textContent = persona.tagline;
  chatModeBadge.hidden = mode !== "mock";
  pickerView.hidden = true;
  chatView.hidden = false;
  addBubble(
    "coach",
    `Hi, I'm ${persona.name} ${persona.emoji} — your ${persona.tagline
      .split("—")[0]
      .trim()
      .toLowerCase()} coach. What would you like to work on?`
  );
  input.focus();
}

document.getElementById("back-btn").addEventListener("click", () => {
  chatView.hidden = true;
  pickerView.hidden = false;
});

function addBubble(kind, text) {
  const div = document.createElement("div");
  div.className = `msg ${kind}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text || sendBtn.disabled) return;

  input.value = "";
  addBubble("user", text);
  history.push({ role: "user", content: text });

  sendBtn.disabled = true;
  const typing = addBubble("coach typing", `${currentPersona.name} is thinking…`);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ persona: currentPersona.key, messages: history }),
    });
    const data = await res.json();
    typing.remove();
    if (!res.ok) {
      addBubble("error", data.error || `Request failed (${res.status})`);
      history.pop(); // let the user retry the same turn
    } else {
      addBubble("coach", data.reply);
      history.push({ role: "assistant", content: data.reply });
    }
  } catch {
    typing.remove();
    addBubble("error", "Network error — could not reach the coach.");
    history.pop();
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
});

init();
