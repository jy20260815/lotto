INDEX_HTML = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>로또 번호 생성기</title>
<style>
  :root {
    --bg: #0f1115;
    --card: #171a21;
    --card-strong: #171a2c;
    --card-strong-hover: #1c2038;
    --text: #e8e8ea;
    --muted: #9aa0ac;
    --desc: #b7bcc7;
    --border: #2a2f3a;
    --accent: #4f7cff;
    --high: #e0523f;
    --low: #2f9e6e;
    --neutral: #8a5fd6;
    --warn: #e0b83f;
  }
  :root[data-theme="light"] {
    --bg: #f4f5f9;
    --card: #ffffff;
    --card-strong: #eef1ff;
    --card-strong-hover: #e2e7ff;
    --text: #1a1c22;
    --muted: #5b6270;
    --desc: #454b58;
    --border: #e2e4ea;
    --accent: #3757e8;
    --high: #d1453a;
    --low: #1f8f5c;
    --neutral: #7c4dd6;
    --warn: #a9750a;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, "Segoe UI", "Malgun Gothic", sans-serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    justify-content: center;
    padding: 2.5rem 1rem 6rem;
  }
  main { width: 100%; max-width: 560px; }

  .header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
  h1 { font-size: 1.4rem; margin-bottom: 0.25rem; }
  p.subtitle { color: var(--muted); margin-top: 0; font-size: 0.9rem; }
  h2.section-title { font-size: 0.95rem; margin: 1.75rem 0 0.6rem; }

  .icon-btn {
    background: var(--card);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.5rem 0.8rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.85rem;
    white-space: nowrap;
  }
  .icon-btn:hover { border-color: var(--accent); }

  .back-btn {
    background: none;
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.5rem 0.9rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.85rem;
  }
  .back-btn:hover { border-color: var(--accent); }

  /* ---------- 빠른 생성 ---------- */
  .quick-box {
    border: 1.5px dashed color-mix(in srgb, var(--accent) 40%, var(--border));
    background: color-mix(in srgb, var(--accent) 6%, var(--card));
    border-radius: 14px;
    padding: 1rem;
  }
  .chip-row { display: flex; flex-wrap: wrap; gap: 0.6rem; }
  .chip {
    --c: var(--accent);
    display: inline-flex;
    align-items: center;
    border: 1.5px solid var(--c);
    color: var(--c);
    background: var(--card);
    padding: 0.55rem 0.95rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
  }
  .chip:hover { background: var(--c); color: #fff; }
  .chip:disabled { opacity: 0.5; cursor: default; }
  .chip.hero { font-weight: 700; }

  /* ---------- 직접 설정 ---------- */
  .config-card {
    margin-top: 1.25rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.1rem 1.25rem 1.25rem;
  }
  .field-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.9rem; }
  .field label {
    display: block;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--muted);
    margin-bottom: 0.4rem;
  }
  .field select {
    width: 100%;
    background: var(--card-strong);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.6rem 0.7rem;
    border-radius: 8px;
    font-size: 0.88rem;
  }
  .cta-btn {
    width: 100%;
    margin-top: 1.1rem;
    padding: 0.95rem;
    border: none;
    border-radius: 10px;
    background: var(--accent);
    color: #fff;
    font-size: 0.98rem;
    font-weight: 700;
    cursor: pointer;
  }
  .cta-btn:hover { filter: brightness(1.08); }
  .cta-btn:disabled { opacity: 0.5; cursor: default; }

  /* ---------- 결과 카드 ---------- */
  #results { margin-top: 1rem; display: flex; flex-direction: column; gap: 1rem; }
  .result-card {
    background: var(--card);
    border-radius: 12px;
    padding: 1.1rem 1.5rem 1.25rem;
    border: 1px solid var(--border);
    border-top: 4px solid var(--cat, var(--accent));
  }
  .card-header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; gap: 0.5rem; }
  .combo-title { font-size: 0.85rem; font-weight: 700; }
  .tag-row { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.85rem; }
  .pill-tag {
    font-size: 0.7rem;
    font-weight: 700;
    padding: 0.18rem 0.55rem;
    border-radius: 999px;
    background: color-mix(in srgb, var(--cat, var(--accent)) 18%, transparent);
    color: var(--cat, var(--accent));
  }
  .copy-btn {
    background: var(--card-strong);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.3rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    cursor: pointer;
    white-space: nowrap;
  }
  .copy-btn:hover { border-color: var(--accent); }
  .card-actions { display: flex; gap: 0.4rem; flex-shrink: 0; }
  .cart-btn.in-cart-btn { border-color: var(--accent); color: var(--accent); background: var(--card); }

  .balls { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1rem; }
  .ball {
    position: relative;
    width: 2.4rem; height: 2.4rem;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 600;
    color: #fff;
  }
  .ball.high { background: var(--high); }
  .ball.low { background: var(--low); }
  .ball.neutral { background: var(--neutral); }

  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  td { padding: 0.4rem 0.3rem; border-bottom: 1px solid var(--border); color: var(--muted); }
  td.num { color: var(--text); font-weight: 600; width: 2.5rem; }
  .traits {
    margin-top: 0.9rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border);
    font-size: 0.8rem;
    color: var(--muted);
    line-height: 1.6;
  }
  .traits .disclaimer { color: var(--warn); margin-top: 0.4rem; }
  .empty-msg { color: var(--muted); font-size: 0.9rem; }
  footer { margin-top: 2rem; font-size: 0.78rem; color: var(--muted); line-height: 1.5; }
  footer p { margin: 0.6rem 0 0; }

  /* ---------- 카테고리 설명 ---------- */
  details.info-box {
    margin-top: 1.75rem;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
  }
  details.info-box summary {
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--muted);
  }
  .info-item { margin-top: 0.9rem; padding-top: 0.9rem; border-top: 1px solid var(--border); }
  .info-item:first-of-type { border-top: none; padding-top: 0; margin-top: 0.75rem; }
  .info-item strong { font-size: 0.85rem; margin-right: 0.4rem; }
  .info-item p { margin: 0.3rem 0 0; color: var(--desc); font-size: 0.8rem; line-height: 1.5; }

  .cart-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem; }
  .cart-header h2 { margin: 0; font-size: 1.1rem; }
  .cart-hint { color: var(--muted); font-size: 0.85rem; margin: 0 0 1rem; }
  #cart-list { display: flex; flex-direction: column; gap: 1rem; margin-bottom: 1.5rem; }
  h3.today-title { font-size: 0.95rem; margin: 1.5rem 0 0.3rem; }
  #today-pick .balls { margin-top: 0.5rem; }

  #cart-fab {
    position: fixed;
    right: 1.5rem; bottom: 1.5rem;
    padding: 0.7rem 1.2rem;
    border-radius: 999px;
    background: var(--accent);
    color: #fff;
    border: none;
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.88rem;
    font-weight: 700;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
    z-index: 20;
  }
  #cart-badge {
    background: rgba(255, 255, 255, 0.25);
    color: #fff;
    font-size: 0.72rem;
    font-weight: 700;
    border-radius: 999px;
    min-width: 1.3rem; height: 1.3rem;
    display: flex; align-items: center; justify-content: center;
    padding: 0 0.3rem;
  }
