"use strict";

const THEME_KEY = "lotto_theme";
const CART_KEY = "lotto_cart";
const TODAY_KEY = "lotto_today_pick";
const TAB_KEY = "lotto_tab";

const CATEGORIES = [
  { id: "independent", name: "독립 50:50 방식", shortName: "독립 50:50", tag: "표준", color: "var(--accent)",
    desc: "변동 슬롯 2개가 각각 독립적으로 고/저확률 중 선택" },
  { id: "fixed", name: "고정 1:1 방식", shortName: "고정 1:1", tag: "표준", color: "var(--accent)",
    desc: "변동 슬롯을 고확률 1개 + 저확률 1개로 고정" },
  { id: "all_high", name: "고확률만", shortName: "고확률만", tag: "고빈도", color: "var(--high)",
    desc: "6개 전부 출현빈도 상위 15개 풀에서 선택" },
  { id: "all_low", name: "저확률만", shortName: "저확률만", tag: "저빈도", color: "var(--low)",
    desc: "6개 전부 출현빈도 하위 15개 풀에서 선택" },
  { id: "biased", name: "편향 가정", shortName: "편향 가정", tag: "실험적", color: "var(--warn)",
    desc: "최근 100회차에 가중치를 줘서 혹시 있을지 모를 편향을 잡아보는 실험 모드" },
  { id: "unpopular", name: "비인기 조합", shortName: "비인기 조합", tag: "분할회피", color: "var(--neutral)",
    desc: "당첨 확률은 동일. 남들이 덜 고르는 조합이라 당첨 시 상금 분할 인원이 줄 수 있음" },
];
const RANDOM_LABEL = "무작위 선택";

function categoryById(id) {
  return CATEGORIES.find(c => c.id === id) || CATEGORIES[0];
}

/* ---------- 유틸 ---------- */
const $ = id => document.getElementById(id);

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

function storageGet(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}
function storageSet(key, value) {
  try { localStorage.setItem(key, value); } catch { /* 저장 불가 환경에서는 무시 */ }
}

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let message = `요청 실패 (${res.status})`;
    try {
      const body = await res.json();
      if (body && typeof body.detail === "string") message = body.detail;
    } catch { /* JSON이 아니면 기본 메시지 */ }
    throw new Error(message);
  }
  return res.json();
}

function sortNums(numbers) {
  return [...numbers].sort((a, b) => a - b);
}

function fmtInt(n) {
  return n.toLocaleString("ko-KR");
}

function fmtWon(n) {
  if (n >= 1e8) return `${(n / 1e8).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}억원`;
  if (n >= 1e4) return `${(n / 1e4).toLocaleString("ko-KR", { maximumFractionDigits: 1 })}만원`;
  return `${fmtInt(n)}원`;
}

function fmtAmount(n) {
  if (n >= 1e4) return `${fmtInt(n / 1e4)}만개`;
  return `${fmtInt(n)}개`;
}

/* 번호 공 색은 십의 자리로 구분: 1~9, 10~19, 20~29, 30~39, 40~45 */
function ballColorClass(n) {
  return "d" + (Math.floor(n / 10) + 1);
}

function ball(n, cls) {
  return el("span", "ball " + cls, n);
}

async function copyText(text, btn, doneLabel, idleLabel) {
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = doneLabel;
    setTimeout(() => { btn.textContent = idleLabel; }, 1500);
  } catch (err) {
    alert("복사 실패: " + err.message);
  }
}

/* ---------- 테마 ---------- */
const themeToggleBtn = $("theme-toggle");
function applyTheme(theme, persist) {
  document.documentElement.setAttribute("data-theme", theme);
  if (persist) storageSet(THEME_KEY, theme);
  themeToggleBtn.textContent = theme === "light" ? "다크 모드" : "라이트 모드";
}
applyTheme(document.documentElement.getAttribute("data-theme") || "dark", false);
themeToggleBtn.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  applyTheme(current === "dark" ? "light" : "dark", true);
});

/* ---------- 탭 ---------- */
const tabButtons = [...document.querySelectorAll(".tab")];
const tabLoaders = {};

function showTab(name) {
  tabButtons.forEach(btn => btn.setAttribute("aria-selected", String(btn.dataset.tab === name)));
  document.querySelectorAll(".panel").forEach(panel => {
    panel.hidden = panel.id !== "panel-" + name;
  });
  storageSet(TAB_KEY, name);
  const activeTab = tabButtons.find(btn => btn.dataset.tab === name);
  if (activeTab) activeTab.scrollIntoView({ block: "nearest", inline: "nearest" });
  if (location.hash !== "#" + name) history.replaceState(null, "", "#" + name);
  if (tabLoaders[name]) tabLoaders[name]();
}
tabButtons.forEach(btn => btn.addEventListener("click", () => showTab(btn.dataset.tab)));
window.addEventListener("hashchange", () => {
  const name = location.hash.slice(1);
  if (tabButtons.some(b => b.dataset.tab === name)) showTab(name);
});

/* ---------- 툴팁 ---------- */
const tooltip = $("tooltip");
function showTooltip(target, title, sub) {
  tooltip.replaceChildren(el("strong", null, title), document.createTextNode(sub));
  tooltip.hidden = false;
  const rect = target.getBoundingClientRect();
  const tipRect = tooltip.getBoundingClientRect();
  let left = rect.left + rect.width / 2 - tipRect.width / 2;
  left = Math.max(8, Math.min(left, window.innerWidth - tipRect.width - 8));
  let top = rect.top - tipRect.height - 8;
  if (top < 8) top = rect.bottom + 8;
  tooltip.style.left = left + "px";
  tooltip.style.top = top + "px";
}
function hideTooltip() {
  tooltip.hidden = true;
}
function attachTooltip(node, title, sub) {
  node.addEventListener("pointerenter", () => showTooltip(node, title, sub));
  node.addEventListener("pointerleave", hideTooltip);
  node.addEventListener("focus", () => showTooltip(node, title, sub));
  node.addEventListener("blur", hideTooltip);
}
window.addEventListener("scroll", hideTooltip, { passive: true });

