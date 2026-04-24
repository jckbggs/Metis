document.addEventListener("DOMContentLoaded", async function () {
  const chatWrapper = document.querySelector(".chat-wrapper");
  const chatBox = document.getElementById("chatBox");
  const userInput = document.getElementById("userInput");
  const sendBtn = document.getElementById("sendBtn");
  const remainingBox = document.getElementById("remainingBox");
  const chatTitle = document.getElementById("chatTitle");
  const chatSubtitle = document.getElementById("chatSubtitle");
  const initialBotMessage = document.getElementById("initialBotMessage");

  if (!chatWrapper || !chatBox || !userInput || !sendBtn) return;

  const endpoint = chatWrapper.dataset.chatEndpoint || "/chat/website-info";

  function addMessage(text, sender) {
    const div = document.createElement("div");
    div.className = `chat-message ${sender}`;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
  }

  function addThinkingMessage() {
    const div = document.createElement("div");
    div.className = "chat message bot thinking";
    div.textContent = "Thinking...";
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
  }

  try {
    const meResponse = await fetch("/api/me", { credentials: "same-origin" });
    const meData = await meResponse.json();

    if (meData.logged_in) {
      chatTitle.textContent = "Website Information";
      chatSubtitle.textContent = "Ask about the Metis website and available support.";
      initialBotMessage.textContent =
        `Hi ${meData.username}. I can explain what the website does and what each page is for.`;
      if (remainingBox) {
        remainingBox.style.display = "none";
      }
    } else {
      chatTitle.textContent = "Guest Chat";
      chatSubtitle.textContent = "Ask general questions about the website and support options.";
      initialBotMessage.textContent =
        "Hi. I’m the Metis guest chatbot. I can explain what the website does and what each page is for.";
      if (remainingBox) {
        remainingBox.textContent = "Guest messages remaining: 15";
        remainingBox.style.display = "block";
      }
    }
  } catch (error) {
    console.error("Failed to load user info:", error);
  }

  async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    addMessage(message, "user");
    userInput.value = "";
    sendBtn.disabled = true;
    userInput.disabled = true;

    const thinkingBubble = addThinkingMessage();

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ message })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      thinkingBubble.remove();
      addMessage(data.reply, "bot");

      if (!data.logged_in && remainingBox && typeof data.remaining === "number") {
        remainingBox.textContent = `Guest messages remaining: ${data.remaining}`;
      }

      if (!data.logged_in && data.remaining === 0) {
        userInput.disabled = true;
        sendBtn.disabled = true;
      }
    } catch (error) {
      console.error("Website info chat error:", error);
      thinkingBubble.remove();
      addMessage("Sorry, something went wrong.", "bot");
      userInput.disabled = false;
      sendBtn.disabled = false;
    } finally {
      if (!userInput.disabled) {
        sendBtn.disabled = false;
        userInput.disabled = false;
        userInput.focus();
      }
    }
  }

  sendBtn.addEventListener("click", sendMessage);

  userInput.addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
      sendMessage();
    }
  });
});