</style>
</head>
<body>
<main>
  <div class="header-row">
    <div>
      <h1>로또 번호 생성기</h1>
      <p class="subtitle">역대 회차 출현 빈도 기반 실험용 번호 생성기</p>
    </div>
    <button class="icon-btn" id="theme-toggle">다크 모드</button>
  </div>

  <div id="view-generator">
    <h2 class="section-title">빠른 생성</h2>
    <div class="quick-box">
      <div class="chip-row" id="chip-row"></div>
    </div>

    <h2 class="section-title">직접 설정</h2>
    <div class="config-card">
      <div class="field-grid">
        <div class="field">
          <label for="cat-select">카테고리</label>
          <select id="cat-select"></select>
        </div>
        <div class="field">
          <label for="count-select">생성 개수</label>
          <select id="count-select">
            <option value="1">1개</option>
            <option value="3">3개</option>
            <option value="5" selected>5개</option>
            <option value="10">10개</option>
          </select>
        </div>
      </div>
      <button class="cta-btn" id="cta-btn">번호 생성하기</button>
    </div>

    <h2 class="section-title">생성된 조합</h2>
    <div id="results">
      <p class="empty-msg">위 칩을 누르거나 "번호 생성하기"를 눌러 조합을 만들어보세요.</p>
    </div>

    <details class="info-box">
      <summary>카테고리별 설명 보기</summary>
      <div id="info-list"></div>
    </details>

    <footer>
      <p>
        고확률/저확률 = 역대 출현빈도 상위·하위 15개 번호 풀입니다.
        로또는 완전 무작위 추첨이라 과거 출현 빈도는 다음 회차 당첨 확률에 통계적으로
        영향을 주지 않습니다. 이 도구는 실험/재미 목적입니다.
      </p>
      <p>
        편향 가정 모드: 최근 100회차에 가중치를 준 실험적 모드로, 지금까지 이 프로젝트
        데이터로는 유의미한 편향이 발견되지 않았습니다. 근거가 약한 실험 모드입니다.
      </p>
      <p>
        비인기 조합 모드: 이 조합은 당첨 확률을 높이지 않습니다. 모든 조합의 당첨 확률은
        동일합니다. 다만 다른 사람이 이 조합을 고를 가능성이 낮아서, 당첨 시 상금을 나눠
        가질 인원이 줄어들 수 있다는 것이 이 모드의 목적입니다.
      </p>
      <p>마음에 드는 조합의 "담기" 버튼을 누르면 그 조합 전체가 장바구니에 저장됩니다. 오른쪽 아래 장바구니 버튼에서 확인하세요.</p>
    </footer>
  </div>

  <div id="view-cart" style="display: none;">
    <div class="cart-header">
      <button class="back-btn" id="back-btn">뒤로가기</button>
      <h2>장바구니</h2>
    </div>
    <p class="cart-hint">생성 화면에서 마음에 드는 조합의 "담기" 버튼을 누르면 그 조합 전체가 여기 저장됩니다. 그중 하나를 오늘의 번호로 선택해보세요.</p>
    <div id="cart-list"></div>

    <h3 class="today-title">오늘의 나의 번호</h3>
    <div id="today-pick"></div>
  </div>