/* ---------- 장바구니 (조합 단위로 저장) ---------- */
function loadJson(key, fallback) {
  try {
    return JSON.parse(storageGet(key) || "null") ?? fallback;
  } catch {
    return fallback;
  }
}
function loadCart() {
  // 이전 버전은 장바구니를 낱개 번호 배열로 저장했다. 조합 단위 배열이 아닌
  // 옛 형식이 남아있으면 크래시를 막기 위해 비운다.
  const parsed = loadJson(CART_KEY, []);
  if (!Array.isArray(parsed) || !parsed.every(item => Array.isArray(item))) return [];
  return parsed;
}
function loadTodayPick() {
  const parsed = loadJson(TODAY_KEY, null);
  return Array.isArray(parsed) ? parsed : null;
}

let cart = loadCart();
let todayPick = loadTodayPick();
const cartBadge = $("cart-badge");

function comboKey(numbers) {
  return sortNums(numbers).join(",");
}
function findCartIndex(numbers) {
  const key = comboKey(numbers);
  return cart.findIndex(c => comboKey(c) === key);
}
function persistCart() {
  storageSet(CART_KEY, JSON.stringify(cart));
  cartBadge.textContent = cart.length;
  document.querySelectorAll(".cart-btn[data-numbers]").forEach(updateCartBtn);
}
function persistTodayPick() {
  storageSet(TODAY_KEY, JSON.stringify(todayPick));
}
function updateCartBtn(btn) {
  const inCart = findCartIndex(btn.dataset.numbers.split(",").map(Number)) !== -1;
  btn.textContent = inCart ? "담김" : "담기";
  btn.classList.toggle("active", inCart);
}
function toggleCombo(numbers) {
  const idx = findCartIndex(numbers);
  if (idx === -1) {
    cart.push(sortNums(numbers));
  } else {
    cart.splice(idx, 1);
    if (todayPick && comboKey(todayPick) === comboKey(numbers)) {
      todayPick = null;
      persistTodayPick();
    }
  }
  persistCart();
}
cartBadge.textContent = cart.length;

function buildCartCard(numbers) {
  const isToday = todayPick && comboKey(todayPick) === comboKey(numbers);
  const card = el("div", "card result-card");
  card.style.setProperty("--cat", "var(--neutral)");

  const headerRow = el("div", "card-header-row");
  headerRow.appendChild(el("div", "combo-title", isToday ? "오늘의 번호" : "담은 조합"));
  const actions = el("div", "card-actions");

  const todayBtn = el("button", "small-btn" + (isToday ? " active" : ""), isToday ? "선택 해제" : "오늘의 번호로");
  todayBtn.type = "button";
  todayBtn.addEventListener("click", () => {
    todayPick = isToday ? null : [...numbers];
    persistTodayPick();
    renderCart();
  });
  const copyBtn = el("button", "small-btn", "복사");
  copyBtn.type = "button";
  copyBtn.addEventListener("click", () => copyText(numbers.join(", "), copyBtn, "복사됨!", "복사"));
  const removeBtn = el("button", "small-btn", "삭제");
  removeBtn.type = "button";
  removeBtn.addEventListener("click", () => {
    toggleCombo(numbers);
    renderCart();
  });
  actions.append(todayBtn, copyBtn, removeBtn);
  headerRow.appendChild(actions);
  card.appendChild(headerRow);

  const balls = el("div", "balls");
  numbers.forEach(n => balls.appendChild(ball(n, ballColorClass(n))));
  card.appendChild(balls);
  return card;
}

function renderCart() {
  const list = $("cart-list");
  list.replaceChildren();
  if (cart.length === 0) {
    list.appendChild(el("p", "empty-msg", "아직 담은 조합이 없습니다. 번호 생성 탭에서 조합을 담아보세요."));
  } else {
    cart.forEach(numbers => list.appendChild(buildCartCard(numbers)));
  }

  const todayEl = $("today-pick");
  todayEl.replaceChildren();
  if (!todayPick) {
    todayEl.appendChild(el("p", "empty-msg", '담은 조합 중 하나를 "오늘의 번호로" 선택해보세요.'));
    return;
  }
  const card = el("div", "card");
  const balls = el("div", "balls");
  todayPick.forEach(n => balls.appendChild(ball(n, ballColorClass(n))));
  const copyBtn = el("button", "small-btn", "오늘의 번호 복사");
  copyBtn.type = "button";
  copyBtn.style.marginTop = "0.8rem";
  copyBtn.addEventListener("click", () => copyText(todayPick.join(", "), copyBtn, "복사됨!", "오늘의 번호 복사"));
  card.append(balls, copyBtn);
  todayEl.appendChild(card);
}
tabLoaders.cart = renderCart;

