// Daily Parlays: loads the parlay history from the repo's `data` branch,
// computes stats in the browser, and draws the page. No build step needed.

const OWNER = "Vroonster20";
const REPO = "parlay-notifier";
const DATA_BRANCH = "data";
const DATA_URL = `https://raw.githubusercontent.com/${OWNER}/${REPO}/${DATA_BRANCH}/parlays.json`;
const COMMITS_URL = `https://api.github.com/repos/${OWNER}/${REPO}/commits?sha=${DATA_BRANCH}&per_page=1`;
const PAGE_SIZE = 10;

// Add ?data=some-file.json to the page URL to test against a local file.
const params = new URLSearchParams(location.search);
const dataSource = params.get("data") || `${DATA_URL}?t=${Date.now()}`;

const SPORTS = {
  basketball_nba: { name: "NBA", icon: "🏀" },
  americanfootball_nfl: { name: "NFL", icon: "🏈" },
  americanfootball_ncaaf: { name: "NCAAF", icon: "🏈" },
  icehockey_nhl: { name: "NHL", icon: "🏒" },
  baseball_mlb: { name: "MLB", icon: "⚾" },
};

const state = {
  parlays: [],
  sport: "all",
  reducedOnly: false,
  shown: PAGE_SIZE,
};

// ---------- Helpers ----------

const $ = (id) => document.getElementById(id);

