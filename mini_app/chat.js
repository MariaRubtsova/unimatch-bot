// Screen 4 — AI Chat

function initChat() {
  const messagesEl = document.getElementById("chat-messages");
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");

  // Welcome message + quick replies
  appendBotMessage(
    `Привет, ${state.firstName || ""}! 👋 Я помогу с вопросами о поступлении.\n\nСпроси меня что угодно:`,
    [
      "Подобрать программы",
      "Требования IELTS",
      "Стоимость обучения",
    ]
  );

  sendBtn.addEventListener("click", sendMessage);
  input.addEventListener("keydown", e => { if (e.key === "Enter") sendMessage(); });
}

async function sendMessage() {
  const input = document.getElementById("chat-input");
  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  appendUserMessage(text);

  // Typing indicator
  const typingId = appendBotMessage("...", null, true);

  try {
    const resp = await fetch(`${API}/chat/`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ message: text }),
    });
    if (!resp.ok) throw new Error();
    const data = await resp.json();
    updateMessage(typingId, data.reply);
  } catch {
    updateMessage(typingId, "Ошибка. Попробуй снова.");
  }
}

function appendUserMessage(text) {
  const el = document.createElement("div");
  el.className = "chat-msg user";
  el.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
  document.getElementById("chat-messages").appendChild(el);
  scrollChat();
}

function appendBotMessage(text, quickReplies = null, isTyping = false) {
  const id = "msg-" + Date.now();
  const el = document.createElement("div");
  el.className = "chat-msg bot";
  el.id = id;

  let html = `<div class="bubble">${isTyping ? "⏳" : escapeHtml(text).replace(/\n/g, "<br>")}</div>`;

  if (quickReplies) {
    html += `<div class="quick-replies">` +
      quickReplies.map(r => `<button class="quick-reply" onclick="onQuickReply('${r}')">${r}</button>`).join("") +
      `</div>`;
  }

  el.innerHTML = html;
  document.getElementById("chat-messages").appendChild(el);
  scrollChat();
  return id;
}

function updateMessage(id, text) {
  const el = document.getElementById(id);
  if (!el) return;
  el.querySelector(".bubble").innerHTML = escapeHtml(text).replace(/\n/g, "<br>");
}

function onQuickReply(text) {
  document.getElementById("chat-input").value = text;
  sendMessage();
}

function scrollChat() {
  const el = document.getElementById("chat-messages");
  el.scrollTop = el.scrollHeight;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
