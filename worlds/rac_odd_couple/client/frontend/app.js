// --- State ---
let suppressedEvents = new Set();
let currentMovie = null;
let player = null;
let pollHandle = null;
let hasReportedPlayed = false;

// The Archipelago client only ever installs one file, under this fixed name
// (see client/backend.py's PATCHED_SWF_NAME) - there is nothing else to pick
// from, so the movie dropdown that used to live here has been removed.
const PATCHED_MOVIE = "ap_patched_odd_couple.swf";

// Maps backend scene/event names to the item name the player receives to
// unlock them, for display in the items panel.
const SCENE_DISPLAY_NAMES = {
  stereo: "Stereo",
  taxiDriver: "Taxi Driver",
  gimp: "Gimp",
  phonecall1: "Phonecall",
  scissors: "Scissors",
  tv: "TV",
};

const playerWrapper = document.getElementById("player-wrapper");
const clickBlocker = document.getElementById("click-blocker");
const connStatus = document.getElementById("conn-status");
const itemsToggle = document.getElementById("items-toggle");
const itemsPanel = document.getElementById("items-panel");
const itemsList = document.getElementById("items-list");

// Reserved suppressed-event name that means "block all mouse clicks on the
// player itself". Needed because most SWFs handle button clicks (AVM1
// buttons etc.) entirely inside Flash/Ruffle's own runtime and never call
// out to ExternalInterface for permission, so the checkEvent() bridge below
// can't intercept them. This overlay physically sits on top of the player
// and swallows the click before it ever reaches the canvas.
const CLICK_BLOCK_EVENT = "Avm1Button";

function updateClickBlocker() {
  clickBlocker.classList.toggle("active", suppressedEvents.has(CLICK_BLOCK_EVENT));
}

// The items panel shows the unsuppressed (i.e. already-unlocked) scenes,
// translated to their item display names.
function renderItems() {
  const unlocked = Object.keys(SCENE_DISPLAY_NAMES).filter((scene) => !suppressedEvents.has(scene));
  itemsList.innerHTML = "";
  if (!unlocked.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "No items received yet.";
    itemsList.appendChild(li);
    return;
  }
  for (const scene of unlocked) {
    const li = document.createElement("li");
    li.textContent = SCENE_DISPLAY_NAMES[scene];
    itemsList.appendChild(li);
  }
}

itemsToggle.addEventListener("click", () => {
  itemsPanel.classList.toggle("hidden");
});

// --- WebSocket to the embedded server ---
// Served on a separate port from the page itself (see client/backend.py's
// WS_PORT) since the embedded server is a plain stdlib HTTP server plus a
// `websockets` server, not a single combined HTTP/WS listener.
const WS_PORT = 8001;
let ws;
function connectWs() {
  ws = new WebSocket(`ws://${location.hostname}:${WS_PORT}/`);

  ws.onopen = () => {
    connStatus.textContent = "connected";
    connStatus.className = "status ok";
  };
  ws.onclose = () => {
    connStatus.textContent = "disconnected, retrying...";
    connStatus.className = "status bad";
    setTimeout(connectWs, 1500);
  };
  ws.onerror = () => ws.close();

  ws.onmessage = (evt) => {
    const msg = JSON.parse(evt.data);
    switch (msg.type) {
      case "state":
        suppressedEvents = new Set(msg.suppressed);
        renderItems();
        updateClickBlocker();
        break;
      case "suppress":
        msg.events.forEach((e) => suppressedEvents.add(e));
        renderItems();
        updateClickBlocker();
        break;
      case "enable":
        msg.events.forEach((e) => suppressedEvents.delete(e));
        renderItems();
        updateClickBlocker();
        break;
      case "set_suppressed":
        suppressedEvents = new Set(msg.events);
        renderItems();
        updateClickBlocker();
        break;
      case "scene_initiated":
        console.log(`Scene initiated: ${msg.scene}`);
        break;
      case "movie_played_ack":
        console.log(`Server acknowledged movie played: ${msg.movie}`);
        break;
    }
  };
}

function sendWs(payload) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(payload));
  }
}

// --- ExternalInterface bridge: the SWF calls these by name via
// ExternalInterface.call("checkEvent", "someEventName"). It gets back
// true if the event is allowed to proceed, false if it should be a no-op.
// The SWF is expected to gate its own click handling on the return value,
// e.g.: if (ExternalInterface.call("checkEvent", "btnA")) { doStuff(); }
window.checkEvent = function (eventName) {
  const allowed = !suppressedEvents.has(eventName);
  sendWs({ type: "event_fired", event: eventName, movie: currentMovie });
  return allowed;
};

// Optional explicit signal a SWF can call when it considers itself finished:
// ExternalInterface.call("reportMovieEnded");
window.reportMovieEnded = function () {
  reportPlayed();
};

function reportPlayed() {
  if (hasReportedPlayed || !currentMovie) return;
  hasReportedPlayed = true;
  sendWs({ type: "movie_played", movie: currentMovie });
}

// --- Fallback "played" detection: poll Ruffle's Flash-compatible scripting
// properties. A movie is considered played once it has started (currentFrame
// advanced past 0) and then stops playing on its own (isPlaying becomes
// false), which is the standard pattern for a SWF that calls stop() on its
// last frame.
function startPlayedPolling() {
  let everPlayed = false;
  stopPlayedPolling();
  pollHandle = setInterval(() => {
    if (!player) return;
    try {
      const playing = player.isPlaying;
      const frame = player.currentFrame;
      if (playing && frame > 0) everPlayed = true;
      if (everPlayed && !playing) {
        reportPlayed();
        stopPlayedPolling();
      }
    } catch (e) {
      // player not ready yet
    }
  }, 250);
}

function stopPlayedPolling() {
  if (pollHandle) clearInterval(pollHandle);
  pollHandle = null;
}

// --- Movie loading: there is exactly one movie - the one the Archipelago
// client patched and installed - so this loads unconditionally on startup.
function loadMovie(filename) {
  currentMovie = filename;
  hasReportedPlayed = false;
  stopPlayedPolling();
  playerWrapper.innerHTML = "";

  const ruffle = window.RufflePlayer.newest();
  player = ruffle.createPlayer();
  playerWrapper.appendChild(player);
  player.load({ url: `/game/${filename}?v=${Date.now()}`, allowScriptAccess: "always" });
  player.traceObserver = (msg) => console.log("[SWF trace]", msg);

  startPlayedPolling();
}

connectWs();
loadMovie(PATCHED_MOVIE);
