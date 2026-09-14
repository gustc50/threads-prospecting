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

async function loadThreadsConfig() {
  const res = await fetch("/api/threads-config");
  const data = await res.json();

  document.getElementById("threads_user_id").value = data.user_id;

  const status = document.getElementById("threads-status");
  status.textContent = data.token_set
    ? "Token do Threads configurado."
    : "Token do Threads ainda não configurado — preencha abaixo.";
  status.className = "status " + (data.token_set ? "ok" : "warn");
}

document.getElementById("threads-config-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = document.getElementById("threads-config-message");
  setMessage(message, "Salvando...");

  const body = {
    user_id: document.getElementById("threads_user_id").value,
    token: document.getElementById("threads_token").value,
  };

  const res = await fetch("/api/threads-config", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));

  if (res.ok) {
    setMessage(message, "Credenciais salvas.", "ok");
    document.getElementById("threads_token").value = "";
    loadThreadsConfig();
  } else {
    setMessage(message, data.error || "Erro ao salvar.", "error");
  }
});

function renderLead(lead) {
  const card = document.createElement("div");
  card.className = "lead-card";

  const author = document.createElement("p");
  author.className = "lead-author";
  author.textContent = `@${lead.post.username || "desconhecido"} · ${lead.post.permalink || ""}`;
  card.appendChild(author);

  const text = document.createElement("p");
  text.className = "lead-text";
  text.textContent = lead.post.text || "";
  card.appendChild(text);

  if (lead.skip) {
    const badge = document.createElement("span");
    badge.className = "badge skip";
    badge.textContent = "SKIP — não é um lead relevante";
    card.appendChild(badge);
    return card;
  }

  const replyBox = document.createElement("textarea");
  replyBox.rows = 3;
  replyBox.value = lead.reply;
  card.appendChild(replyBox);

  const actions = document.createElement("div");
  actions.className = "lead-actions";

  if (lead.published_id) {
    const badge = document.createElement("span");
    badge.className = "badge published";
    badge.textContent = "Publicado automaticamente";
    actions.appendChild(badge);
  } else {
    const publishBtn = document.createElement("button");
    publishBtn.type = "button";
    publishBtn.textContent = "Publicar resposta";
    publishBtn.addEventListener("click", async () => {
      publishBtn.disabled = true;
      publishBtn.textContent = "Publicando...";

      const res = await fetch("/api/prospect/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ post_id: lead.post.id, text: replyBox.value }),
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        const badge = document.createElement("span");
        badge.className = "badge published";
        badge.textContent = "Publicado";
        publishBtn.replaceWith(badge);
      } else {
        publishBtn.disabled = false;
        publishBtn.textContent = "Publicar resposta";
        alert(data.error || "Erro ao publicar.");
      }
    });
    actions.appendChild(publishBtn);
  }

  card.appendChild(actions);
  return card;
}

document.getElementById("prospect-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = document.getElementById("prospect-message");
  const list = document.getElementById("leads-list");
  const autoPublish = document.getElementById("auto_publish").checked;
  setMessage(message, autoPublish ? "Buscando e publicando..." : "Buscando leads...");
  list.innerHTML = "";

  const keywords = document
    .getElementById("keywords")
    .value.split(",")
    .map((k) => k.trim())
    .filter(Boolean);

  const res = await fetch("/api/prospect/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ keywords, auto_publish: autoPublish }),
  });
  const data = await res.json().catch(() => ({}));

  if (res.ok) {
    if (data.leads.length === 0) {
      setMessage(message, "Nenhum post encontrado para essas palavras-chave.");
    } else {
      setMessage(message, `${data.leads.length} post(s) encontrado(s).`, "ok");
      data.leads.forEach((lead) => list.appendChild(renderLead(lead)));
    }
  } else {
    setMessage(message, data.error || "Erro ao buscar leads.", "error");
  }
});

loadConfig();
loadThreadsConfig();
