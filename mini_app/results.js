// Screen 2 — Results list with scoring

function renderResults(results) {
  const list = document.getElementById("results-list");
  const sub = document.getElementById("results-sub");
  const actions = document.getElementById("results-actions");

  state.selectMode = false;
  state.selectedIds.clear();

  if (!results || results.length === 0) {
    list.innerHTML = `<div class="empty"><div class="empty-icon">🔍</div>Программы не найдены.<br>Попробуй изменить параметры.</div>`;
    actions.style.display = "none";
    sub.textContent = "Ничего не найдено";
    return;
  }

  sub.textContent = `Найдено ${results.length} программ`;
  actions.style.display = "block";

  list.innerHTML = results.map((p, i) => {
    const isTop = i < 5;
    const color = p.score >= 75 ? "var(--green)" : p.score >= 50 ? "var(--yellow)" : "var(--red)";
    const deadline = p.deadline ? formatDate(p.deadline) : "Уточни на сайте";
    const tuition = p.tuition_year ? `${p.tuition_year.toLocaleString("ru")} €/год` : "Бесплатно / уточни";

    return `
      <div class="program-card ${isTop ? "top" : ""}" id="card-${p.program_id}" onclick="onCardClick(${p.program_id})">
        ${isTop ? `<div class="badge">Топ-${i+1}</div>` : ""}
        <div class="card-select" id="check-${p.program_id}" style="display:none">
          <input type="checkbox" onclick="event.stopPropagation(); toggleSelect(${p.program_id})" id="cb-${p.program_id}">
        </div>
        <h3>${p.program_name}</h3>
        <div class="meta">${p.university_name} · ${p.country}</div>
        <div class="details">
          <span>💰 ${tuition}</span>
          <span>🎓 IELTS ${p.min_ielts}+</span>
          <span>📅 ${deadline}</span>
        </div>
        ${p.url ? `<a href="${p.url}" target="_blank" onclick="event.stopPropagation()" style="display:inline-block;margin-top:8px;font-size:12px;color:var(--accent);text-decoration:none;padding:4px 10px;border:1px solid var(--accent);border-radius:20px;">🔗 Сайт программы</a>` : ""}
        <div class="progress-bar">
          <div class="progress-fill" style="width:${p.score}%; background:${color}"></div>
        </div>
        <div style="font-size:12px;color:var(--hint);margin-top:4px">${p.score}% совпадения</div>
      </div>
    `;
  }).join("");

  // Button handlers
  document.getElementById("btn-add-top5").onclick = () => addToDeadlines(
    results.slice(0, 5).map(p => p.program_id)
  );

  document.getElementById("btn-add-manual").onclick = () => {
    state.selectMode = !state.selectMode;
    const btn = document.getElementById("btn-add-manual");

    if (state.selectMode) {
      btn.textContent = "Добавить выбранные";
      btn.classList.remove("secondary");
      document.querySelectorAll(".card-select").forEach(el => el.style.display = "block");
    } else {
      const ids = [...state.selectedIds];
      if (ids.length > 0) addToDeadlines(ids);
      else {
        btn.textContent = "Выбрать вручную";
        btn.classList.add("secondary");
        document.querySelectorAll(".card-select").forEach(el => el.style.display = "none");
      }
    }
  };
}

function onCardClick(programId) {
  if (state.selectMode) {
    toggleSelect(programId);
    return;
  }
  openChecklist(programId);
}

function toggleSelect(programId) {
  const cb = document.getElementById(`cb-${programId}`);
  if (state.selectedIds.has(programId)) {
    state.selectedIds.delete(programId);
    if (cb) cb.checked = false;
  } else {
    state.selectedIds.add(programId);
    if (cb) cb.checked = true;
  }
}

async function addToDeadlines(programIds) {
  if (!programIds.length) return;
  try {
    const resp = await fetch(`${API}/deadlines/`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ program_ids: programIds }),
    });
    if (!resp.ok) throw new Error();
    tg.showAlert(`✅ Добавлено ${programIds.length} программ в дедлайны!`);
    navigate("apps");
  } catch {
    tg.showAlert("Ошибка при сохранении. Попробуй снова.");
  }
}

function formatDate(dateStr) {
  const d = new Date(dateStr);
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}
