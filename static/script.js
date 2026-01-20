// Generate a random thread ID on load if empty
document.addEventListener("DOMContentLoaded", () => {
    if (!document.getElementById('threadId').value) {
        document.getElementById('threadId').value = "thread_" + Math.floor(Math.random() * 10000);
    }
});

function handleEnter(event) {
    if (event.key === "Enter") sendMessage();
}

function resetSession() {
    document.getElementById('threadId').value = "thread_" + Math.floor(Math.random() * 10000);
    document.getElementById('chatHistory').innerHTML = `
        <div class="message assistant">
            <div class="bubble">Session reset. New Thread ID generated.</div>
        </div>`;
}

async function sendMessage() {
    const input = document.getElementById('userMessage');
    const message = input.value.trim();
    if (!message) return;

    const senderEmail = document.getElementById('senderEmail').value;
    const threadId = document.getElementById('threadId').value;

    // 1. Add User Message to UI
    appendMessage(message, 'user');
    input.value = '';

    // 2. Show loading indicator
    const loadingId = appendMessage("Thinking...", 'assistant', true);

    try {
        // 3. Call FastAPI Backend
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sender: senderEmail,
                thread_id: threadId,
                message: message
            })
        });

        const data = await response.json();

        // 4. Update UI with AI Response
        removeMessage(loadingId);
        appendMessage(data.response, 'assistant');

    } catch (error) {
        removeMessage(loadingId);
        appendMessage("Error: Could not reach the agent.", 'assistant');
        console.error(error);
    }
}

function appendMessage(text, role, isLoading = false) {
    const history = document.getElementById('chatHistory');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;

    // Assign ID if loading
    const msgId = isLoading ? "loading-" + Date.now() : "";
    if (msgId) msgDiv.id = msgId;

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.innerText = text; // Safe text insertion
    if (isLoading) bubble.style.fontStyle = "italic";

    msgDiv.appendChild(bubble);
    history.appendChild(msgDiv);
    history.scrollTop = history.scrollHeight;

    return msgId;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}