function sportInfo(key) {
  return SPORTS[key] || { name: key.split("_").pop().toUpperCase(), icon: "🎯" };
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

// "2026-11-02" -> local Date, without the UTC shift new Date("2026-11-02") causes
function parseDay(day) {
  const [y, m, d] = day.split("-").map(Number);
  return new Date(y, m - 1, d);
}

function formatDay(day) {
  return parseDay(day).toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

function formatTime(iso) {
  return new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

function formatOdds(price) {
  const rounded = Math.round(price);
  return rounded > 0 ? `+${rounded}` : `${rounded}`.replace("-", "−");
}

function formatMoney(amount, signed = true) {
  const abs = Math.abs(amount).toFixed(2);
  if (!signed) return `$${abs}`;
  if (amount > 0.004) return `+$${abs}`;
  if (amount < -0.004) return `−$${abs}`;
  return `$${abs}`;
}

function toDecimal(price) {
  return price < 0 ? 1 + 100 / -price : 1 + price / 100;
}

// ---------- Parlay math ----------

const DROPPED = new Set(["void", "push"]);

function analyze(parlay) {
  const legs = parlay.legs;
  const active = legs.filter((l) => !DROPPED.has(l.result));
  const results = active.map((l) => l.result);

  let status = "won";
  if (results.includes("loss")) status = "lost";
  else if (results.includes("pending")) status = "pending";
  if (active.length === 0) status = "void";

  const multiplier = active.reduce((m, l) => m * toDecimal(l.price), 1);
  const profit = status === "won" ? multiplier - 1 : status === "lost" ? -1 : 0;

  return {
    ...parlay,
    status,
    reduced: active.length < legs.length,
    size: legs.length,
    activeSize: active.length,
    wins: results.filter((r) => r === "win").length,
    multiplier,
    profit,
  };
}

function summarize(parlays) {
  const decided = parlays.filter((p) => p.status === "won" || p.status === "lost");
  const won = decided.filter((p) => p.status === "won").length;
  const lost = decided.length - won;

  let legWins = 0;
  let legLosses = 0;
  for (const p of parlays) {
    for (const leg of p.legs) {
      if (leg.result === "win") legWins++;
      if (leg.result === "loss") legLosses++;
    }
  }

  // Oldest first, for the running profit line and the streak
  const chronological = [...decided].sort((a, b) => a.date.localeCompare(b.date) || a.sport.localeCompare(b.sport));
  const series = [0];
  for (const p of chronological) series.push(series[series.length - 1] + p.profit);

  let streak = 0;
  let streakType = null;
  for (let i = chronological.length - 1; i >= 0; i--) {
    const type = chronological[i].status;
    if (streakType === null) streakType = type;
    if (type !== streakType) break;
    streak++;
  }

  return {
    decided: decided.length,
    won,
    lost,
    legWins,
    legLosses,
    profit: series[series.length - 1],
    series,
    firstDate: chronological.length ? chronological[0].date : null,
    streak,
    streakType,
  };
}

// ---------- Rendering ----------

function renderTabs() {
  const tabs = $("tabs");
  tabs.textContent = "";
  const present = [...new Set(state.parlays.map((p) => p.sport))];
  const keys = ["all", ...Object.keys(SPORTS).filter((k) => present.includes(k)), ...present.filter((k) => !SPORTS[k])];

  for (const key of keys) {
    const label = key === "all" ? "All sports" : `${sportInfo(key).icon} ${sportInfo(key).name}`;
    const button = el("button", "tab", label);
    button.type = "button";
    button.setAttribute("aria-pressed", String(state.sport === key));
    button.addEventListener("click", () => {
      state.sport = key;
      state.shown = PAGE_SIZE;
      state.reducedOnly = false;
      render();
    });
    tabs.append(button);
  }
}

function renderStake(summary, label) {
  const value = $("stake-value");
  value.textContent = formatMoney(summary.profit);
  value.classList.toggle("is-down", summary.profit < -0.004);

  $("stake-caption").textContent = summary.decided
    ? `What $1 on every ${label} parlay since ${formatDay(summary.firstDate)} would have returned, across ${summary.decided} graded ${summary.decided === 1 ? "parlay" : "parlays"}.`
    : `What $1 on every ${label} parlay would have returned. The first result posts the morning after its first parlay.`;

  drawTrail(summary.series);
}

function drawTrail(series) {
  const svg = $("stake-svg");
  svg.textContent = "";
  const W = 600;
  const H = 180;
  const pad = 14;
  const ns = "http://www.w3.org/2000/svg";

  const min = Math.min(0, ...series);
  const max = Math.max(0, ...series);
  const span = max - min || 1;
  // Each balance gets an equal-width step, so even one result reads clearly
  const x = (i) => (i / series.length) * W;
  const y = (v) => pad + (1 - (v - min) / span) * (H - pad * 2);
  const zeroY = y(0);

  // Cyan above break-even, orange below
  const defs = document.createElementNS(ns, "defs");
  const grad = document.createElementNS(ns, "linearGradient");
  grad.id = "trail-color";
  grad.setAttribute("gradientUnits", "userSpaceOnUse");
  grad.setAttribute("x1", "0");
  grad.setAttribute("x2", "0");
  grad.setAttribute("y1", "0");
  grad.setAttribute("y2", String(H));
  const split = Math.min(1, (zeroY + 2) / H); // break-even itself stays cyan
  for (const [offset, color] of [[0, "#3df2ff"], [split, "#3df2ff"], [split, "#ff7a1a"], [1, "#ff7a1a"]]) {
    const stop = document.createElementNS(ns, "stop");
    stop.setAttribute("offset", String(offset));
    stop.setAttribute("stop-color", color);
    grad.append(stop);
  }
  defs.append(grad);
  svg.append(defs);

  const base = document.createElementNS(ns, "line");
  base.setAttribute("class", "baseline");
  base.setAttribute("x1", "0");
  base.setAttribute("x2", String(W));
  base.setAttribute("y1", String(zeroY));
  base.setAttribute("y2", String(zeroY));
  svg.append(base);

  // Step line: each parlay is a discrete jump, like a light cycle turning
  let d = `M 0 ${y(series[0])}`;
  for (let i = 1; i < series.length; i++) {
    d += ` H ${x(i)} V ${y(series[i])}`;
  }
  d += ` H ${W}`;

  const path = document.createElementNS(ns, "path");
  path.setAttribute("d", d);
  path.setAttribute("class", "trail");
  path.setAttribute("stroke", "url(#trail-color)");
  svg.append(path);

  if (!drawTrail.played) {
    // The stroke is measured on screen (non-scaling), so scale the length to the chart's size
    const box = svg.getBoundingClientRect();
    const scale = Math.max(box.width / W, box.height / H, 1);
    path.style.setProperty("--len", String(Math.ceil(path.getTotalLength() * scale)));
    path.classList.add("draw");
    path.addEventListener("animationend", () => path.classList.remove("draw"), { once: true });
    drawTrail.played = true;
  }
}

function renderStrip(summary) {
  const strip = $("strip");
  strip.textContent = "";
  const pct = (a, b) => (b ? `${Math.round((a / b) * 100)}%` : "–");

  const streakText = summary.streak
    ? `${summary.streakType === "won" ? "Won" : "Lost"} ${summary.streak}`
    : "–";

  const stats = [
    [`${summary.won}–${summary.lost}`, "Parlay record"],
    [pct(summary.won, summary.decided), "Parlays hit"],
    [pct(summary.legWins, summary.legWins + summary.legLosses), "Legs hit"],
    [streakText, "Current streak"],
  ];

  for (const [value, label] of stats) {
    const stat = el("div", "stat");
    stat.append(el("span", "stat-value", value), el("span", "stat-label", label));
    strip.append(stat);
  }
}

function renderDistribution(parlays) {
  const dist = $("dist");
  dist.textContent = "";
  const full = parlays.filter((p) => !p.reduced && (p.status === "won" || p.status === "lost"));
  const size = 4;
  const counts = Array(size + 1).fill(0);
  for (const p of full) if (p.size === size) counts[p.wins]++;
  const most = Math.max(...counts, 1);

  if (!full.length) {
    dist.append(el("p", "empty", "Nothing graded yet. Each parlay shows up here the morning after its games finish."));
  } else {
    for (let hits = size; hits >= 0; hits--) {
      const row = el("div", `dist-row${hits === size ? " is-win" : ""}`);
      const track = el("div", "dist-track");
      const fill = el("div", "dist-fill");
      fill.style.width = `${(counts[hits] / most) * 100}%`;
      if (counts[hits] === 0) fill.style.width = "0";
      track.append(fill);
      row.append(el("span", "dist-label", `${hits}/${size}`), track, el("span", "dist-count", String(counts[hits])));
      dist.append(row);
    }
  }

  // Reduced parlays: a postponed or tied game was dropped, so they no longer fit the 4-leg chart
  const reduced = parlays.filter((p) => p.reduced && p.status !== "pending");
  const note = $("reduced-note");
  note.textContent = "";
  const filter = $("reduced-filter");
  filter.hidden = reduced.length === 0;

  if (reduced.length) {
    const won = reduced.filter((p) => p.status === "won").length;
    note.append(
      `${reduced.length} ${reduced.length === 1 ? "parlay was" : "parlays were"} reduced after a void or tied leg (${won} won). They count in the record but not this chart. `
    );
    const link = el("button", "link-button", "Show them");
    link.type = "button";
    link.addEventListener("click", () => {
      state.reducedOnly = true;
      state.shown = PAGE_SIZE;
      render();
      $("history-title").scrollIntoView({ behavior: "smooth", block: "start" });
    });
    note.append(link);
  }
}

const MARKS = { win: "✓", loss: "✕", pending: "•", void: "⊘", push: "=" };
const LEG_NOTE = { void: "Void, dropped", push: "Tie, dropped" };

function slip(p, { open = false } = {}) {
  const info = sportInfo(p.sport);
  const wrap = el("article", `slip-wrap is-${p.status}`);
  const frame = el("div", "slip");
  const details = el("details", "slip-inner");
  details.open = open;

  const summary = el("summary", "slip-summary");
  const title = el("div", "slip-title", `${info.icon} ${info.name}`);
  title.append(el("span", "slip-date", formatDay(p.date)));

  const statusText = { won: "Won", lost: "Lost", pending: "Pending", void: "Void" }[p.status];
  const meta = el("div", "slip-meta");
  const pips = el("div", "pips");
  for (const leg of p.legs) pips.append(el("span", `pip ${leg.result}`));
  const hitsText = p.status === "pending" ? `${p.wins} of ${p.activeSize} in` : `${p.wins}/${p.activeSize} hit`;
  pips.append(el("span", "pips-text", hitsText));
  if (p.reduced) pips.append(el("span", "tag", `Reduced to ${p.activeSize}`));

  const payout = p.status === "lost" ? "$1 → $0" : `$1 → ${formatMoney(p.multiplier, false)}`;
  meta.append(pips, el("span", "", p.status === "pending" ? `Pays ${formatMoney(p.multiplier, false)}` : payout));

  summary.append(title, el("span", "status", statusText), meta);
  details.append(summary);

  const legs = el("ul", "legs");
  for (const leg of p.legs) {
    const row = el("li", `leg ${leg.result}`);
    row.append(
      el("span", "leg-mark", MARKS[leg.result] || "•"),
      el("span", "leg-pick", leg.team),
      el("span", "leg-odds", formatOdds(leg.price)),
      el("span", "leg-opp", LEG_NOTE[leg.result] || `vs ${leg.opponent}`),
      el("span", "leg-time", formatTime(leg.commence_time))
    );
    legs.append(row);
  }
  details.append(legs);

  frame.append(details);
  wrap.append(frame);
  return wrap;
}

function renderActive(parlays) {
  const box = $("active");
  box.textContent = "";
  const pending = parlays
    .filter((p) => p.status === "pending")
    .sort((a, b) => b.date.localeCompare(a.date) || a.sport.localeCompare(b.sport));

  if (!pending.length) {
    box.append(el("p", "empty", "No active parlays. The next slate posts around 5:30 AM Central."));
    return;
  }
  for (const p of pending) box.append(slip(p, { open: true }));
}

function renderHistory(parlays) {
  const box = $("history");
  box.textContent = "";
  let done = parlays
    .filter((p) => p.status !== "pending")
    .sort((a, b) => b.date.localeCompare(a.date) || a.sport.localeCompare(b.sport));

  const filter = $("reduced-filter");
  filter.setAttribute("aria-pressed", String(state.reducedOnly));
  if (state.reducedOnly) done = done.filter((p) => p.reduced);

  if (!done.length) {
    box.append(el("p", "empty", state.reducedOnly ? "No reduced parlays." : "No graded parlays yet."));
  }
  for (const p of done.slice(0, state.shown)) box.append(slip(p));

  const more = $("more");
  const remaining = done.length - state.shown;
  more.hidden = remaining <= 0;
  more.textContent = `Show ${Math.min(PAGE_SIZE, remaining)} more`;
}

function render() {
  const parlays = state.sport === "all" ? state.parlays : state.parlays.filter((p) => p.sport === state.sport);
  const label = state.sport === "all" ? "" : sportInfo(state.sport).name;
  const summary = summarize(parlays);

  renderTabs();
  renderStake(summary, label ? `${label}` : "daily");
  renderStrip(summary);
  renderDistribution(parlays);
  renderActive(parlays);
  renderHistory(parlays);
}

async function loadUpdated(parlays) {
  const target = $("updated");
  try {
    if (params.get("data")) throw new Error("local test data");
    const res = await fetch(COMMITS_URL);
    if (!res.ok) throw new Error(res.status);
    const [commit] = await res.json();
    const when = new Date(commit.commit.committer.date);
    target.textContent = `Updated ${when.toLocaleDateString(undefined, { month: "short", day: "numeric" })}, ${when.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}`;
  } catch {
    const latest = parlays.map((p) => p.date).sort().pop();
    target.textContent = latest ? `Latest slate ${formatDay(latest)}` : "";
  }
}

async function init() {
  $("more").addEventListener("click", () => {
    state.shown += PAGE_SIZE;
    render();
  });
  $("reduced-filter").addEventListener("click", () => {
    state.reducedOnly = !state.reducedOnly;
    state.shown = PAGE_SIZE;
    render();
  });

  try {
    const res = await fetch(dataSource, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const raw = await res.json();
    state.parlays = raw.map(analyze);
  } catch (err) {
    $("app").prepend(el("p", "error", `Couldn't load the parlay history (${err.message}). Refresh the page to try again.`));
    $("updated").textContent = "";
  }

  render();
  loadUpdated(state.parlays);
}

init();