</main>

<button id="cart-fab" title="장바구니">
  장바구니
  <span id="cart-badge">0</span>
</button>

<script>
const THEME_KEY = "lotto_theme";
const CART_KEY = "lotto_cart";
const TODAY_KEY = "lotto_today_pick";

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
function categoryById(id) {
  return CATEGORIES.find(c => c.id === id) || CATEGORIES[0];
}

function loadCart() {
  // 이전 버전은 장바구니를 낱개 번호 배열로 저장했다. 조합 단위 배열([[..6개..], ...])이
  // 아닌 옛 형식이 남아있으면 크래시를 막기 위해 비운다.
  let parsed;
  try {
    parsed = JSON.parse(localStorage.getItem(CART_KEY) || "[]");
  } catch {
    parsed = [];
  }
  if (!Array.isArray(parsed) || !parsed.every(item => Array.isArray(item))) {
    return [];
  }
  return parsed;
}
function loadTodayPick() {
  let parsed;
  try {
    parsed = JSON.parse(localStorage.getItem(TODAY_KEY) || "null");
  } catch {
    parsed = null;
  }
  return Array.isArray(parsed) ? parsed : null;
}

let cart = loadCart();
let todayPick = loadTodayPick();
let busy = false;

const themeToggleBtn = document.getElementById("theme-toggle");
const viewGenerator = document.getElementById("view-generator");
const viewCart = document.getElementById("view-cart");
const cartFab = document.getElementById("cart-fab");
const cartBadge = document.getElementById("cart-badge");
const backBtn = document.getElementById("back-btn");
const cartListEl = document.getElementById("cart-list");
const todayPickEl = document.getElementById("today-pick");
const chipRow = document.getElementById("chip-row");
const catSelect = document.getElementById("cat-select");
const countSelect = document.getElementById("count-select");
const ctaBtn = document.getElementById("cta-btn");
const resultsEl = document.getElementById("results");
const infoList = document.getElementById("info-list");

