const BASE_URL = "http://127.0.0.1:8000";

const chatBox = document.getElementById("chatBox");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const sendBtn = document.getElementById("sendBtn");
const uploadBtn = document.getElementById("uploadBtn");
const appStatus = document.getElementById("appStatus");

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "";
});

uploadBtn.addEventListener("click", uploadFile);
sendBtn.addEventListener("click", askQuery);

document.getElementById("queryInput").addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    askQuery();
  }
});

function addMessage(text, type) {
  const msg = document.createElement("div");
  msg.className = `message ${type}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.innerText = type === "user" ? "🧑" : "🤖";

  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${type}`;
  bubble.innerText = text;

  if (type === "user") {
    msg.appendChild(bubble);
    msg.appendChild(avatar);
  } else {
    msg.appendChild(avatar);
    msg.appendChild(bubble);
  }

  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function showLoader() {
  const loader = document.createElement("div");
  loader.className = "loader";
  loader.id = "loader";
  loader.innerText = "🤖 Thinking...";
  chatBox.appendChild(loader);
}

function removeLoader() {
  const loader = document.getElementById("loader");
  if (loader) loader.remove();
}

async function parseResponse(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || data.message || `Request failed (${response.status})`);
  }
  return data;
}

async function refreshBackendStatus() {
  try {
    const response = await fetch(`${BASE_URL}/health`);
    const data = await parseResponse(response);
    appStatus.textContent = data.index_available
      ? "Backend ready · document index found"
      : "Backend ready · upload a PDF to begin";
  } catch {
    appStatus.textContent = "Backend unavailable · start the API on port 8000";
  }
}

async function uploadFile() {
  const file = fileInput.files[0];
  if (!file) {
    appStatus.textContent = "Choose a PDF first.";
    return;
  }
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    appStatus.textContent = "Only PDF files are supported.";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  uploadBtn.disabled = true;
  appStatus.textContent = "Uploading and indexing PDF…";

  try {
    const res = await fetch(`${BASE_URL}/upload`, {
      method: "POST",
      body: formData
    });
    const data = await parseResponse(res);
    showFileCard(data.file_name, data.num_chunks);
    appStatus.textContent = `Indexed ${data.file_name} · ${data.num_chunks} text chunks`;
    fileInput.value = "";
    fileName.textContent = "";
  } catch (err) {
    appStatus.textContent = `Upload failed: ${err.message}`;
  } finally {
    uploadBtn.disabled = false;
  }
}

function showFileCard(name, chunkCount) {
  const card = document.createElement("div");
  card.className = "file-card";

  const filename = document.createElement("strong");
  filename.textContent = `📄 ${name}`;
  const detail = document.createElement("span");
  detail.textContent = `Ready for querying · ${chunkCount} chunks`;
  card.append(filename, document.createElement("br"), detail);

  chatBox.appendChild(card);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function askQuery() {
  const input = document.getElementById("queryInput");
  const query = input.value.trim();
  const promptType = document.getElementById("promptType").value;

  if (!query) return;

  addMessage(query, "user");
  input.value = "";
  input.focus();

  showLoader();
  sendBtn.disabled = true;

  try {
    const res = await fetch(`${BASE_URL}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        q: query,
        prompt_type: promptType
      })
    });

    const data = await parseResponse(res);
    removeLoader();
    renderResponse(data);

  } catch (err) {
    removeLoader();
    addMessage(`❌ ${err.message}`, "bot");
  } finally {
    sendBtn.disabled = false;
  }
}

function renderResponse(data) {
  const msg = document.createElement("div");
  msg.className = "message bot";

  const content = document.createElement("div");
  content.className = "chat-bubble bot";

  const meta = document.createElement("div");
  meta.className = "meta";
  const latency = document.createElement("span");
  latency.textContent = `⚡ ${Number(data.latency).toFixed(2)}s`;
  const sources = document.createElement("span");
  sources.textContent = `📄 Sources: ${(data.sources || []).join(", ") || "unknown"}`;
  const chunks = document.createElement("span");
  chunks.textContent = `🔎 ${data.retrieved_chunks || 0} chunks · ${data.model || "Ollama"}`;
  meta.append(latency, sources, chunks);

  msg.appendChild(content);
  msg.appendChild(meta);
  chatBox.appendChild(msg);

  chatBox.scrollTop = chatBox.scrollHeight;

  typeEffect(content, data.answer || "No answer was returned.");
}

function typeEffect(element, answer) {
  if (!window.marked || !window.DOMPurify) {
    element.textContent = answer;
    return;
  }
  const safeHtml = DOMPurify.sanitize(marked.parse(answer));
  element.innerHTML = safeHtml;
}

refreshBackendStatus();

const toggleBtn = document.getElementById("themeToggle");

if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark");
  toggleBtn.textContent = "☀️";
}

toggleBtn.addEventListener("click", () => {
  document.body.classList.toggle("dark");

  const isDark = document.body.classList.contains("dark");

  toggleBtn.textContent = isDark ? "☀️" : "🌙";

  localStorage.setItem("theme", isDark ? "dark" : "light");
});