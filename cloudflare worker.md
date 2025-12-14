Google OAuth setup (service account)
Use a Google Cloud service account and share your target calendar with it.
Steps
1) In Google Cloud Console
Create project → enable “Google Calendar API”
Create service account → grant no special roles
Create JSON key
2) Share your Google Calendar with the service account’s email
In Google Calendar → Settings → Select calendar → Share with specific people
Add the service account email with “Make changes to events”
3) Secrets for the Worker
GOOGLE_SA_EMAIL = the service account email
GOOGLE_SA_PRIVATE_KEY = the private key string from the JSON (beginning with -----BEGIN PRIVATE KEY-----)
GOOGLE_CALENDAR_ID = your calendar ID (often your Gmail address)
NOTION_TOKEN and DATA_SOURCE_ID are already used
Add secrets
wrangler secret put GOOGLE_SA_EMAIL
wrangler secret put GOOGLE_SA_PRIVATE_KEY
wrangler secret put GOOGLE_CALENDAR_ID
Worker: extend with Google Calendar sync
Drop-in replacement for src/worker.js that adds create/update to GCal and writes back GCal event ID and link. It uses the exact times and Slot logic we set, and updates on both /ingest-task and /notion-webhook.
export default {
async fetch(req, env) {
const url = new URL(req.url);
if (req.method === "POST" && url.pathname === "/ingest-task") {
const body = await req.json();
return await ingestTask(body, env);
}
if (req.method === "POST" && url.pathname === "/notion-webhook") {
const { page_id } = await req.json();
await autoslotExistingPage(page_id, env, { syncCalendar: true });
return new Response("OK");
}
return new Response("OK");
},
};
const NOTION_VERSION = "2022-06-28";
const SLOT_ORDER = [
["Self-care AM", 1, "06:30", "07:15"],
["Executive report & agenda", 2, "07:15", "07:45"],
["Deep work 1", 3, "08:00", "10:00"],
["Break 1", 4, "10:00", "10:15"],
["Deep work 2", 5, "10:15", "12:15"],
["Break 2", 6, "12:15", "12:30"],
["Lunch", 7, "12:30", "13:15"],
["Deep work 3", 8, "13:30", "15:30"],
["Break 3", 9, "15:30", "15:45"],
["Deep work 4", 10, "15:45", "17:45"],
["Break 4", 11, "17:45", "18:00"],
["Self-care PM", 12, "21:30", "22:00"],
["Wind-down", 13, "22:00", "22:15"],
];
function notion(path, env, init = {}) {
return fetch(https://api.notion.com/v1${path}, {
...init,
headers: {
Authorization: Bearer ${env.NOTION_TOKEN},
"Notion-Version": NOTION_VERSION,
"Content-Type": "application/json",
...(init.headers || {}),
},
});
}
function dateAt(dateOnly, hhmm) {
return ${dateOnly}T${hhmm}:00;
}
async function queryByDate(dateOnly, env) {
const body = {
filter: { property: "Due date", date: { equals: dateOnly } },
page_size: 100,
sorts: [{ property: "Order", direction: "ascending" }],
};
const res = await notion(/databases/${env.DATA_SOURCE_ID}/query, env, {
method: "POST",
body: JSON.stringify(body),
});
return res.json();
}
function nextFreeSlot(results, excludeId) {
const used = new Set(
results
.filter(r => r.id !== excludeId)
.map(r => r.properties?.Order?.number)
.filter(n => typeof n === "number")
);
for (const entry of SLOT_ORDER) {
if (!used.has(entry[1])) return entry;
}
return SLOT_ORDER[SLOT_ORDER.length - 1];
}
function normaliseTitle(s) {
return (s || "").replace(/^Focus blocks[:—-]s/i, "").trim() || s;
}
// ----- Google Calendar (Service Account JWT) -----
async function googleAccessToken(env) {
// JWT for OAuth 2.0 Service Account
const header = btoa(JSON.stringify({ alg: "RS256", typ: "JWT" }));
const now = Math.floor(Date.now() / 1000);
const claimSet = {
iss: env.GOOGLE_SA_EMAIL,
scope: "https://www.googleapis.com/auth/calendar",
aud: "https://oauth2.googleapis.com/token",
exp: now + 3600,
iat: now,
};
const payload = btoa(JSON.stringify(claimSet));
const toSign = new TextEncoder().encode(${header}.${payload});
// Import PKCS#8 private key
const pem = env.GOOGLE_SA_PRIVATE_KEY.trim();
const pkcs8 = pem
.replace("-----BEGIN PRIVATE KEY-----", "")
.replace("-----END PRIVATE KEY-----", "")
.replace(/s+/g, "");
const keyData = Uint8Array.from(atob(pkcs8), c => c.charCodeAt(0));
const cryptoKey = await crypto.subtle.importKey(
"pkcs8",
keyData.buffer,
{ name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
false,
["sign"]
);
const sig = await crypto.subtle.sign("RSASSA-PKCS1-v1_5", cryptoKey, toSign);
const signature = btoa(String.fromCharCode(...new Uint8Array(sig)));
const assertion = ${header}.${payload}.${signature};
const tokenRes = await fetch("https://oauth2.googleapis.com/token", {
method: "POST",
headers: { "Content-Type": "application/x-www-form-urlencoded" },
body: new URLSearchParams({
grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
assertion,
}),
});
const token = await tokenRes.json();
if (!token.access_token) throw new Error("Google token error: " + JSON.stringify(token));
return token.access_token;
}
async function upsertGCalEvent(env, page, startISO, endISO) {
const access = await googleAccessToken(env);
const calId = encodeURIComponent(env.GOOGLE_CALENDAR_ID);
const props = page.properties || {};
const title = (props.Task?.title ?? []).map(t => t.plain_text).join("") || "Untitled";
const titleClean = normaliseTitle(title);
const eventId = props["GCal event ID"]?.rich_text?.[0]?.plain_text || props["GCal event ID"]?.plain_text || null;
const eventBody = {
summary: titleClean,
start: { dateTime: startISO, timeZone: "Europe/London" },
end: { dateTime: endISO, timeZone: "Europe/London" },
description: Notion task: ${titleClean},
};
let gEvent;
if (eventId) {
const res = await fetch(https://www.googleapis.com/calendar/v3/calendars/${calId}/events/${encodeURIComponent(eventId)}, {
method: "PATCH",
headers: { Authorization: Bearer ${access}, "Content-Type": "application/json" },
body: JSON.stringify(eventBody),
});
gEvent = await res.json();
} else {
const res = await fetch(https://www.googleapis.com/calendar/v3/calendars/${calId}/events, {
method: "POST",
headers: { Authorization: Bearer ${access}, "Content-Type": "application/json" },
body: JSON.stringify(eventBody),
});
gEvent = await res.json();
}
if (!gEvent || !gEvent.id) return;
// Write back to Notion
await notion(/pages/${page.id}, env, {
method: "PATCH",
body: JSON.stringify({
properties: {
"GCal event ID": { rich_text: [{ type: "text", text: { content: gEvent.id } }] },
"GCal link": { url: gEvent.htmlLink || null },
},
}),
});
}
async function ensureExecReport(dateOnly, env, results) {
const hasExec = results.some(r => r.properties?.Slot?.select?.name === "Executive report & agenda");
if (hasExec) return;
const start = dateAt(dateOnly, "07:15");
const end = dateAt(dateOnly, "07:45");
await notion(/pages, env, {
method: "POST",
body: JSON.stringify({
parent: { database_id: env.DATA_SOURCE_ID },
properties: {
Task: { title: [{ type: "text", text: { content: "Executive report & agenda" } }] },
"Due date": { date: { start, end } },
Slot: { select: { name: "Executive report & agenda" } },
Order: { number: 2 },
},
}),
});
}
async function applySlotAndTimes(pageId, dateOnly, slotEntry, env, newTitle, syncCalendar, pageObj) {
const [slotName, order, s, e] = slotEntry;
const startISO = dateAt(dateOnly, s);
const endISO = dateAt(dateOnly, e);
const props = {
Slot: { select: { name: slotName } },
Order: { number: order },
"Due date": { date: { start: startISO, end: endISO } },
};
if (newTitle) props.Task = { title: [{ type: "text", text: { content: newTitle } }] };
await notion(/pages/${pageId}, env, { method: "PATCH", body: JSON.stringify({ properties: props }) });
if (syncCalendar) {
// Fetch page details if not provided
const page = pageObj || (await (await notion(/pages/${pageId}, env)).json());
await upsertGCalEvent(env, page, startISO, endISO);
}
}
async function autoslotExistingPage(pageId, env, { syncCalendar } = {}) {
const page = await (await notion(/pages/${pageId}, env)).json();
const dueStart = page.properties?.["Due date"]?.date?.start;
if (!dueStart) return;
const dateOnly = dueStart.slice(0, 10);
const { results } = await queryByDate(dateOnly, env);
await ensureExecReport(dateOnly, env, results);
const titleRich = page.properties?.Task?.title ?? [];
const titleText = titleRich.map(t => t.plain_text).join("");
const newTitle = normaliseTitle(titleText);
const slotEntry = nextFreeSlot(results, pageId);
await applySlotAndTimes(pageId, dateOnly, slotEntry, env, newTitle, !!syncCalendar, page);
}
async function ingestTask(body, env) {
const title = body.title?.toString().trim();
const dateInput = body.date?.toString().trim();
const priority = body.priority?.toString().trim() || "Medium";
if (!title || !dateInput) return new Response("Missing title or date", { status: 400 });
const dateOnly = dateInput.slice(0, 10);
// Create minimal page
const created = await (
await notion(/pages, env, {
method: "POST",
body: JSON.stringify({
parent: { database_id: env.DATA_SOURCE_ID },
properties: {
Task: { title: [{ type: "text", text: { content: title } }] },
"Due date": { date: { start: dateOnly } },
Priority: { select: { name: priority } },
},
}),
})
).json();
// Slot + GCal
await autoslotExistingPage(created.id, env, { syncCalendar: true });
return new Response("OK");
}
wrangler.toml additions
[vars]
DATA_SOURCE_ID = "✅Task tracker"
Add nothing here for secrets; use wrangler secret put for the following:
NOTION_TOKEN, GOOGLE_SA_EMAIL, GOOGLE_SA_PRIVATE_KEY, GOOGLE_CALENDAR_ID
Deployment
wrangler secret put NOTION_TOKEN
wrangler secret put GOOGLE_SA_EMAIL
wrangler secret put GOOGLE_SA_PRIVATE_KEY
wrangler secret put GOOGLE_CALENDAR_ID
wrangler deploy
Notion Calendar + Worker together
Notion Calendar gives you a first‑class calendar UI with two‑way edits
The Worker guarantees any task arriving from GitHub or Drive gets auto‑slotted, timeboxed, colour‑coded, and mirrored to Google
Want me to add a Notion Automation now that POSTs to /notion-webhook when a task is created or Due date changes, so Google events stay in sync when you edit inside Notion too?
yes please
Brilliant — here’s the exact Notion Automation to keep Google Calendar in sync via your Worker.
Notion Automation
Trigger
When: Page is created or updated
Where: Task tracker
Filter: Any page where Due date is not empty
Action
Webhook
URL: https://YOUR-WORKER.workers.dev/notion-webhook
Method: POST
Headers: Content-Type: application/json
Body:
{
"page_id": "Page ID"
}