/* ---------- 번호 생성: 조합 카드 ---------- */
function buildComboCard(combo, titleText, cat, indexTag) {
  const card = el("div", "card result-card");
  card.style.setProperty("--cat", cat.color);

  const headerRow = el("div", "card-header-row");
  headerRow.appendChild(el("div", "combo-title", titleText));
  const actions = el("div", "card-actions");
  const cartBtn = el("button", "small-btn cart-btn");
  cartBtn.type = "button";
  cartBtn.dataset.numbers = combo.numbers.join(",");
  cartBtn.addEventListener("click", () => toggleCombo(combo.numbers));
  updateCartBtn(cartBtn);
  const copyBtn = el("button", "small-btn", "복사");
  copyBtn.type = "button";
  copyBtn.addEventListener("click", () => copyText(combo.numbers.join(", "), copyBtn, "복사됨!", "복사"));
  actions.append(cartBtn, copyBtn);
  headerRow.appendChild(actions);
  card.appendChild(headerRow);

  const tagRow = el("div", "tag-row");
  tagRow.appendChild(el("span", "pill-tag", cat.tag));
  if (indexTag) tagRow.appendChild(el("span", "pill-tag", indexTag));
  const sum = combo.numbers.reduce((a, b) => a + b, 0);
  const odd = combo.numbers.filter(n => n % 2).length;
  tagRow.appendChild(el("span", "pill-tag", `합계 ${sum}`));
  tagRow.appendChild(el("span", "pill-tag", `홀${odd}:짝${6 - odd}`));
  card.appendChild(tagRow);

  const balls = el("div", "balls");
  const table = el("table");
  combo.detail.forEach(item => {
    const pinned = item.source.includes("고정수");
    const node = ball(item.number, ballColorClass(item.number) + (pinned ? " pinned" : ""));
    if (pinned) node.title = "고정수";
    balls.appendChild(node);
    const ratioLabel = item.source.includes("최근") ? "최근 100회 출현비율" : "역대 출현비율";
    const row = el("tr");
    row.append(
      el("td", "num", item.number),
      el("td", null, item.source),
      el("td", null, `${ratioLabel} ${(item.ratio * 100).toFixed(1)}%`),
    );
    table.appendChild(row);
  });
  card.appendChild(balls);

  // 번호별 근거 표와 특징은 기본으로 접어두고 버튼으로 펼친다.
  const details = el("div", "combo-details");
  details.hidden = true;
  details.appendChild(table);
  if (combo.traits) {
    const traitsEl = el("div", "traits", "특징: " + combo.traits.join(", "));
    traitsEl.appendChild(el("div", "disclaimer",
      "이 조합은 당첨 확률을 높이지 않습니다. 모든 조합의 당첨 확률은 동일합니다. " +
      "다만 다른 사람이 이 조합을 고를 가능성이 낮아서, 당첨 시 상금을 나눠 가질 인원이 줄어들 수 있습니다."));
    details.appendChild(traitsEl);
  }
  const toggle = el("button", "details-toggle", "세부정보 보기");
  toggle.type = "button";
  toggle.setAttribute("aria-expanded", "false");
  toggle.addEventListener("click", () => {
    details.hidden = !details.hidden;
    toggle.textContent = details.hidden ? "세부정보 보기" : "세부정보 닫기";
    toggle.setAttribute("aria-expanded", String(!details.hidden));
  });
  card.append(toggle, details);
  return card;
}

const resultsEl = $("results");
// 새로 생성하면 이전 결과는 지우고 이번 결과만 보여준다 (남길 조합은 장바구니에 담는다).
function showResultCards(cards) {
  resultsEl.replaceChildren(...cards);
}

/* ---------- 번호 생성: 세부 조건 ---------- */
const pickerState = new Map(); // number -> "pinned" | "excluded"
const numPicker = $("num-picker");
const oddSelect = $("odd-select");
const sumMinInput = $("sum-min");
const sumMaxInput = $("sum-max");

for (let n = 1; n <= 45; n++) {
  const btn = el("button", null, n);
  btn.type = "button";
  btn.dataset.n = n;
  btn.setAttribute("aria-label", `${n}번`);
  btn.addEventListener("click", () => cyclePicker(n, btn));
  numPicker.appendChild(btn);
}

function pinnedNumbers() {
  return sortNums([...pickerState].filter(([, s]) => s === "pinned").map(([n]) => n));
}
function excludedNumbers() {
  return sortNums([...pickerState].filter(([, s]) => s === "excluded").map(([n]) => n));
}

function cyclePicker(n, btn) {
  const current = pickerState.get(n);
  let next;
  if (!current) next = pinnedNumbers().length >= 5 ? "excluded" : "pinned";
  else if (current === "pinned") next = "excluded";
  else next = null;
  if (next) pickerState.set(n, next);
  else pickerState.delete(n);
  if (next) btn.dataset.state = next;
  else delete btn.dataset.state;
  const label = next === "pinned" ? "고정" : next === "excluded" ? "제외" : "선택 안 함";
  btn.setAttribute("aria-label", `${n}번 ${label}`);
  updateOptionsSummary();
}

$("picker-reset").addEventListener("click", () => {
  pickerState.clear();
  numPicker.querySelectorAll("button").forEach(btn => {
    delete btn.dataset.state;
    btn.setAttribute("aria-label", `${btn.dataset.n}번`);
  });
  updateOptionsSummary();
});

function readConstraints() {
  const params = new URLSearchParams();
  const include = pinnedNumbers();
  const exclude = excludedNumbers();
  if (include.length) params.set("include", include.join(","));
  if (exclude.length) params.set("exclude", exclude.join(","));
  if (oddSelect.value !== "") params.set("odd", oddSelect.value);
  if (sumMinInput.value !== "") params.set("sum_min", sumMinInput.value);
  if (sumMaxInput.value !== "") params.set("sum_max", sumMaxInput.value);
  return params;
}

function updateOptionsSummary() {
  const parts = [];
  const include = pinnedNumbers();
  const exclude = excludedNumbers();
  if (include.length) parts.push(`고정 ${include.join(", ")}`);
  if (exclude.length) parts.push(`제외 ${exclude.length}개`);
  if (oddSelect.value !== "") parts.push(oddSelect.selectedOptions[0].textContent.replace(/\s/g, ""));
  if (sumMinInput.value !== "" || sumMaxInput.value !== "") {
    parts.push(`합계 ${sumMinInput.value || 21}~${sumMaxInput.value || 255}`);
  }
  $("options-summary").textContent = parts.length ? parts.join(" · ") : "없음";
}
[oddSelect, sumMinInput, sumMaxInput].forEach(input => input.addEventListener("input", updateOptionsSummary));

/* ---------- 번호 생성: 요청 ---------- */
const chipRow = $("chip-row");
const ruleRowsEl = $("rule-rows");
const addRowBtn = $("add-row");
const MAX_RULE_ROWS = 5;
const COUNT_OPTIONS = [1, 3, 5, 10];
const ctaBtn = $("cta-btn");
const genError = $("gen-error");
let busy = false;

async function withBusy(fn) {
  if (busy) return;
  busy = true;
  genError.textContent = "";
  chipRow.querySelectorAll(".chip").forEach(node => { node.disabled = true; });
  ctaBtn.disabled = true;
  try {
    await fn();
  } catch (err) {
    genError.textContent = err.message;
  } finally {
    busy = false;
    chipRow.querySelectorAll(".chip").forEach(node => { node.disabled = false; });
    ctaBtn.disabled = false;
  }
}

