// Screen 1 — Profile form (chips + sliders)

document.addEventListener("DOMContentLoaded", () => {
  // Chip groups: single-select
  setupChips("chips-country");
  setupChips("chips-field");
  setupChips("chips-degree");

  // Sliders
  setupSlider("slider-gpa", "val-gpa", v => parseFloat(v).toFixed(1));
  setupSlider("slider-ielts", "val-ielts", v => parseFloat(v).toFixed(1));
  setupSlider("slider-budget", "val-budget", v => parseInt(v).toLocaleString("ru") + " €");

  document.getElementById("btn-find").addEventListener("click", onFindPrograms);
});

function setupChips(groupId) {
  const group = document.getElementById(groupId);
  if (!group) return;
  group.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      group.querySelectorAll(".chip").forEach(c => c.classList.remove("selected"));
      chip.classList.add("selected");
    });
  });
}

function setupSlider(sliderId, valId, formatter) {
  const slider = document.getElementById(sliderId);
  const valEl = document.getElementById(valId);
  if (!slider || !valEl) return;
  valEl.textContent = formatter(slider.value);
  slider.addEventListener("input", () => {
    valEl.textContent = formatter(slider.value);
  });
}

function getChipValue(groupId) {
  const selected = document.querySelector(`#${groupId} .chip.selected`);
  return selected ? selected.dataset.value : null;
}

async function onFindPrograms() {
  const country = getChipValue("chips-country");
  const field = getChipValue("chips-field");
  const degree = getChipValue("chips-degree");
  const gpa = parseFloat(document.getElementById("slider-gpa").value);
  const ielts = parseFloat(document.getElementById("slider-ielts").value);
  const budget = parseInt(document.getElementById("slider-budget").value);

  if (!field || !degree) {
    tg.showAlert("Выбери направление и тип программы");
    return;
  }

  const btn = document.getElementById("btn-find");
  btn.disabled = true;
  btn.textContent = "Поиск...";

  try {
    const resp = await fetch(`${API}/match/`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ gpa, ielts, budget, field, degree_type: degree, country }),
    });

    if (!resp.ok) throw new Error("API error");
    const results = await resp.json();
    state.results = results;

    renderResults(results);
    navigate("results");
  } catch (e) {
    tg.showAlert("Ошибка при поиске программ. Попробуй снова.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Найти программы";
  }
}
