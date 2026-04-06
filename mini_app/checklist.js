// Screen 3 — Checklist + Screen: My Apps

async function openChecklist(programId) {
  state.currentProgramId = programId;
  navigate("checklist");

  const header = document.getElementById("checklist-header");
  const list = document.getElementById("checklist-list");
  header.innerHTML = `<div class="loading"><div class="spinner"></div>Загрузка...</div>`;
  list.innerHTML = "";

  try {
    const resp = await fetch(`${API}/checklist/${programId}`, { headers: authHeaders() });
    if (!resp.ok) throw new Error();
    const data = await resp.json();
    renderChecklist(data);
  } catch {
    header.innerHTML = `<div class="empty">Ошибка загрузки чеклиста</div>`;
  }
}

function renderChecklist(data) {
  const header = document.getElementById("checklist-header");
  const list = document.getElementById("checklist-list");

  const isUrgent = data.days_left <= 14 && data.days_left >= 0;
  const done = data.items.filter(i => i.is_done).length;
  const total = data.items.length;

  header.innerHTML = `
    <div style="margin-bottom:16px">
      <div class="page-header">${data.program_name}</div>
      <div class="page-sub">${data.university_name}</div>
    </div>
    <div class="deadline-banner ${isUrgent ? "urgent" : ""}">
      ${data.deadline
        ? `📅 Дедлайн: ${formatDate(data.deadline)} (${data.days_left} дн.)`
        : "📅 Дедлайн не указан"}
    </div>
    <div style="font-size:14px;margin-bottom:12px;color:var(--hint)">${done} из ${total} документов готово</div>
    <div class="progress-bar" style="height:8px;margin-bottom:16px">
      <div class="progress-fill" style="width:${total ? Math.round(done/total*100) : 0}%; background:var(--btn)"></div>
    </div>
  `;

  list.innerHTML = data.items.map(item => `
    <div class="checklist-item ${item.is_done ? "done" : ""}" id="ci-${item.id}">
      <input type="checkbox" ${item.is_done ? "checked" : ""}
        onchange="toggleChecklistItem(${item.id}, this.checked)">
      <div class="item-text">
        <div class="item-name">${item.item_name}</div>
        ${item.hint ? `<div class="item-hint">${item.hint}</div>` : ""}
      </div>
    </div>
  `).join("");

  document.getElementById("btn-download-ics").onclick = () => downloadIcs();
}

async function toggleChecklistItem(itemId, isDone) {
  // Optimistic UI update
  const row = document.getElementById(`ci-${itemId}`);
  if (row) row.classList.toggle("done", isDone);

  try {
    await fetch(`${API}/checklist/${itemId}`, {
      method: "PATCH",
      headers: authHeaders(),
      body: JSON.stringify({ is_done: isDone }),
    });
  } catch {
    // revert on failure
    if (row) row.classList.toggle("done", !isDone);
  }
}

async function downloadIcs() {
  try {
    const resp = await fetch(`${API}/export/ics`, { headers: authHeaders() });
    if (!resp.ok) throw new Error();
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "unimatch_deadlines.ics";
    a.click();
    URL.revokeObjectURL(url);
  } catch {
    tg.showAlert("Ошибка при скачивании файла");
  }
}

async function loadApps() {
  const list = document.getElementById("apps-list");
  list.innerHTML = `<div class="loading"><div class="spinner"></div>Загрузка...</div>`;

  try {
    const resp = await fetch(`${API}/deadlines/`, { headers: authHeaders() });
    if (!resp.ok) throw new Error();
    const items = await resp.json();

    if (!items.length) {
      list.innerHTML = `<div class="empty"><div class="empty-icon">📭</div>Нет сохранённых программ.<br>Найди программы через «Подбор».</div>`;
      return;
    }

    list.innerHTML = items.map(item => {
      const color = item.days_left <= 7 ? "var(--red)" : item.days_left <= 30 ? "var(--yellow)" : "var(--green)";
      return `
        <div class="deadline-row" onclick="openChecklist(${item.program_id})">
          <div class="deadline-dot" style="background:${color}"></div>
          <div class="deadline-info">
            <div class="prog">${item.program_name}</div>
            <div class="uni">${item.university_name} · ${item.country}</div>
          </div>
          <div class="deadline-date">
            ${item.deadline ? formatDate(item.deadline) : "—"}<br>
            <span style="color:${color}">${item.days_left} дн.</span>
          </div>
        </div>
      `;
    }).join("");
  } catch {
    list.innerHTML = `<div class="empty">Ошибка загрузки</div>`;
  }
}