async function fetchCategoryCards(cat, count, params) {
  const query = new URLSearchParams(params);
  query.set("rule", cat.id);
  query.set("count", count);
  const data = await api("/api/generate?" + query);
  return data.combinations.map((combo, idx) =>
    buildComboCard(combo, cat.name, cat, count > 1 ? `조합 ${idx + 1}` : null));
}

/* requests: [{ cat, count }] — 모든 줄을 생성한 뒤 한 번에 보여준다. 하나라도 실패하면 이전 결과를 유지한다. */
function generateCategories(requests, params) {
  return withBusy(async () => {
    const groups = await Promise.all(requests.map(({ cat, count }) => fetchCategoryCards(cat, count, params)));
    showResultCards(groups.flat());
  });
}

function generateWeekly() {
  return withBusy(async () => {
    const data = await api("/api/weekly");
    showResultCards(data.picks.map(combo => buildComboCard(combo, combo.label, categoryById(combo.slot_rule), null)));
  });
}

const heroChip = el("button", "chip hero", "이번주 추천 전체 생성");
heroChip.type = "button";
heroChip.addEventListener("click", generateWeekly);
chipRow.appendChild(heroChip);

const infoList = $("info-list");
CATEGORIES.forEach(cat => {
  const chip = el("button", "chip", cat.shortName);
  chip.type = "button";
  chip.style.setProperty("--c", cat.color);
  chip.addEventListener("click", () => generateCategories([{ cat, count: 1 }]));
  chipRow.appendChild(chip);

  const info = el("div", "info-item");
  const dot = el("span", "dot");
  dot.style.background = cat.color;
  info.append(dot, el("strong", null, cat.name), el("span", "pill-tag", cat.tag), el("p", null, cat.desc));
  infoList.appendChild(info);
});

/* ---------- 직접 설정: 카테고리 줄 (최대 5줄) ---------- */
function ruleRows() {
  return [...ruleRowsEl.querySelectorAll(".rule-row")];
}

function refreshRuleRows() {
  const rows = ruleRows();
  rows.forEach((row, idx) => {
    row.querySelector(".remove-row-btn").disabled = rows.length === 1;
    row.querySelector(".cat-select").setAttribute("aria-label", `카테고리 ${idx + 1}`);
    row.querySelector(".count-select").setAttribute("aria-label", `카테고리 ${idx + 1} 생성 개수`);
  });
  addRowBtn.hidden = rows.length >= MAX_RULE_ROWS;
  $("row-count").textContent = `(${rows.length}/${MAX_RULE_ROWS})`;
}

function addRuleRow() {
  if (ruleRows().length >= MAX_RULE_ROWS) return;
  // 새 줄은 아직 고르지 않은 카테고리로 시작한다.
  const used = new Set(ruleRows().map(row => row.querySelector(".cat-select").value));
  const next = CATEGORIES.find(c => !used.has(c.id)) || CATEGORIES[0];

  const row = el("div", "rule-row");
  const catSel = el("select", "cat-select");
  CATEGORIES.forEach(cat => {
    const opt = el("option", null, cat.name);
    opt.value = cat.id;
    catSel.appendChild(opt);
  });
  catSel.value = next.id;
  const countSel = el("select", "count-select");
  COUNT_OPTIONS.forEach(n => {
    const opt = el("option", null, `${n}개`);
    opt.value = n;
    countSel.appendChild(opt);
  });
  countSel.value = "5";
  const removeBtn = el("button", "remove-row-btn", "×");
  removeBtn.type = "button";
  removeBtn.setAttribute("aria-label", "이 카테고리 빼기");
  removeBtn.addEventListener("click", () => {
    row.remove();
    refreshRuleRows();
  });
  row.append(catSel, countSel, removeBtn);
  ruleRowsEl.appendChild(row);
  refreshRuleRows();
}

addRowBtn.addEventListener("click", addRuleRow);
addRuleRow();

ctaBtn.addEventListener("click", () => {
  const requests = ruleRows().map(row => ({
    cat: categoryById(row.querySelector(".cat-select").value),
    count: parseInt(row.querySelector(".count-select").value, 10),
  }));
  generateCategories(requests, readConstraints());
});

/* ---------- 당첨 확인 ---------- */
let latestRound = null;
let shownDraw = null;
const drawRoundInput = $("draw-round");
const checkError = $("check-error");
const checkResults = $("check-results");

function renderDraw(draw) {
  shownDraw = draw;
  drawRoundInput.value = draw.round;
  $("draw-date").textContent = draw.draw_date;
  const balls = $("draw-balls");
  balls.replaceChildren();
  draw.numbers.forEach(n => balls.appendChild(ball(n, ballColorClass(n))));
  balls.appendChild(el("span", "plus", "+"));
  const bonus = ball(draw.bonus, ballColorClass(draw.bonus));
  bonus.title = "보너스 번호";
  bonus.setAttribute("aria-label", `보너스 ${draw.bonus}`);
  balls.appendChild(bonus);
  $("draw-prev").disabled = draw.round <= 1;
  $("draw-next").disabled = latestRound !== null && draw.round >= latestRound;
}

async function loadDraw(round) {
  checkError.textContent = "";
  try {
    renderDraw(await api(round ? `/api/draws/${round}` : "/api/draws/latest"));
  } catch (err) {
    checkError.textContent = err.message;
    if (shownDraw) drawRoundInput.value = shownDraw.round;
  }
}

$("draw-prev").addEventListener("click", () => shownDraw && loadDraw(shownDraw.round - 1));
$("draw-next").addEventListener("click", () => shownDraw && loadDraw(shownDraw.round + 1));
drawRoundInput.addEventListener("change", () => {
  const round = parseInt(drawRoundInput.value, 10);
  if (round >= 1) loadDraw(round);
});

