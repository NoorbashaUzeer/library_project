const COLORS = ["#9b2c1f", "#2f4f6b", "#3d6b4f", "#7a5a1e", "#4b3a6b", "#1f5c5c", "#6b2f4f"];
let books = [];
let activeCategory = "All";

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const colorFor = (b) => COLORS[b.id % COLORS.length];
const badge = (b) => `<span class="badge ${b.in_stock ? "in" : "out"}">${esc(b.availability)}</span>`;
const cover = (b) => `<div class="cover" style="background:${colorFor(b)}">
  <div class="t">${esc(b.title)}</div><div class="a">${esc(b.author)}</div></div>`;

async function load() {
  const res = await fetch("/api/books");
  books = await res.json();
  renderTabs();
  render();
}

function renderTabs() {
  const cats = ["All", ...new Set(books.map((b) => b.category))];
  $("tabs").innerHTML = cats.map((c) =>
    `<button class="tab ${c === activeCategory ? "active" : ""}" data-cat="${esc(c)}">${esc(c)}</button>`).join("");
}

function render() {
  const q = $("search").value.trim().toLowerCase();
  const list = books.filter((b) =>
    (activeCategory === "All" || b.category === activeCategory) &&
    (!q || b.title.toLowerCase().includes(q) || b.author.toLowerCase().includes(q)));
  $("count").textContent = `${list.length} book${list.length === 1 ? "" : "s"}`;
  $("grid").innerHTML = list.length ? list.map((b) => `
    <button class="book" data-id="${b.id}">
      ${cover(b)}
      <h3>${esc(b.title)}</h3><p>${esc(b.author)}</p>${badge(b)}
    </button>`).join("") : `<p class="muted">No books match your search.</p>`;
}

async function openBook(id) {
  const res = await fetch(`/api/books/${id}`);
  if (!res.ok) return;
  const b = await res.json();
  const year = b.year == null ? "—" : b.year < 0 ? `${-b.year} BC` : b.year;
  $("detail").innerHTML = `<div class="detail">
    ${cover(b)}
    <div>
      <p class="muted small">${esc(b.category)}</p>
      <h2>${esc(b.title)}</h2>
      <p>by ${esc(b.author)}</p>
      ${badge(b)}
      <dl class="meta">
        <dt>Year</dt><dd>${esc(year)}</dd>
        <dt>Pages</dt><dd>${esc(b.pages ?? "—")}</dd>
        <dt>Copies</dt><dd>${b.available_copies} available / ${b.total_copies} total</dd>
      </dl>
      <p>${esc(b.description || "No description available.")}</p>
      ${b.ebook_url
        ? `<a class="btn primary" href="${esc(b.ebook_url)}" target="_blank" rel="noopener">Read E-book</a>`
        : `<button class="btn" disabled>No e-book available</button>`}
      <p class="muted small">Visit the library desk to use physical copies — no online borrowing.</p>
    </div></div>`;
  $("modal").classList.remove("hidden");
}

$("search").addEventListener("input", render);
$("tabs").addEventListener("click", (e) => {
  const t = e.target.closest(".tab");
  if (!t) return;
  activeCategory = t.dataset.cat;
  renderTabs();
  render();
});
$("grid").addEventListener("click", (e) => {
  const card = e.target.closest(".book");
  if (card) openBook(card.dataset.id);
});
$("closeModal").addEventListener("click", () => $("modal").classList.add("hidden"));
$("modal").addEventListener("click", (e) => { if (e.target.id === "modal") $("modal").classList.add("hidden"); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") $("modal").classList.add("hidden"); });

load();
