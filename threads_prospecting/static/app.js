const tabButtons = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabButtons.forEach((b) => b.classList.remove("active"));
    tabPanels.forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

function setMessage(el, text, kind) {
  el.textContent = text;
  el.className = "message" + (kind ? ` ${kind}` : "");
}

async function loadConfig() {
  const res = await fetch("/api/config");
  const data = await res.json();

  document.getElementById("nicho").value = data.account.nicho;
  document.getElementById("tom").value = data.account.tom;
  document.getElementById("publico").value = data.account.publico;
  document.getElementById("nome_da_conta").value = data.account.nome_da_conta;

  const status = document.getElementById("config-status");
  status.textContent = data.api_key_set
    ? "Chave da API configurada."
    : "Chave da API ainda não configurada — preencha abaixo.";
  status.className = "status " + (data.api_key_set ? "ok" : "warn");
}

document.getElementById("config-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = document.getElementById("config-message");
  setMessage(message, "Salvando...");

  const body = {
    account: {
      nicho: document.getElementById("nicho").value,
      tom: document.getElementById("tom").value,
      publico: document.getElementById("publico").value,
      nome_da_conta: document.getElementById("nome_da_conta").value,
    },
    api_key: document.getElementById("api_key").value,
  };

  const res = await fetch("/api/config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));

  if (res.ok) {
    setMessage(message, "Configurações salvas.", "ok");
    document.getElementById("api_key").value = "";
    loadConfig();
  } else {
    setMessage(message, data.error || "Erro ao salvar.", "error");
  }
});

document.getElementById("post-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = document.getElementById("post-message");
  const result = document.getElementById("post-result");
  setMessage(message, "Gerando post...");
  result.value = "";

  const res = await fetch("/api/post", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic: document.getElementById("topic").value }),
  });
  const data = await res.json().catch(() => ({}));

  if (res.ok) {
    setMessage(message, "");
    result.value = data.post;
  } else {
    setMessage(message, data.error || "Erro ao gerar post.", "error");
  }
});

document.getElementById("post-copy").addEventListener("click", () => {
  const result = document.getElementById("post-result");
  if (result.value) navigator.clipboard.writeText(result.value);
});

document.getElementById("reply-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = document.getElementById("reply-message");
  const result = document.getElementById("reply-result");
  setMessage(message, "Gerando resposta...");
  result.value = "";

  const res = await fetch("/api/reply", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ comment: document.getElementById("comment").value }),
  });
  const data = await res.json().catch(() => ({}));

  if (res.ok) {
    if (data.skip) {
      setMessage(message, "Comentário marcado para pular (SKIP) — melhor não responder.", "warn");
    } else {
      setMessage(message, "");
      result.value = data.reply;
    }
  } else {
    setMessage(message, data.error || "Erro ao gerar resposta.", "error");
  }
});

document.getElementById("reply-copy").addEventListener("click", () => {
  const result = document.getElementById("reply-result");
  if (result.value) navigator.clipboard.writeText(result.value);
});

loadConfig();
