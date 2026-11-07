// Leave Manager UI. Data reaches the DOM only through textContent / new Option — never innerHTML
// (docs/conventions.md, Known traps).
const $ = (id) => document.getElementById(id);

async function api(method, path, body) {
  const response = await fetch(`/api${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) throw response;
  return response.status === 204 ? null : response.json();
}

function show(viewId) {
  for (const id of ["login", "my-requests"]) $(id).hidden = id !== viewId;
  $(viewId).querySelector("h1").focus();
}

async function showLogin() {
  const people = await api("GET", "/people");
  $("person").replaceChildren(
    new Option("Choose your name", ""),
    ...people.map((p) => new Option(p.full_name, p.id)),
  );
  $("login-error").textContent = "";
  show("login");
}

async function loadRequests() {
  const status = $("requests-status");
  $("retry").hidden = true;
  status.textContent = "Loading your requests…";
  try {
    const { requests } = await api("GET", "/my/requests");
    // shortcut: rows are not rendered — no request can exist yet; the spec that lets Employees
    // create requests adds the list (spec 0001, success state out of scope).
    status.textContent = requests.length ? "" : "You have no leave requests yet.";
  } catch (error) {
    if (error.status === 401) return showLogin();
    status.textContent = "Could not load your requests.";
    $("retry").hidden = false;
  }
}

async function start() {
  let person;
  try {
    person = await api("GET", "/me");
  } catch {
    return showLogin();
  }
  $("signed-in").textContent = `Signed in as ${person.full_name}`;
  show("my-requests");
  await loadRequests();
}

$("login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const personId = $("person").value;
  if (!personId) {
    $("login-error").textContent = "Choose who you are.";
    return;
  }
  await api("POST", "/session", { person_id: personId }).catch(() => {});
  await start();
});

$("logout").addEventListener("click", async () => {
  await api("DELETE", "/session");
  await showLogin();
});

$("retry").addEventListener("click", loadRequests);

start();