function parseTicket(text) {
  const parts = text.split(/[\s,]+/).filter(Boolean);
  const numbers = parts.map(Number);
  if (numbers.length !== 6 || numbers.some(n => !Number.isInteger(n) || n < 1 || n > 45)) {
    throw new Error("1~45 사이 번호 6개를 입력해주세요.");
  }
  if (new Set(numbers).size !== 6) throw new Error("중복된 번호가 있습니다.");
  return numbers;
}

async function runCheck(tickets, title) {
  checkError.textContent = "";
  const data = await api("/api/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tickets, round: shownDraw ? shownDraw.round : null }),
  });
  const winning = new Set(data.draw.numbers);
  checkResults.replaceChildren();

  const wins = data.results.filter(r => r.rank).length;
  checkResults.appendChild(el("p", "empty-msg",
    `${title} · ${data.draw.round}회 기준 · ${data.results.length}개 중 ${wins}개 당첨`));

  data.results.forEach(result => {
    const card = el("div", "card");
    const header = el("div", "card-header-row");
    header.appendChild(el("div", "combo-title", `${result.matched.length}개 일치`));
    header.appendChild(el("span", "rank-badge" + (result.rank ? " win" : ""), result.rank_label));
    card.appendChild(header);
    const balls = el("div", "balls");
    result.numbers.forEach(n => balls.appendChild(ball(n, winning.has(n) ? ballColorClass(n) : "miss")));
    card.appendChild(balls);
    if (result.bonus_matched) {
      card.appendChild(el("p", "check-meta", `보너스 번호 ${data.draw.bonus} 포함`));
    }
    checkResults.appendChild(card);
  });
}

$("manual-check").addEventListener("click", async () => {
  try {
    await runCheck([parseTicket($("manual-input").value)], "직접 입력");
  } catch (err) {
    checkError.textContent = err.message;
  }
});
$("manual-input").addEventListener("keydown", event => {
  if (event.key === "Enter") $("manual-check").click();
});
$("cart-check").addEventListener("click", async () => {
  if (cart.length === 0) {
    checkError.textContent = "장바구니가 비어 있습니다. 번호 생성 탭에서 조합을 담아보세요.";
    return;
  }
  try {
    await runCheck(cart, "장바구니 전체");
  } catch (err) {
    checkError.textContent = err.message;
  }
});
tabLoaders.check = () => { if (!shownDraw) loadDraw(null); };

/* ---------- 차트 공통 ---------- */
function niceScale(max, tickCount = 4) {
  if (max <= 0) return { max: 1, step: 1 };
  const rough = max / tickCount;
  const mag = Math.pow(10, Math.floor(Math.log10(rough)));
  const norm = rough / mag;
  const step = (norm <= 1 ? 1 : norm <= 2 ? 2 : norm <= 2.5 ? 2.5 : norm <= 5 ? 5 : 10) * mag;
  return { max: Math.ceil(max / step) * step, step };
}

/* 세로 막대 차트. items: [{ value, color, xLabel, tipTitle, tipSub }] */
function columnChart(container, { items, ref, yFormat = fmtInt, ariaLabel }) {
  const rawMax = Math.max(...items.map(i => i.value), ref ? ref.value : 0);
  const { max, step } = niceScale(rawMax);
  const pct = v => (v / max) * 100;

  const chart = el("div", "col-chart");
  chart.setAttribute("role", "img");
  chart.setAttribute("aria-label", ariaLabel);
  const yAxis = el("div", "y-axis");
  const plot = el("div", "plot");
  for (let v = 0; v <= max + step / 2; v += step) {
    const tick = el("span", null, yFormat(v));
    tick.style.bottom = pct(v) + "%";
    yAxis.appendChild(tick);
    if (v > 0) {
      const line = el("div", "gridline");
      line.style.bottom = pct(v) + "%";
      plot.appendChild(line);
    }
  }

  const cols = el("div", "cols");
  items.forEach(item => {
    const col = el("button", "col");
    col.type = "button";
    col.setAttribute("aria-label", `${item.tipTitle}, ${item.tipSub}`);
    const bar = el("span", "bar");
    bar.style.setProperty("--h", pct(item.value) + "%");
    if (item.color) bar.style.setProperty("--c", item.color);
    col.appendChild(bar);
    attachTooltip(col, item.tipTitle, item.tipSub);
    cols.appendChild(col);
  });
  plot.appendChild(cols);

  if (ref) {
    const line = el("div", "ref-line");
    line.style.bottom = pct(ref.value) + "%";
    plot.appendChild(line);
    if (ref.label) {
      const label = el("span", "ref-label", ref.label);
      label.style.bottom = pct(ref.value) + "%";
      plot.appendChild(label);
    }
  }

  const xAxis = el("div", "x-axis");
  items.forEach(item => xAxis.appendChild(el("span", null, item.xLabel || "")));

  chart.append(yAxis, plot, xAxis);
  container.replaceChildren(chart);
}

function tableView(container, headers, rows, numericFrom = 1) {
  const details = el("details", "table-view");
  details.appendChild(el("summary", null, "표로 보기"));
  const wrap = el("div", "table-wrap");
  const table = el("table");
  const head = el("tr");
  headers.forEach((h, i) => head.appendChild(el("th", i >= numericFrom ? "num-col" : null, h)));
  table.appendChild(head);
  rows.forEach(cells => {
    const tr = el("tr");
    cells.forEach((c, i) => tr.appendChild(el("td", i >= numericFrom ? "num-col" : "strong", c)));
    table.appendChild(tr);
  });
  wrap.appendChild(table);
  details.appendChild(wrap);
  container.appendChild(details);
}

/* ---------- 통계 ---------- */
let statsWindow = 0;
let statsLoadedWindow = null;
let statsRequest = 0;
const statsBody = $("stats-body");

function tile(label, value, note) {
  const node = el("div", "tile");
  node.append(el("div", "tile-label", label), el("div", "tile-value", value));
  if (note) node.appendChild(el("div", "tile-note", note));
  return node;
}