/* ---------- 테마 ---------- */
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem(THEME_KEY, theme);
  themeToggleBtn.textContent = theme === "light" ? "다크 모드" : "라이트 모드";
}
applyTheme(localStorage.getItem(THEME_KEY) || "dark");
themeToggleBtn.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  applyTheme(current === "dark" ? "light" : "dark");
});

/* ---------- 화면 전환 ---------- */
function showGenerator() {
  viewGenerator.style.display = "";
  viewCart.style.display = "none";
  cartFab.style.display = "flex";
}
function showCart() {
  viewGenerator.style.display = "none";
  viewCart.style.display = "";
  cartFab.style.display = "none";
  renderCart();
}
backBtn.addEventListener("click", showGenerator);
cartFab.addEventListener("click", showCart);

/* ---------- 장바구니 (조합 단위로 저장) ---------- */
function comboKey(numbers) {
  return [...numbers].sort((a, b) => a - b).join(",");
}
function findCartIndex(numbers) {
  const key = comboKey(numbers);
  return cart.findIndex(c => comboKey(c) === key);
}
function isComboInCart(numbers) {
  return findCartIndex(numbers) !== -1;
}
function persistCart() {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  cartBadge.textContent = cart.length;
  document.querySelectorAll(".cart-btn[data-numbers]").forEach(updateCartBtn);
}
function persistTodayPick() {
  localStorage.setItem(TODAY_KEY, JSON.stringify(todayPick));
}
function updateCartBtn(btn) {
  const numbers = btn.dataset.numbers.split(",").map(Number);
  const inCart = isComboInCart(numbers);
  btn.textContent = inCart ? "담김" : "담기";
  btn.classList.toggle("in-cart-btn", inCart);
}
function toggleCombo(numbers) {
  const idx = findCartIndex(numbers);
  if (idx === -1) {
    cart.push([...numbers].sort((a, b) => a - b));
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

async function copyText(text, btn, doneLabel, idleLabel) {
  try {
    await navigator.clipboard.writeText(text);
    btn.textContent = doneLabel;
    setTimeout(() => { btn.textContent = idleLabel; }, 1500);
  } catch (err) {
    alert("복사 실패: " + err.message);
  }
}

function buildCartCard(numbers) {
  const isToday = todayPick && comboKey(todayPick) === comboKey(numbers);

  const card = document.createElement("div");
  card.className = "result-card";

  const headerRow = document.createElement("div");
  headerRow.className = "card-header-row";

  const title = document.createElement("div");
  title.className = "combo-title";
  title.textContent = isToday ? "오늘의 번호" : "담은 조합";
  headerRow.appendChild(title);

  const actions = document.createElement("div");
  actions.className = "card-actions";

  const todayBtn = document.createElement("button");
  todayBtn.className = "copy-btn" + (isToday ? " in-cart-btn" : "");
  todayBtn.textContent = isToday ? "선택 해제" : "오늘의 번호로 선택";
  todayBtn.addEventListener("click", () => {
    todayPick = isToday ? null : [...numbers];
    persistTodayPick();
    renderCart();
  });
  actions.appendChild(todayBtn);

  const copyBtn = document.createElement("button");
  copyBtn.className = "copy-btn";
  copyBtn.textContent = "복사";
  copyBtn.addEventListener("click", () => copyText(numbers.join(", "), copyBtn, "복사됨!", "복사"));
  actions.appendChild(copyBtn);

  const removeBtn = document.createElement("button");
  removeBtn.className = "copy-btn";
  removeBtn.textContent = "삭제";
  removeBtn.addEventListener("click", () => {
    toggleCombo(numbers);
    renderCart();
  });
  actions.appendChild(removeBtn);

  headerRow.appendChild(actions);
  card.appendChild(headerRow);

  const balls = document.createElement("div");
  balls.className = "balls";
  numbers.forEach(n => {
    const ball = document.createElement("div");
    ball.className = "ball neutral";
    ball.textContent = n;
    balls.appendChild(ball);
  });
  card.appendChild(balls);

  return card;
}

function renderCart() {
  cartListEl.innerHTML = "";
  if (cart.length === 0) {
    cartListEl.innerHTML = '<p class="empty-msg">아직 담은 조합이 없습니다. 뒤로가기를 눌러 생성 화면에서 조합을 담아보세요.</p>';
  } else {
    cart.forEach(numbers => cartListEl.appendChild(buildCartCard(numbers)));
  }
  renderTodayPick();
}

function renderTodayPick() {
  todayPickEl.innerHTML = "";
  if (!todayPick) {
    todayPickEl.innerHTML = '<p class="empty-msg">담은 조합 중 하나를 "오늘의 번호로 선택"해보세요.</p>';
    return;
  }

  const balls = document.createElement("div");
  balls.className = "balls";
  todayPick.forEach(n => {
    const ball = document.createElement("div");
    ball.className = "ball neutral";
    ball.textContent = n;
    balls.appendChild(ball);
  });
  todayPickEl.appendChild(balls);

  const copyBtn = document.createElement("button");
  copyBtn.className = "copy-btn";
  copyBtn.textContent = "오늘의 번호 복사";
  copyBtn.addEventListener("click", () => copyText(todayPick.join(", "), copyBtn, "복사됨!", "오늘의 번호 복사"));
  todayPickEl.appendChild(copyBtn);
}

/* ---------- 조합 카드 ---------- */
function ballClass(source) {
  if (source.includes("고확률") || source.includes("고빈도")) return "high";
  if (source.includes("저확률") || source.includes("저빈도")) return "low";
  return "neutral";
}

function buildComboCard(combo, titleText, cat, indexTag) {
  const card = document.createElement("div");
  card.className = "result-card";
  card.style.setProperty("--cat", cat.color);

  const headerRow = document.createElement("div");
  headerRow.className = "card-header-row";

  const title = document.createElement("div");
  title.className = "combo-title";
  title.textContent = titleText;
  headerRow.appendChild(title);

  const actions = document.createElement("div");
  actions.className = "card-actions";

  const cartBtn = document.createElement("button");
  cartBtn.className = "copy-btn cart-btn";
  cartBtn.dataset.numbers = combo.numbers.join(",");
  cartBtn.addEventListener("click", () => toggleCombo(combo.numbers));
  actions.appendChild(cartBtn);
  updateCartBtn(cartBtn);

  const copyBtn = document.createElement("button");
  copyBtn.className = "copy-btn";
  copyBtn.textContent = "복사";
  copyBtn.addEventListener("click", () => copyText(combo.numbers.join(", "), copyBtn, "복사됨!", "복사"));
  actions.appendChild(copyBtn);

  headerRow.appendChild(actions);
  card.appendChild(headerRow);

  const tagRow = document.createElement("div");
  tagRow.className = "tag-row";
  const catTag = document.createElement("span");
  catTag.className = "pill-tag";
  catTag.textContent = cat.tag;
  tagRow.appendChild(catTag);
  if (indexTag) {
    const idxTag = document.createElement("span");
    idxTag.className = "pill-tag";
    idxTag.textContent = indexTag;
    tagRow.appendChild(idxTag);
  }
  card.appendChild(tagRow);

  const balls = document.createElement("div");
  balls.className = "balls";
  const table = document.createElement("table");

  combo.detail.forEach(item => {
    const ball = document.createElement("div");
    ball.className = "ball " + ballClass(item.source);
    ball.textContent = item.number;
    balls.appendChild(ball);

    const ratioLabel = item.source.includes("최근") ? "최근 100회 출현비율" : "역대 출현비율";
    const row = document.createElement("tr");
    row.innerHTML = `<td class="num">${item.number}</td><td>${item.source}</td><td>${ratioLabel} ${(item.ratio * 100).toFixed(1)}%</td>`;
    table.appendChild(row);
  });

  card.appendChild(balls);
  card.appendChild(table);

  if (combo.traits) {
    const traitsEl = document.createElement("div");
    traitsEl.className = "traits";
    traitsEl.innerHTML =
      "특징: " + combo.traits.join(", ") +
      '<div class="disclaimer">이 조합은 당첨 확률을 높이지 않습니다. 모든 조합의 당첨 확률은 동일합니다. ' +
      "다만 다른 사람이 이 조합을 고를 가능성이 낮아서, 당첨 시 상금을 나눠 가질 인원이 줄어들 수 있습니다.</div>";
    card.appendChild(traitsEl);
  }

  return card;
}

function addResultCards(cards) {
  const empty = resultsEl.querySelector(".empty-msg");
  if (empty) empty.remove();
  cards.forEach(card => resultsEl.prepend(card));
}

async function withBusy(fn) {
  if (busy) return;
  busy = true;
  chipRow.querySelectorAll(".chip").forEach(el => el.disabled = true);
  ctaBtn.disabled = true;
  try {
    await fn();
  } finally {
    busy = false;
    chipRow.querySelectorAll(".chip").forEach(el => el.disabled = false);
    ctaBtn.disabled = false;
  }
}

async function generateCategory(cat, count) {
  await withBusy(async () => {
    try {
      const res = await fetch(`/api/generate?rule=${cat.id}&count=${count}`);
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      const cards = data.combinations.map((combo, idx) =>
        buildComboCard(combo, cat.name, cat, count > 1 ? `조합 ${idx + 1}` : null)
      );
      addResultCards(cards.reverse());
    } catch (err) {
      alert("번호 생성 실패: " + err.message);
    }
  });
}

async function generateWeekly() {
  await withBusy(async () => {
    try {
      const res = await fetch("/api/weekly");
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      const cards = data.picks.map(combo => {
        const cat = categoryById(combo.slot_rule);
        return buildComboCard(combo, combo.label, cat, null);
      });
      addResultCards(cards.reverse());
    } catch (err) {
      alert("이번주 로또번호 생성 실패: " + err.message);
    }
  });
}

/* ---------- 빠른 생성 칩 / 직접 설정 폼 구성 ---------- */
const heroChip = document.createElement("button");
heroChip.className = "chip hero";
heroChip.textContent = "이번주 추천 전체 생성";
heroChip.addEventListener("click", generateWeekly);
chipRow.appendChild(heroChip);

CATEGORIES.forEach(cat => {
  const chip = document.createElement("button");
  chip.className = "chip";
  chip.style.setProperty("--c", cat.color);
  chip.textContent = cat.shortName;
  chip.addEventListener("click", () => generateCategory(cat, 1));
  chipRow.appendChild(chip);

  const opt = document.createElement("option");
  opt.value = cat.id;
  opt.textContent = cat.name;
  catSelect.appendChild(opt);

  const info = document.createElement("div");
  info.className = "info-item";
  info.innerHTML = `<strong style="color:${cat.color}">${cat.name}</strong><span class="pill-tag" style="--cat:${cat.color}">${cat.tag}</span><p>${cat.desc}</p>`;
  infoList.appendChild(info);
});

ctaBtn.addEventListener("click", () => {
  const cat = categoryById(catSelect.value);
  const count = parseInt(countSelect.value, 10);
  generateCategory(cat, count);
});
</script>
</body>
</html>
"""
