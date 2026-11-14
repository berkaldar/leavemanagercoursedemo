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
  // No reload between users: drop everything of the previous one (Known traps, 0002 F-1).
  $("requests-table").tBodies[0].replaceChildren();
  $("requests-table").hidden = true;
  $("request-form").reset();
  for (const id of ["request-message", "requests-status", "signed-in"]) $(id).textContent = "";
  const people = await api("GET", "/people");
  $("person").replaceChildren(
    new Option("Choose your name", ""),
    ...people.map((p) => new Option(p.full_name, p.id)),
  );
  $("login-error").textContent = "";
  show("login");
}

function requestRow(r) {
  const row = document.createElement("tr");
  for (const value of [r.leave_type, r.start_date, r.end_date, r.working_days, r.status]) {
    row.insertCell().textContent = value;
  }
  return row;
}

async function loadRequests() {
  const status = $("requests-status");
  $("retry").hidden = true;
  status.textContent = "Loading your requests…";
  try {
    const { requests } = await api("GET", "/my/requests");
    status.textContent = requests.length ? "" : "You have no leave requests yet.";
    $("requests-table").tBodies[0].replaceChildren(...requests.map(requestRow));
    $("requests-table").hidden = !requests.length;
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

const MISSING_INPUT = "Choose a leave type, a start date and an end date.";

// The refusal sentence for a failed submit: the server's own for a rule (409), else ours.
async function refusal(error) {
  if (error.status === 409) return (await error.json()).message;
  if (error.status === 422) return MISSING_INPUT;
  return "Could not submit your request. Try again.";
}

$("request-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const message = $("request-message");
  const body = {
    leave_type: $("leave-type").value,
    start_date: $("start-date").value,
    end_date: $("end-date").value,
  };
  if (!body.leave_type || !body.start_date || !body.end_date) {
    message.textContent = MISSING_INPUT;
    return;
  }
  const submit = form.querySelector("button[type=submit]");
  submit.disabled = true;
  message.textContent = "Submitting…";
  try {
    await api("POST", "/my/requests", body);
    message.textContent = "Request submitted.";
    form.reset();
    await loadRequests();
  } catch (error) {
    if (error.status === 401) return showLogin();
    message.textContent = await refusal(error);
  } finally {
    submit.disabled = false;
  }
});

start();