function renderStats(data) {
  const scope = data.window ? `최근 ${data.total_draws}회` : "전체";
  const byCount = [...data.numbers].sort((a, b) => b.count - a.count || a.number - b.number);
  const top = byCount[0];
  const coldest = [...data.numbers].sort((a, b) => (b.gap ?? -1) - (a.gap ?? -1))[0];
  $("stat-tiles").replaceChildren(
    tile("분석 회차", `${fmtInt(data.total_draws)}회`, `${data.first_round}회 ~ ${data.latest_round}회`),
    tile("최다 출현 번호", `${top.number}번`, `${scope} ${fmtInt(top.count)}회`),
    tile("최장 미출현 번호", `${coldest.number}번`, `${coldest.gap}회째 안 나옴`),
  );

  // 번호별 출현: 상위 15 / 하위 15 / 그 외를 색으로 구분 (생성 규칙의 고·저확률 풀과 같은 기준)
  const highSet = new Set(byCount.slice(0, 15).map(n => n.number));
  const lowSet = new Set(byCount.slice(-15).map(n => n.number));
  const expected = data.total_draws * data.expected_ratio;
  $("freq-sub").textContent =
    `${scope} 기준 · 점선은 모든 번호가 똑같이 나왔을 때의 기대값(${expected.toFixed(1)}회)입니다`;
  const legend = $("freq-legend");
  legend.replaceChildren();
  [["var(--high)", "상위 15개"], ["var(--low)", "하위 15개"], ["var(--other)", "그 외"]].forEach(([color, label]) => {
    const key = el("i");
    key.style.background = color;
    const item = el("span");
    item.append(key, document.createTextNode(label));
    legend.appendChild(item);
  });
  const lineKey = el("span");
  lineKey.append(el("i", "line"), document.createTextNode("기대값"));
  legend.appendChild(lineKey);

  const freqEl = $("chart-freq");
  columnChart(freqEl, {
    ariaLabel: `${scope} 번호별 출현 횟수 막대 차트`,
    ref: { value: expected },
    items: data.numbers.map(n => ({
      value: n.count,
      color: highSet.has(n.number) ? "var(--high)" : lowSet.has(n.number) ? "var(--low)" : "var(--other)",
      xLabel: n.number === 1 || n.number % 5 === 0 ? String(n.number) : "",
      tipTitle: `${n.number}번 · ${fmtInt(n.count)}회`,
      tipSub: `출현율 ${(n.ratio * 100).toFixed(1)}% · 마지막 ${n.last_round ?? "-"}회`,
    })),
  });
  tableView(freqEl, ["번호", "출현", "출현율", "마지막 출현", "미출현"],
    data.numbers.map(n => [
      `${n.number}`, fmtInt(n.count), `${(n.ratio * 100).toFixed(1)}%`,
      n.last_round ? `${n.last_round}회` : "-", n.gap !== null ? `${n.gap}회` : "-",
    ]));

  const oddEl = $("chart-odd");
  columnChart(oddEl, {
    ariaLabel: "홀수 개수별 회차 수 막대 차트",
    items: data.odd_even.map(o => ({
      value: o.count,
      xLabel: `${o.odd}:${o.even}`,
      tipTitle: `${fmtInt(o.count)}회`,
      tipSub: `홀${o.odd} : 짝${o.even} · ${(o.count / data.total_draws * 100).toFixed(1)}%`,
    })),
  });
  tableView(oddEl, ["홀:짝", "회차 수", "비율"],
    data.odd_even.map(o => [`${o.odd}:${o.even}`, fmtInt(o.count), `${(o.count / data.total_draws * 100).toFixed(1)}%`]));

  const rangeEl = $("chart-range");
  const pctFmt = v => `${Math.round(v * 100)}%`;
  columnChart(rangeEl, {
    ariaLabel: "번호 구간별 출현 비율 막대 차트",
    yFormat: pctFmt,
    items: data.ranges.map(r => ({
      value: r.share,
      xLabel: r.label,
      tipTitle: `${(r.share * 100).toFixed(1)}%`,
      tipSub: `${r.label} · 기대 ${(r.expected_share * 100).toFixed(1)}%`,
    })),
  });
  // 구간마다 기대 비율이 다르므로 막대별 기준선을 그린다.
  const { max: rangeMax } = niceScale(Math.max(...data.ranges.map(r => r.share)));
  rangeEl.querySelectorAll(".col").forEach((col, i) => {
    const mark = el("span", "ref-line");
    mark.style.bottom = (data.ranges[i].expected_share / rangeMax) * 100 + "%";
    mark.style.left = "15%";
    mark.style.right = "15%";
    col.style.position = "relative";
    col.appendChild(mark);
  });
  tableView(rangeEl, ["구간", "출현 횟수", "비율", "기대 비율"],
    data.ranges.map(r => [r.label, fmtInt(r.count), `${(r.share * 100).toFixed(1)}%`, `${(r.expected_share * 100).toFixed(1)}%`]));

  const sumEl = $("chart-sum");
  columnChart(sumEl, {
    ariaLabel: "당첨번호 합계 구간별 회차 수 막대 차트",
    items: data.sums.map((s, i) => ({
      value: s.count,
      xLabel: i % 2 === 0 ? String(s.from) : "",
      tipTitle: `${fmtInt(s.count)}회`,
      tipSub: `합계 ${s.label}`,
    })),
  });
  tableView(sumEl, ["합계 구간", "회차 수"], data.sums.map(s => [s.label, fmtInt(s.count)]));
}

async function renderRecentDraws() {
  const box = $("recent-draws");
  if (box.childElementCount) return;
  const data = await api("/api/draws?limit=10");
  data.draws.forEach(draw => {
    const row = el("div", "recent-row");
    row.appendChild(el("span", "round", `${draw.round}회`));
    const balls = el("div", "balls");
    draw.numbers.forEach(n => balls.appendChild(ball(n, "small " + ballColorClass(n))));
    balls.appendChild(el("span", "plus", "+"));
    balls.appendChild(ball(draw.bonus, "small " + ballColorClass(draw.bonus)));
    row.appendChild(balls);
    box.appendChild(row);
  });
}

