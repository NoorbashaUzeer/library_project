const form = document.getElementById("bookForm");
const msg = document.getElementById("msg");
let books = [];

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

async function load() {
  books = await (await fetch("/api/books")).json();
  document.getElementById("rows").innerHTML = books.map((b) => `
    <tr><td>${esc(b.title)}<br><span class="muted small">${esc(b.author)}</span></td>
    <td>${esc(b.category)}</td>
    <td><span class="badge ${b.in_stock ? "in" : "out"}">${esc(b.availability)}</span></td>
    <td><button class="link" data-edit="${b.id}">Edit</button><button class="link del" data-del="${b.id}">Delete</button></td></tr>`).join("");
  const cats = [...new Set(books.map((b) => b.category))];
  document.getElementById("cats").innerHTML = cats.map((c) => `<option value="${esc(c)}">`).join("");
}

function resetForm() {
  form.reset();
  form.id.value = "";
  document.getElementById("formTitle").textContent = "Add a new book";
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  const id = data.id;
  delete data.id;
  const res = await fetch(id ? `/api/books/${id}` : "/api/books", {
    method: id ? "PUT" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const out = await res.json();
  if (!res.ok) { msg.textContent = out.error || "Something went wrong"; msg.className = "small error"; return; }
  msg.textContent = id ? "Book updated." : "Book added.";
  msg.className = "small muted";
  resetForm();
  load();
});

document.getElementById("resetBtn").addEventListener("click", () => { resetForm(); msg.textContent = ""; });

document.getElementById("rows").addEventListener("click", async (e) => {
  const editId = e.target.dataset.edit, delId = e.target.dataset.del;
  if (editId) {
    const b = books.find((x) => x.id == editId);
    for (const k of ["id", "title", "author", "category", "year", "pages", "description", "total_copies", "available_copies", "ebook_url"]) {
      form[k].value = b[k] ?? "";
    }
    document.getElementById("formTitle").textContent = "Edit book";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  if (delId && confirm("Delete this book?")) {
    await fetch(`/api/books/${delId}`, { method: "DELETE" });
    load();
  }
});

load();