async function loadStats() {
  if (statsLoadedWindow === statsWindow) return;
  const requestId = ++statsRequest;
  statsBody.classList.add("loading");
  try {
    const data = await api(`/api/stats?window=${statsWindow}`);
    if (requestId !== statsRequest) return;
    renderStats(data);
    statsLoadedWindow = statsWindow;
    await renderRecentDraws();
  } catch (err) {
    alert("통계 불러오기 실패: " + err.message);
  } finally {
    if (requestId === statsRequest) statsBody.classList.remove("loading");
  }
}

document.querySelectorAll("#window-filter button").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("#window-filter button").forEach(b => b.setAttribute("aria-checked", String(b === btn)));
    statsWindow = parseInt(btn.dataset.window, 10);
    loadStats();
  });
});
tabLoaders.stats = loadStats;

/* ---------- 구매 시뮬레이션 ---------- */
const simAmountsEl = $("sim-amounts");
const simOutput = $("sim-output");
const simRerun = $("sim-rerun");
let simData = null;
let simAmount = 5;

function fmtExpected(v) {
  if (v < 0.01) return "≈0";
  if (v < 10) return v.toFixed(2);
  return fmtInt(Math.round(v));
}

function simTable(headers) {
  const wrap = el("div", "table-wrap");
  wrap.style.marginTop = "0.75rem";
  const table = el("table", "sim-table");
  const head = el("tr");
  headers.forEach((h, i) => head.appendChild(el("th", i ? "num-col" : null, h)));
  table.appendChild(head);
  wrap.appendChild(table);
  return { wrap, table };
}

// 1~3등이 실제로 나온 칸은 강조한다 (기댓값 행은 강조하지 않음).
function rankCells(tr, ranks, format = fmtInt) {
  [1, 2, 3, 4, 5].forEach(rank => {
    const v = ranks[rank];
    const cls = "num-col" + (format === fmtInt && v > 0 && rank <= 3 ? " hit" : "");
    tr.appendChild(el("td", cls, format(v)));
  });
}

function renderSimAmounts() {
  simAmountsEl.replaceChildren();
  simData.results.forEach(r => {
    const btn = el("button", null, fmtAmount(r.amount));
    btn.type = "button";
    btn.setAttribute("role", "radio");
    btn.setAttribute("aria-checked", String(r.amount === simAmount));
    btn.addEventListener("click", () => {
      simAmount = r.amount;
      renderSimulation();
    });
    simAmountsEl.appendChild(btn);
  });
}

function renderSimulation() {
  renderSimAmounts();
  const drawByRound = new Map(simData.draws.map(d => [d.round, d]));
  const result = simData.results.find(r => r.amount === simAmount);
  const roundCount = simData.draws.length;
  simOutput.replaceChildren();

  // 선택한 개수: 회차별 등수 표
  const detail = el("div", "card");
  detail.appendChild(el("h3", "chart-title", `회차마다 ${fmtAmount(result.amount)}씩 구매`));
  const summary = el("div", "sim-summary");
  const addSummary = (label, value) => {
    const item = el("span", null, label + " ");
    item.appendChild(el("b", null, value));
    summary.appendChild(item);
  };
  const chance = result.first_prize_chance * 100;
  addSummary("회당 비용", fmtWon(result.cost_per_round));
  addSummary(`${roundCount}회 총 비용`, fmtWon(result.total_cost));
  addSummary("회당 1등이 1개라도 나올 확률", `${chance < 1 ? chance.toPrecision(2) : chance.toFixed(1)}%`);
  detail.appendChild(summary);

  const { wrap, table } = simTable(["회차", "1등", "2등", "3등", "4등", "5등"]);
  result.per_round.forEach(row => {
    const draw = drawByRound.get(row.round);
    const tr = el("tr");
    const roundCell = el("td", "strong nowrap", `${row.round}회`);
    roundCell.appendChild(el("span", "sim-draw", `${draw.numbers.join("·")} +${draw.bonus}`));
    tr.appendChild(roundCell);
    rankCells(tr, row.ranks);
    table.appendChild(tr);
  });
  const sumRow = el("tr", "sum-row");
  sumRow.appendChild(el("td", "nowrap", "합계"));
  rankCells(sumRow, result.totals);
  table.appendChild(sumRow);
  const expRow = el("tr");
  expRow.appendChild(el("td", "nowrap", "이론 기댓값"));
  rankCells(expRow, result.expected, fmtExpected);
  table.appendChild(expRow);
  detail.appendChild(wrap);
  detail.appendChild(el("p", "hint", result.method === "direct"
    ? "무작위 번호를 실제로 하나씩 뽑아 각 회차 당첨번호와 맞춰본 결과입니다."
    : "개수가 많아 하나씩 뽑는 대신, 무작위 번호를 이만큼 샀을 때의 등수별 개수를 확률분포에서 바로 뽑았습니다. 하나씩 뽑은 것과 통계적으로 같은 결과입니다."));
  simOutput.appendChild(detail);

  // 전체 개수 한눈에 보기
  const overview = el("div", "card");
  overview.appendChild(el("h3", "chart-title", `구매 개수별 ${roundCount}회 합계`));
  overview.appendChild(el("p", "chart-sub", "행을 누르면 위에서 회차별로 볼 수 있습니다."));
  const all = simTable(["회차당", "1등", "2등", "3등", "4등", "5등"]);
  simData.results.forEach(r => {
    const tr = el("tr", "selectable" + (r.amount === simAmount ? " selected" : ""));
    tr.tabIndex = 0;
    const amountCell = el("td", "strong nowrap", fmtAmount(r.amount));
    amountCell.appendChild(el("span", "sim-draw", `총 ${fmtWon(r.total_cost)}`));
    tr.appendChild(amountCell);
    rankCells(tr, r.totals);
    const select = () => {
      simAmount = r.amount;
      renderSimulation();
      simOutput.scrollIntoView({ behavior: "smooth", block: "start" });
    };
    tr.addEventListener("click", select);
    tr.addEventListener("keydown", event => { if (event.key === "Enter") select(); });
    all.table.appendChild(tr);
  });
  overview.appendChild(all.wrap);
  simOutput.appendChild(overview);
}

async function loadSimulation() {
  simRerun.disabled = true;
  $("sim-error").textContent = "";
  try {
    simData = await api("/api/simulate?rounds=5");
    renderSimulation();
  } catch (err) {
    $("sim-error").textContent = err.message;
  } finally {
    simRerun.disabled = false;
  }
}

simRerun.addEventListener("click", loadSimulation);
tabLoaders.simulate = () => { if (!simData) loadSimulation(); };

/* ---------- 백테스트 ---------- */
const btOutput = $("bt-output");
const btRun = $("bt-run");

function ruleLabel(rule) {
  return rule === "random" ? RANDOM_LABEL : categoryById(rule).shortName;
}

function renderBacktest(data) {
  btOutput.replaceChildren();
  const totalTickets = data.rounds * data.tickets_per_round;

  const summary = el("div", "card");
  summary.appendChild(el("h3", "chart-title", "규칙별 평균 일치 개수"));
  summary.appendChild(el("p", "chart-sub",
    `${data.from_round}회 ~ ${data.to_round}회 (${data.rounds}회) · 규칙마다 회차당 ${data.tickets_per_round}개씩 총 ${fmtInt(totalTickets)}개 조합 · ` +
    `점선은 이론 기댓값 ${data.expected.avg_matches.toFixed(2)}개`));

  const chart = el("div", "hbar-chart");
  const max = Math.max(...data.results.map(r => r.avg_matches), data.expected.avg_matches) * 1.1;
  data.results.forEach(r => {
    const row = el("div", "hbar-row");
    row.tabIndex = 0;
    row.appendChild(el("span", "hbar-label", ruleLabel(r.rule)));
    const track = el("div", "hbar-track");
    const bar = el("div", "bar");
    bar.style.setProperty("--w", (r.avg_matches / max) * 100 + "%");
    bar.style.setProperty("--c", r.rule === "random" ? "var(--other)" : "var(--low)");
    const ref = el("span", "ref-line");
    ref.style.setProperty("--ref", (data.expected.avg_matches / max) * 100 + "%");
    track.append(bar, ref);
    row.appendChild(track);
    row.appendChild(el("span", "hbar-value", r.avg_matches.toFixed(2)));
    attachTooltip(row, `평균 ${r.avg_matches.toFixed(3)}개 일치`,
      `${ruleLabel(r.rule)} · 5등 이상 ${r.wins}회 (기대 ${data.expected.wins.toFixed(1)}회)`);
    chart.appendChild(row);
  });
  summary.appendChild(chart);
  btOutput.appendChild(summary);

  const tableCard = el("div", "card");
  tableCard.appendChild(el("h3", "chart-title", "등수별 당첨 횟수"));
  tableCard.appendChild(el("p", "chart-sub",
    "기댓값 행은 완전 무작위로 샀을 때 같은 장수에서 기대되는 평균 당첨 횟수입니다."));
  const wrap = el("div", "table-wrap");
  wrap.style.marginTop = "0.75rem";
  const table = el("table");
  const head = el("tr");
  ["규칙", "평균 일치", "5등", "4등", "3등", "2등", "1등", "당첨 합계"].forEach((h, i) =>
    head.appendChild(el("th", i ? "num-col" : null, h)));
  table.appendChild(head);
  const addRow = (label, avg, ranks, wins, digits) => {
    const tr = el("tr");
    tr.appendChild(el("td", "strong nowrap", label));
    tr.appendChild(el("td", "num-col", avg.toFixed(2)));
    [5, 4, 3, 2, 1].forEach(rank => {
      const v = ranks[rank];
      tr.appendChild(el("td", "num-col", digits ? (v < 0.01 ? "≈0" : v.toFixed(2)) : fmtInt(v)));
    });
    tr.appendChild(el("td", "num-col strong", digits ? wins.toFixed(1) : fmtInt(wins)));
    table.appendChild(tr);
  };
  data.results.forEach(r => addRow(ruleLabel(r.rule), r.avg_matches, r.ranks, r.wins, false));
  addRow("이론 기댓값", data.expected.avg_matches, data.expected.ranks, data.expected.wins, true);
  wrap.appendChild(table);
  tableCard.appendChild(wrap);
  tableCard.appendChild(el("p", "hint",
    "5등 이상 당첨 횟수가 규칙마다 조금씩 다른 것은 표본이 작아서 생기는 우연한 차이입니다. " +
    "검증 회차를 늘리거나 다시 실행하면 순위가 쉽게 바뀝니다."));
  btOutput.appendChild(tableCard);
}

btRun.addEventListener("click", async () => {
  btRun.disabled = true;
  $("bt-error").textContent = "";
  const previous = [...btOutput.childNodes];
  btOutput.replaceChildren(el("p", "spinner-note", "과거 회차를 하나씩 재현하는 중입니다..."));
  try {
    const rounds = $("bt-rounds").value;
    const tickets = $("bt-tickets").value;
    renderBacktest(await api(`/api/backtest?rounds=${rounds}&tickets=${tickets}`));
  } catch (err) {
    btOutput.replaceChildren(...previous);
    $("bt-error").textContent = err.message;
  } finally {
    btRun.disabled = false;
  }
});

/* ---------- 초기화 ---------- */
(async function init() {
  try {
    const latest = await api("/api/draws/latest");
    latestRound = latest.round;
    $("data-status").textContent = `${latest.round}회 (${latest.draw_date})까지 반영 · 실험용 번호 생성기`;
    renderDraw(latest);
  } catch {
    /* 데이터가 없어도 생성 화면은 에러 메시지로 안내된다 */
  }
  const isTab = name => tabButtons.some(b => b.dataset.tab === name);
  const hashTab = location.hash.slice(1);
  const savedTab = storageGet(TAB_KEY);
  showTab(isTab(hashTab) ? hashTab : isTab(savedTab) ? savedTab : "generate");
})();
