/**
 * Assam Skill University Central Library
 * Smart Book Search, Shelf Locator & Real-Time Seat Occupancy System
 * Frontend Application Engine
 */

// Application State
const AppState = {
  currentUser: {
    id: "ASU/2026/AI-104",
    name: "Ankur Barman",
    dept: "School of Computing & AI"
  },
  activeFloor: 1,
  activeCategory: "",
  searchKeyword: "",
  soundEnabled: true,
  books: [],
  seats: [],
  borrowings: [],
  notifications: [],
  stats: {},
  selectedBook: null,
  selectedSeat: null,
  pollTimer: null
};

// Web Audio API Sound Generator for Real-Time Chimes
class SoundFX {
  static init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) this.ctx = new AudioCtx();
    }
  }

  static playChime(type = "success") {
    if (!AppState.soundEnabled) return;
    try {
      this.init();
      if (!this.ctx) return;
      if (this.ctx.state === "suspended") this.ctx.resume();

      const now = this.ctx.currentTime;
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.connect(gain);
      gain.connect(this.ctx.destination);

      if (type === "success") {
        // High harmonic ascending pleasant chime
        osc.frequency.setValueAtTime(523.25, now); // C5
        osc.frequency.setValueAtTime(659.25, now + 0.1); // E5
        osc.frequency.setValueAtTime(783.99, now + 0.2); // G5
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.5);
        osc.start(now);
        osc.stop(now + 0.5);
      } else if (type === "alert") {
        // Two-tone warning beep
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.setValueAtTime(330, now + 0.15);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
        osc.start(now);
        osc.stop(now + 0.4);
      }
    } catch (e) {
      console.warn("Audio playback not allowed without user gesture:", e);
    }
  }
}

// ============================================================================
// Initialization & Event Listeners
// ============================================================================
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupUserPersona();
  setupSearch();
  setupFloorSwitch();
  setupSoundToggle();
  setupAdminForms();
  startClock();

  // Initial Data Fetch
  refreshAllData();

  // Auto-refresh every 20 seconds for real-time seat & loan updates
  AppState.pollTimer = setInterval(refreshAllData, 20000);
});

function startClock() {
  const clockEl = document.getElementById("liveClock");
  const update = () => {
    const d = new Date();
    const opts = { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" };
    if (clockEl) clockEl.textContent = d.toLocaleDateString("en-IN", opts);
  };
  update();
  setInterval(update, 1000);
}

function setupSoundToggle() {
  const btn = document.getElementById("soundToggleBtn");
  const icon = document.getElementById("soundIcon");
  btn.addEventListener("click", () => {
    AppState.soundEnabled = !AppState.soundEnabled;
    icon.textContent = AppState.soundEnabled ? "🔊" : "🔇";
    if (AppState.soundEnabled) SoundFX.playChime("success");
  });
}

function setupUserPersona() {
  const select = document.getElementById("userPersonaSelect");
  select.addEventListener("change", (e) => {
    const opt = select.options[select.selectedIndex];
    AppState.currentUser = {
      id: opt.value,
      name: opt.getAttribute("data-name"),
      dept: opt.getAttribute("data-dept")
    };

    // Update Issue form defaults if present
    const issueStudId = document.getElementById("issueStudentId");
    const issueStudName = document.getElementById("issueStudentName");
    if (issueStudId) issueStudId.value = opt.value;
    if (issueStudName) issueStudName.value = opt.getAttribute("data-name");

    SoundFX.playChime("success");
    refreshAllData();
  });
}

function setupTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      buttons.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      const pane = document.getElementById(targetId);
      if (pane) pane.classList.add("active");

      if (targetId === "tab-seats") {
        renderSeatMap();
      }
    });
  });

  const notifBtn = document.getElementById("notifBtn");
  notifBtn.addEventListener("click", () => {
    // Switch to Alerts tab
    const alertTab = document.querySelector('[data-tab="tab-alerts"]');
    if (alertTab) alertTab.click();
  });
}

function setupSearch() {
  const input = document.getElementById("bookSearchInput");
  const floorSelect = document.getElementById("bookFilterFloor");
  const btn = document.getElementById("btnSearchBooks");

  const executeSearch = () => {
    AppState.searchKeyword = input.value.trim();
    fetchBooks();
  };

  btn.addEventListener("click", executeSearch);
  input.addEventListener("keyup", (e) => {
    if (e.key === "Enter") executeSearch();
  });
  floorSelect.addEventListener("change", executeSearch);
}

function setupFloorSwitch() {
  const f1 = document.getElementById("btnFloor1");
  const f2 = document.getElementById("btnFloor2");
  const refresh = document.getElementById("btnRefreshSeats");

  f1.addEventListener("click", () => {
    f1.classList.add("active");
    f2.classList.remove("active");
    AppState.activeFloor = 1;
    renderSeatMap();
  });

  f2.addEventListener("click", () => {
    f2.classList.add("active");
    f1.classList.remove("active");
    AppState.activeFloor = 2;
    renderSeatMap();
  });

  refresh.addEventListener("click", () => {
    fetchSeats();
    SoundFX.playChime("success");
  });
}

// ============================================================================
// Data Fetching & Sync
// ============================================================================
async function refreshAllData() {
  await Promise.all([
    fetchStats(),
    fetchBooks(),
    fetchSeats(),
    fetchBorrowings(),
    fetchNotifications(),
    fetchAnnouncements()
  ]);
}

async function fetchStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    if (data.success) {
      AppState.stats = data;
      document.getElementById("statAvailSeats").textContent = `${data.available_seats} / ${data.total_seats}`;
      document.getElementById("statTotalBooks").textContent = `${data.total_inventory} (${data.total_titles} Titles)`;
      document.getElementById("statOverdueFines").textContent = `₹${data.pending_fines.toFixed(2)}`;
    }
  } catch (err) {
    console.error("Failed to fetch stats:", err);
  }
}

async function fetchBooks() {
  try {
    const floor = document.getElementById("bookFilterFloor")?.value || "";
    let url = `/api/books?q=${encodeURIComponent(AppState.searchKeyword)}`;
    if (AppState.activeCategory) url += `&category=${encodeURIComponent(AppState.activeCategory)}`;
    if (floor) url += `&floor=${floor}`;

    const res = await fetch(url);
    const data = await res.json();
    if (data.success) {
      AppState.books = data.books;
      renderCategoryChips(data.categories);
      renderBooksGrid(data.books);
      populateIssueDropdown(data.books);
    }
  } catch (err) {
    console.error("Failed to fetch books:", err);
  }
}

async function fetchSeats() {
  try {
    const res = await fetch(`/api/seats?floor=${AppState.activeFloor}`);
    const data = await res.json();
    if (data.success) {
      AppState.seats = data.seats;
      renderSeatMap();
      renderZoneCards(data.seats);
    }
  } catch (err) {
    console.error("Failed to fetch seats:", err);
  }
}

async function fetchBorrowings() {
  try {
    const res = await fetch(`/api/borrowings?student_id=${encodeURIComponent(AppState.currentUser.id)}`);
    const data = await res.json();
    if (data.success) {
      AppState.borrowings = data.borrowings;
      const activeCount = data.borrowings.filter(b => b.status !== "RETURNED").length;
      document.getElementById("statMyLoans").textContent = `${activeCount} Book(s)`;
      renderBorrowings(data.borrowings);
    }
  } catch (err) {
    console.error("Failed to fetch borrowings:", err);
  }
}

async function fetchNotifications() {
  try {
    const res = await fetch(`/api/notifications?student_id=${encodeURIComponent(AppState.currentUser.id)}`);
    const data = await res.json();
    if (data.success) {
      AppState.notifications = data.notifications;
      const unreadCount = data.notifications.filter(n => !n.read).length;
      const badge = document.getElementById("unreadBadge");
      if (badge) {
        badge.textContent = unreadCount;
        badge.style.display = unreadCount > 0 ? "inline-block" : "none";
      }
      renderAlertsChannel(data.notifications);
    }
  } catch (err) {
    console.error("Failed to fetch notifications:", err);
  }
}

async function fetchAnnouncements() {
  try {
    const res = await fetch("/api/announcements");
    const data = await res.json();
    if (data.success && data.announcements.length > 0) {
      const headline = document.getElementById("announcementHeadline");
      if (headline) headline.textContent = data.announcements[0].title;
    }
  } catch (err) {
    console.error("Failed to fetch announcements:", err);
  }
}

// ============================================================================
// Renderers: Books & Physical Shelf Navigation
// ============================================================================
function renderCategoryChips(categories) {
  const container = document.getElementById("categoryChips");
  if (!container || !categories) return;

  let html = `<div class="filter-chip ${AppState.activeCategory === "" ? "active" : ""}" data-cat="">All Subjects</div>`;
  categories.forEach(cat => {
    html += `<div class="filter-chip ${AppState.activeCategory === cat ? "active" : ""}" data-cat="${cat}">${cat}</div>`;
  });
  container.innerHTML = html;

  container.querySelectorAll(".filter-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      AppState.activeCategory = chip.getAttribute("data-cat");
      fetchBooks();
    });
  });
}

function renderBooksGrid(books) {
  const grid = document.getElementById("booksGrid");
  if (!grid) return;

  if (books.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 48px; background: #fff; border-radius: 12px; border: 1px dashed var(--border);">
        <div style="font-size: 2.5rem; margin-bottom: 8px;">🔍</div>
        <h3 style="font-weight: 700; color: var(--text-main);">No books found matching your query</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem;">Try searching for "Robotics", "AI", "Machine Learning", "Solanki", or "Python".</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = books.map(book => {
    const isAvail = book.available_copies > 0;
    const availClass = isAvail ? (book.available_copies <= 2 ? "low" : "available") : "none";
    const availText = isAvail ? `${book.available_copies} of ${book.total_copies} Available` : "Currently All Loaned Out";
    const floorLabel = book.floor === 0 ? "Ground Floor" : `Floor ${book.floor}`;

    return `
      <div class="book-card" data-id="${book.id}">
        <div class="book-card-header">
          <div class="book-spine-mock" style="background: ${book.cover_color || '#0f766e'};">
            <span class="spine-star">★ ${book.rating}</span>
            <span class="spine-call">${book.call_no}</span>
          </div>
          <div class="book-meta">
            <div class="book-dept-tag">${book.department}</div>
            <h3 class="book-title">${book.title}</h3>
            <div class="book-author">By ${book.author} • ${book.edition || 'Std Edition'}</div>
          </div>
        </div>

        <div class="book-card-body">
          <div class="shelf-location-badge">
            <div class="loc-text">
              <span>📍</span> ${floorLabel} • ${book.aisle} • ${book.rack}
            </div>
            <div class="tier-text">Tier ${book.shelf_tier}</div>
          </div>

          <div class="book-summary-snippet">${book.summary}</div>

          <div class="book-status-row">
            <span class="avail-pill ${availClass}">
              ● ${availText}
            </span>
            <span style="font-size: 0.75rem; color: var(--text-muted); font-family: monospace;">ISBN: ${book.isbn.substring(0, 13)}</span>
          </div>
        </div>

        <div class="book-card-footer">
          <button class="btn-locate" onclick="openShelfLocatorModal(${book.id})">
            <span>🗺️</span> Locate on Shelf
          </button>
          <button class="btn-reserve ${!isAvail ? 'waitlist' : ''}" onclick="quickReserveBook(${book.id})">
            ${isAvail ? 'Reserve Copy' : 'Join Waitlist'}
          </button>
        </div>
      </div>
    `;
  }).join("");
}

// Open Interactive Shelf Locator Modal
async function openShelfLocatorModal(bookId) {
  try {
    const res = await fetch(`/api/books/${bookId}`);
    const data = await res.json();
    if (!data.success) return;

    const book = data.book;
    AppState.selectedBook = book;

    document.getElementById("modalBookTitle").textContent = book.title;
    document.getElementById("modalBookAuthor").textContent = `By ${book.author} (${book.publisher}, ${book.year})`;
    document.getElementById("modalBreadcrumb").textContent = book.location_breadcrumb;
    document.getElementById("modalCallBadge").textContent = book.call_no;
    document.getElementById("modalFloorLabel").textContent = book.floor === 0 ? "Ground Floor" : `Floor ${book.floor}`;

    const resBtn = document.getElementById("modalBtnReserve");
    if (book.available_copies > 0) {
      resBtn.textContent = `Reserve Copy (${book.available_copies} Ready)`;
      resBtn.className = "btn-reserve";
    } else {
      resBtn.textContent = `Join Waitlist (Queue: ${book.reservation_queue.length} Ahead)`;
      resBtn.className = "btn-reserve waitlist";
    }
    resBtn.onclick = () => quickReserveBook(book.id);

    // Render 4-tier Rack Graphic
    renderRackTierGraphic(book.shelf_tier, book.call_no);

    // Render Step-by-Step Walking Directions
    const guideEl = document.getElementById("modalWalkingGuide");
    guideEl.innerHTML = book.walking_guide.map(step => `<li>${step}</li>`).join("");

    // Render Indoor Floor Plan SVG with target rack glowing beacon
    renderFloorPlanShelfMap(book);

    openModal("shelfLocatorModal");
    SoundFX.playChime("success");
  } catch (err) {
    console.error("Failed to load shelf locator:", err);
  }
}

// 4-Tier Rack Shelf Visualizer
function renderRackTierGraphic(activeTier, callNo) {
  const container = document.getElementById("tierVisualizer");
  if (!container) return;

  const tiers = [
    { num: 4, label: "Tier 4 — Top Shelf (Above Eye Level)" },
    { num: 3, label: "Tier 3 — Eye Level Shelf (140 cm)" },
    { num: 2, label: "Tier 2 — Chest Level Shelf (100 cm)" },
    { num: 1, label: "Tier 1 — Bottom Shelf (Base Tier)" }
  ];

  container.innerHTML = tiers.map(t => {
    const isTarget = t.num === activeTier;
    const bg = isTarget ? "#ecfdf5" : "#f8fafc";
    const border = isTarget ? "2px solid #059669" : "1px solid var(--border)";
    const tag = isTarget ? `<span style="background:#059669; color:#fff; font-size:0.7rem; font-weight:800; padding:2px 8px; border-radius:4px;">TARGET BOOK: ${callNo}</span>` : `<span style="font-size:0.75rem; color:#94a3b8;">Other Titles</span>`;

    return `
      <div style="background: ${bg}; border: ${border}; border-radius: 6px; padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 0.82rem; font-weight: ${isTarget ? '800' : '500'}; color: ${isTarget ? '#065f46' : '#475569'};">
          ${isTarget ? '👉 ' : ''}${t.label}
        </span>
        ${tag}
      </div>
    `;
  }).join("");
}

// Render Floor Plan Shelf Map with Path & Pulsing Beacon
function renderFloorPlanShelfMap(book) {
  const container = document.getElementById("modalSvgMapContainer");
  if (!container) return;

  const isFloor1 = book.floor === 1;
  const isFloor2 = book.floor === 2;

  // Racks positioning
  // Floor 1: Aisles A-1..A-3 (Robotics/Mfg), Aisles B-1..B-3 (AI/Computing)
  // Let's calculate target X, Y
  let targetX = 350;
  let targetY = 140;

  if (book.aisle.includes("A-1")) targetX = 140;
  else if (book.aisle.includes("A-2")) targetX = 220;
  else if (book.aisle.includes("A-3")) targetX = 300;
  else if (book.aisle.includes("B-1")) targetX = 420;
  else if (book.aisle.includes("B-2")) targetX = 500;
  else if (book.aisle.includes("B-3")) targetX = 580;
  else if (book.aisle.includes("C-1")) targetX = 160;
  else if (book.aisle.includes("C-2")) targetX = 260;
  else if (book.aisle.includes("D-1")) targetX = 450;
  else if (book.aisle.includes("D-2")) targetX = 550;

  if (book.rack.includes("R-02")) targetY = 180;
  else if (book.rack.includes("R-03")) targetY = 220;

  const svg = `
    <svg viewBox="0 0 740 320" width="100%" height="260" xmlns="http://www.w3.org/2000/svg" style="background:#ffffff; border-radius:8px; border:1px solid #e2e8f0;">
      <!-- Definitions & Glowing Beacon Animation -->
      <defs>
        <radialGradient id="beaconGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#10b981" stop-opacity="0.8"/>
          <stop offset="100%" stop-color="#10b981" stop-opacity="0"/>
        </radialGradient>
        <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
          <feDropShadow dx="1" dy="2" stdDeviation="2" flood-color="#0f172a" flood-opacity="0.15"/>
        </filter>
      </defs>

      <!-- Outer Walls -->
      <rect x="20" y="20" width="700" height="280" rx="12" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>

      <!-- Circulation & Entry (Bottom Center) -->
      <rect x="300" y="260" width="140" height="35" rx="6" fill="#ecfdf5" stroke="#059669" stroke-width="2"/>
      <text x="370" y="282" text-anchor="middle" font-size="11" font-weight="700" fill="#065f46">MAIN ENTRANCE / DESK</text>

      <!-- Atrium / Staircase Core -->
      <rect x="330" y="50" width="80" height="80" rx="6" fill="#e2e8f0" stroke="#94a3b8" stroke-width="1.5"/>
      <text x="370" y="85" text-anchor="middle" font-size="10" font-weight="700" fill="#475569">STAIRS &</text>
      <text x="370" y="100" text-anchor="middle" font-size="10" font-weight="700" fill="#475569">ELEVATOR</text>

      <!-- Section Labels -->
      <text x="180" y="45" text-anchor="middle" font-size="12" font-weight="800" fill="#0f766e">
        ${isFloor1 ? 'SECTION A: MANUFACTURING & ROBOTICS' : 'SECTION C: GREEN ENERGY & EV'}
      </text>
      <text x="540" y="45" text-anchor="middle" font-size="12" font-weight="800" fill="#0f766e">
        ${isFloor1 ? 'SECTION B: COMPUTING & ARTIFICIAL INTELLIGENCE' : 'SECTION D: HEALTHCARE & FOOD TECH'}
      </text>

      <!-- Left Racks (Aisle A or C) -->
      <g stroke="#94a3b8" stroke-width="1" fill="#ffffff" filter="url(#shadow)">
        <rect x="120" y="70" width="45" height="150" rx="4" />
        <rect x="200" y="70" width="45" height="150" rx="4" />
        <rect x="280" y="70" width="45" height="150" rx="4" />
      </g>
      <text x="142" y="235" text-anchor="middle" font-size="9" fill="#64748b" font-weight="700">AISLE 1</text>
      <text x="222" y="235" text-anchor="middle" font-size="9" fill="#64748b" font-weight="700">AISLE 2</text>
      <text x="302" y="235" text-anchor="middle" font-size="9" fill="#64748b" font-weight="700">AISLE 3</text>

      <!-- Right Racks (Aisle B or D) -->
      <g stroke="#94a3b8" stroke-width="1" fill="#ffffff" filter="url(#shadow)">
        <rect x="420" y="70" width="45" height="150" rx="4" />
        <rect x="500" y="70" width="45" height="150" rx="4" />
        <rect x="580" y="70" width="45" height="150" rx="4" />
      </g>
      <text x="442" y="235" text-anchor="middle" font-size="9" fill="#64748b" font-weight="700">AISLE 1</text>
      <text x="522" y="235" text-anchor="middle" font-size="9" fill="#64748b" font-weight="700">AISLE 2</text>
      <text x="602" y="235" text-anchor="middle" font-size="9" fill="#64748b" font-weight="700">AISLE 3</text>

      <!-- Walking Route Dashed Path -->
      <path d="M 370 260 L 370 240 L ${targetX + 15} 240 L ${targetX + 15} ${targetY + 20}" 
            fill="none" stroke="#059669" stroke-width="3" stroke-dasharray="6,4" stroke-linecap="round"/>

      <!-- Pulsing Beacon on Target Rack -->
      <circle cx="${targetX + 15}" cy="${targetY}" r="26" fill="url(#beaconGlow)">
        <animate attributeName="r" values="16;30;16" dur="2s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="0.8;0.2;0.8" dur="2s" repeatCount="indefinite"/>
      </circle>
      <circle cx="${targetX + 15}" cy="${targetY}" r="12" fill="#059669" stroke="#ffffff" stroke-width="2"/>
      <text x="${targetX + 15}" y="${targetY + 4}" text-anchor="middle" font-size="9" font-weight="900" fill="#ffffff">📍</text>

      <!-- Target Rack Label Callout -->
      <g transform="translate(${targetX - 25}, ${targetY - 38})">
        <rect x="0" y="0" width="90" height="24" rx="4" fill="#0f172a" />
        <text x="45" y="16" text-anchor="middle" font-size="9" font-weight="800" fill="#a7f3d0">${book.rack}</text>
      </g>
    </svg>
  `;

  container.innerHTML = svg;
}

// Quick Reserve Book Action
async function quickReserveBook(bookId) {
  try {
    const res = await fetch(`/api/books/${bookId}/reserve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: AppState.currentUser.id,
        student_name: AppState.currentUser.name
      })
    });
    const data = await res.json();
    if (data.success) {
      SoundFX.playChime("success");
      alert(data.message);
      closeModal("shelfLocatorModal");
      refreshAllData();
    } else {
      alert("Error: " + data.error);
    }
  } catch (err) {
    console.error("Reserve failed:", err);
  }
}

// ============================================================================
// Renderers: Real-Time Seat Occupancy & Floor Plan
// ============================================================================
function renderSeatMap() {
  const container = document.getElementById("svgFloorPlanContainer");
  if (!container) return;

  const currentSeats = AppState.seats.filter(s => s.floor === AppState.activeFloor);
  const isFloor1 = AppState.activeFloor === 1;

  let svg = `
    <svg viewBox="0 0 820 420" width="100%" height="420" xmlns="http://www.w3.org/2000/svg" style="background:#ffffff; border-radius:12px; border:1px solid #e2e8f0; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
      <!-- Floor Boundary -->
      <rect x="15" y="15" width="790" height="390" rx="14" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>

      <!-- Floor Header -->
      <text x="35" y="45" font-size="16" font-weight="800" fill="#065f46">
        ASSAM SKILL UNIVERSITY CENTRAL LIBRARY — FLOOR ${AppState.activeFloor} SEATING PLAN
      </text>

      <!-- Entrance & Corridor -->
      <rect x="360" y="375" width="100" height="30" rx="4" fill="#e2e8f0" stroke="#94a3b8"/>
      <text x="410" y="394" text-anchor="middle" font-size="10" font-weight="700" fill="#475569">CENTRAL FOYER</text>

      <!-- Zone Separators & Labels -->
      <line x1="390" y1="60" x2="390" y2="360" stroke="#e2e8f0" stroke-width="2" stroke-dasharray="6,4"/>

      <!-- Left Zone Title -->
      <text x="180" y="75" text-anchor="middle" font-size="13" font-weight="800" fill="#0f766e">
        ${isFloor1 ? 'QUIET INDIVIDUAL STUDY CARRELS (ZONE A)' : 'COLLABORATIVE 4-SEATER PODS (ZONE B)'}
      </text>

      <!-- Right Zone Title -->
      <text x="580" y="75" text-anchor="middle" font-size="13" font-weight="800" fill="#0f766e">
        ${isFloor1 ? 'DIGITAL AI & GPU LAB WORKSTATIONS (ZONE C)' : 'SCHOLARS & RESEARCH SUITE (ZONE D)'}
      </text>
  `;

  // Render Seats
  currentSeats.forEach(seat => {
    const isAvail = seat.status === "AVAILABLE";
    const fill = isAvail ? "#d1fae5" : (seat.status === "OCCUPIED" ? "#fee2e2" : (seat.status === "RESERVED" ? "#fef3c7" : "#f1f5f9"));
    const stroke = isAvail ? "#10b981" : (seat.status === "OCCUPIED" ? "#ef4444" : (seat.status === "RESERVED" ? "#f59e0b" : "#94a3b8"));
    const occupantText = seat.current_student_name ? `Occupant: ${seat.current_student_name}` : 'Click to Reserve';

    svg += `
      <g class="seat-node" onclick="handleSeatClick(${seat.id})" style="cursor: pointer;">
        <rect x="${seat.pos_x}" y="${seat.pos_y}" width="52" height="42" rx="6" 
              class="seat-rect ${seat.status}" fill="${fill}" stroke="${stroke}" stroke-width="2">
          <title>${seat.seat_number} (${seat.status})&#10;${seat.zone}&#10;${occupantText}</title>
        </rect>
        <text x="${seat.pos_x + 26}" y="${seat.pos_y + 24}" class="seat-text" text-anchor="middle" font-size="11" font-weight="800" fill="#1e293b">
          ${seat.seat_number}
        </text>
        ${seat.has_power ? `<text x="${seat.pos_x + 6}" y="${seat.pos_y + 12}" font-size="9">⚡</text>` : ''}
      </g>
    `;
  });

  svg += `</svg>`;
  container.innerHTML = svg;
}

function renderZoneCards(seats) {
  const container = document.getElementById("zonesOverview");
  if (!container) return;

  const zones = {};
  seats.forEach(s => {
    if (!zones[s.zone]) zones[s.zone] = { total: 0, occupied: 0, reserved: 0, available: 0 };
    zones[s.zone].total++;
    if (s.status === "OCCUPIED") zones[s.zone].occupied++;
    else if (s.status === "RESERVED") zones[s.zone].reserved++;
    else if (s.status === "AVAILABLE") zones[s.zone].available++;
  });

  let html = "";
  for (const [zName, z] of Object.entries(zones)) {
    const occPct = Math.round(((z.occupied + z.reserved) / z.total) * 100);
    html += `
      <div class="zone-card">
        <div class="zone-card-header">
          <span class="zone-title">${zName}</span>
          <span class="badge" style="background:#ecfdf5; color:#065f46; font-size:0.75rem; font-weight:700;">${z.available} Free</span>
        </div>
        <div class="zone-occupancy-bar">
          <div class="zone-occupancy-fill" style="width: ${occPct}%;"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:var(--text-muted);">
          <span>Occupancy: ${occPct}%</span>
          <span>${z.total} Desks Total</span>
        </div>
      </div>
    `;
  }
  container.innerHTML = html;
}

// Seat Click Handler
function handleSeatClick(seatId) {
  const seat = AppState.seats.find(s => s.id === seatId);
  if (!seat) return;

  AppState.selectedSeat = seat;

  if (seat.status === "AVAILABLE") {
    // Open Booking Modal
    document.getElementById("seatModalTitle").textContent = `Book Desk ${seat.seat_number}`;
    document.getElementById("seatModalDeskNo").textContent = seat.seat_number;
    document.getElementById("seatModalZone").textContent = `${seat.zone} (Floor ${seat.floor})`;
    document.getElementById("seatModalAmenities").textContent = `⚡ AC Power Outlet • 🌐 LAN Port • 💡 Reading Lamp`;

    // Show form, hide pass
    document.getElementById("seatBookingFormArea").style.display = "block";
    document.getElementById("seatPassGeneratedArea").style.display = "none";

    // Setup duration buttons
    const durBtns = document.querySelectorAll(".duration-choice");
    let chosenDuration = 120;
    durBtns.forEach(b => {
      b.onclick = () => {
        durBtns.forEach(x => x.classList.remove("active"));
        b.classList.add("active");
        chosenDuration = parseInt(b.getAttribute("data-min"));
      };
    });

    const confirmBtn = document.getElementById("btnConfirmSeatBooking");
    confirmBtn.onclick = () => reserveSeatAction(seat.id, chosenDuration);

    openModal("seatBookingModal");
  } else if (seat.status === "RESERVED" && seat.current_student_id === AppState.currentUser.id) {
    // Prompt to check in
    const confirmArrival = confirm(`You have reserved Desk ${seat.seat_number}.\nConfirm Check-In to start studying?`);
    if (confirmArrival) {
      checkInSeatAction(seat.id, seat.checkin_code);
    }
  } else if (seat.status === "OCCUPIED" && seat.current_student_id === AppState.currentUser.id) {
    const vacate = confirm(`You are currently occupying Desk ${seat.seat_number}.\nWould you like to release this seat now?`);
    if (vacate) {
      releaseSeatAction(seat.id);
    }
  } else {
    alert(`Desk ${seat.seat_number} is currently ${seat.status}.\n${seat.current_student_name ? 'Occupied by: ' + seat.current_student_name : ''}`);
  }
}

// Seat Reservation Action
async function reserveSeatAction(seatId, durationMin) {
  try {
    const res = await fetch(`/api/seats/${seatId}/reserve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: AppState.currentUser.id,
        student_name: AppState.currentUser.name,
        duration_minutes: durationMin
      })
    });
    const data = await res.json();
    if (data.success) {
      SoundFX.playChime("success");

      // Switch to Boarding Pass View
      document.getElementById("seatBookingFormArea").style.display = "none";
      const passArea = document.getElementById("seatPassGeneratedArea");
      passArea.style.display = "block";

      document.getElementById("passDeskNumber").textContent = data.seat_number;
      document.getElementById("passCodeDisplay").textContent = data.checkin_code;
      document.getElementById("passGraceNotice").textContent = `⚠️ Check-in required by ${data.grace_period_until} or seat will auto-release.`;

      // Generate SVG QR Code client-side
      generateQRCodeSVG("passQrContainer", `ASU-LIB-SEAT:${data.seat_number}:${data.checkin_code}`);

      // Setup Check in button
      document.getElementById("btnPassCheckInNow").onclick = () => {
        checkInSeatAction(seatId, data.checkin_code);
        closeModal("seatBookingModal");
      };

      refreshAllData();
    } else {
      alert("Error: " + data.error);
    }
  } catch (err) {
    console.error("Failed to reserve seat:", err);
  }
}

async function checkInSeatAction(seatId, code) {
  try {
    const res = await fetch(`/api/seats/${seatId}/checkin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        student_id: AppState.currentUser.id,
        checkin_code: code
      })
    });
    const data = await res.json();
    if (data.success) {
      SoundFX.playChime("success");
      alert(data.message);
      refreshAllData();
    } else {
      alert("Check-in error: " + data.error);
    }
  } catch (err) {
    console.error("Check-in failed:", err);
  }
}

async function releaseSeatAction(seatId) {
  try {
    const res = await fetch(`/api/seats/${seatId}/release`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ student_id: AppState.currentUser.id })
    });
    const data = await res.json();
    if (data.success) {
      SoundFX.playChime("success");
      alert(data.message);
      refreshAllData();
    }
  } catch (err) {
    console.error("Release seat failed:", err);
  }
}

// Client-Side Scalable SVG QR Code Generator (Zero External Dependencies)
function generateQRCodeSVG(containerId, dataString) {
  const container = document.getElementById(containerId);
  if (!container) return;

  // Generate a deterministic 21x21 QR Matrix representation based on string hash
  const size = 21;
  const matrix = Array.from({ length: size }, () => Array(size).fill(false));

  // Finder Patterns (3 corners)
  const addFinder = (r0, c0) => {
    for (let r = 0; r < 7; r++) {
      for (let c = 0; c < 7; c++) {
        if (r === 0 || r === 6 || c === 0 || c === 6 || (r >= 2 && r <= 4 && c >= 2 && c <= 4)) {
          matrix[r0 + r][c0 + c] = true;
        }
      }
    }
  };
  addFinder(0, 0);
  addFinder(0, size - 7);
  addFinder(size - 7, 0);

  // Timing lines
  for (let i = 8; i < size - 8; i++) {
    if (i % 2 === 0) {
      matrix[6][i] = true;
      matrix[i][6] = true;
    }
  }

  // Hash-based data bits
  let hash = 0;
  for (let i = 0; i < dataString.length; i++) {
    hash = (hash << 5) - hash + dataString.charCodeAt(i);
    hash |= 0;
  }

  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      // Don't overwrite finders
      if ((r < 8 && c < 8) || (r < 8 && c >= size - 8) || (r >= size - 8 && c < 8)) continue;
      if (matrix[r][c]) continue;
      const bit = ((hash ^ (r * 31 + c * 17)) & 1) === 1;
      matrix[r][c] = bit;
    }
  }

  // Build SVG
  let svg = `<svg viewBox="0 0 ${size} ${size}" width="140" height="140" xmlns="http://www.w3.org/2000/svg">`;
  svg += `<rect width="${size}" height="${size}" fill="#ffffff"/>`;
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      if (matrix[r][c]) {
        svg += `<rect x="${c}" y="${r}" width="1" height="1" fill="#0f172a"/>`;
      }
    }
  }
  svg += `</svg>`;
  container.innerHTML = svg;
}

// ============================================================================
// Renderers: My Borrowings & Due-Date Tracker
// ============================================================================
function renderBorrowings(borrowings) {
  const container = document.getElementById("borrowingsList");
  if (!container) return;

  const activeLoans = borrowings.filter(b => b.status !== "RETURNED");

  if (activeLoans.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 48px; background: #fff; border-radius: 12px; border: 1px dashed var(--border);">
        <div style="font-size: 2.5rem; margin-bottom: 8px;">📖</div>
        <h3 style="font-weight: 700;">No active books currently borrowed</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem;">Browse the Smart Book Catalog to reserve and pick up books from the circulation desk.</p>
      </div>
    `;
    return;
  }

  const today = new Date();

  container.innerHTML = activeLoans.map(loan => {
    const dueDt = new Date(loan.due_date);
    const diffTime = dueDt.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    const isOverdue = diffDays < 0;
    const isDueSoon = diffDays >= 0 && diffDays <= 3;
    const cardClass = isOverdue ? "overdue" : (isDueSoon ? "due-soon" : "safe");
    const countClass = isOverdue ? "red" : (isDueSoon ? "amber" : "green");

    const daysText = isOverdue ? `${Math.abs(diffDays)}d` : `${diffDays}d`;
    const daysLabel = isOverdue ? "OVERDUE" : "LEFT";

    return `
      <div class="borrowing-card ${cardClass}">
        <div class="due-countdown-box ${countClass}">
          <div class="count-days">${daysText}</div>
          <div class="count-label">${daysLabel}</div>
        </div>

        <div class="borrowing-details">
          <h3>${loan.book_title}</h3>
          <div style="font-size: 0.85rem; color: #475569;">Author: ${loan.book_author}</div>
          <div class="borrowing-meta-strip">
            <span>📅 Issued: ${loan.issue_date}</span>
            <span>⏳ Due: <strong>${loan.due_date}</strong></span>
            <span>📍 Shelf: Floor ${loan.book_floor} (${loan.book_aisle})</span>
            <span>🔄 Renewed: ${loan.renewal_count} of 2 max</span>
            ${isOverdue ? `<span style="color:#b91c1c; font-weight:800;">🚨 Fine: ₹${loan.fine_amount.toFixed(2)} (@ ₹2/day)</span>` : ''}
          </div>
        </div>

        <div class="borrowing-actions">
          <button class="btn-renew" onclick="renewBorrowingAction(${loan.id})">
            <span>🔄</span> Extend (+14 Days)
          </button>
          <button class="btn-return-desk" onclick="returnBookAction(${loan.id})">
            Return Book
          </button>
        </div>
      </div>
    `;
  }).join("");
}

async function renewBorrowingAction(borrowingId) {
  try {
    const res = await fetch(`/api/borrowings/${borrowingId}/renew`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      SoundFX.playChime("success");
      alert(data.message);
      refreshAllData();
    } else {
      SoundFX.playChime("alert");
      alert("Renewal Error: " + data.error);
    }
  } catch (err) {
    console.error("Renewal failed:", err);
  }
}

async function returnBookAction(borrowingId) {
  const ok = confirm("Confirm return of this book at the Circulation Desk?");
  if (!ok) return;

  try {
    const res = await fetch("/api/admin/return-book", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ borrowing_id: borrowingId })
    });
    const data = await res.json();
    if (data.success) {
      SoundFX.playChime("success");
      alert(data.message);
      refreshAllData();
    }
  } catch (err) {
    console.error("Return failed:", err);
  }
}

// Simulate Cron Automated Reminder Dispatcher
document.getElementById("btnSimulateReminders")?.addEventListener("click", async () => {
  try {
    const res = await fetch("/api/notifications/dispatch-reminders", { method: "POST" });
    const data = await res.json();
    if (data.success) {
      SoundFX.playChime("alert");
      alert(`Automated Reminder Engine Executed!\n${data.dispatched_count} SMS and Email notifications dispatched.`);
      refreshAllData();
    }
  } catch (err) {
    console.error("Reminder simulation failed:", err);
  }
});

// ============================================================================
// Renderers: Multi-Channel Alerts Simulator (In-App, SMS, Webmail)
// ============================================================================
function renderAlertsChannel(notifications) {
  // 1. In-App Feed
  const inAppList = document.getElementById("inAppAlertsList");
  if (inAppList) {
    inAppList.innerHTML = notifications.slice(0, 8).map(n => {
      const isUrgent = n.urgency === "OVERDUE" || n.urgency === "URGENT";
      const border = isUrgent ? "border-left: 4px solid #ef4444;" : "border-left: 4px solid #10b981;";
      return `
        <div style="background: #f8fafc; border: 1px solid var(--border); ${border} border-radius: 8px; padding: 12px;">
          <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <strong style="font-size:0.85rem; color:var(--text-main);">${n.title}</strong>
            <span style="font-size:0.7rem; color:var(--text-muted);">${n.timestamp}</span>
          </div>
          <p style="font-size:0.82rem; color:#475569; margin:0;">${n.message}</p>
        </div>
      `;
    }).join("");
  }

  // 2. Simulated Smartphone SMS
  const smsContainer = document.getElementById("smsScreenContainer");
  if (smsContainer) {
    const smsAlerts = notifications.filter(n => n.channel === "SMS");
    if (smsAlerts.length > 0) {
      smsContainer.innerHTML = `
        <div style="font-size: 0.72rem; color: #64748b; text-align: center; margin-bottom: 12px;">Sender: ASU-LIB (Assam Skill Univ)</div>
        ${smsAlerts.map(n => `
          <div class="sms-bubble ${n.urgency === 'OVERDUE' ? 'urgent' : ''}">
            <strong>${n.title}</strong>
            <div>${n.message}</div>
            <div class="sms-time">${n.timestamp.split(" ")[1] || ''}</div>
          </div>
        `).join("")}
      `;
    }
  }

  // 3. Simulated Institutional Webmail
  const emailContainer = document.getElementById("emailMockupContainer");
  if (emailContainer) {
    const emailAlerts = notifications.filter(n => n.channel === "EMAIL");
    if (emailAlerts.length > 0) {
      const topEmail = emailAlerts[0];
      emailContainer.innerHTML = `
        <div class="email-meta">
          <div><strong>From:</strong> Central Library &lt;library@asu.ac.in&gt;</div>
          <div><strong>To:</strong> ${AppState.currentUser.name} &lt;${AppState.currentUser.id.toLowerCase().replace('/', '.')}@student.asu.ac.in&gt;</div>
          <div><strong>Subject:</strong> ${topEmail.title}</div>
          <div><strong>Date:</strong> ${topEmail.timestamp}</div>
        </div>
        <div class="email-body">
          ${topEmail.message}
        </div>
        <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--border); font-size: 0.75rem; color: #64748b;">
          Assam Skill University Central Library • Mangaldai, Darrang, Assam — 784125 • Tel: +91 3713-XXXXXX
        </div>
      `;
    }
  }
}

// ============================================================================
// Admin Circulation & Management Forms
// ============================================================================
function populateIssueDropdown(books) {
  const select = document.getElementById("issueBookSelect");
  if (!select) return;
  select.innerHTML = books.map(b => `
    <option value="${b.id}" ${b.available_copies <= 0 ? 'disabled' : ''}>
      ${b.title} (${b.available_copies} available) [${b.call_no}]
    </option>
  `).join("");
}

function setupAdminForms() {
  // 1. Issue Book Form
  const formIssue = document.getElementById("formIssueBook");
  formIssue?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const bookId = document.getElementById("issueBookSelect").value;
    const studId = document.getElementById("issueStudentId").value;
    const studName = document.getElementById("issueStudentName").value;
    const days = document.getElementById("issueDuration").value;

    try {
      const res = await fetch("/api/admin/issue-book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          book_id: parseInt(bookId),
          student_id: studId,
          student_name: studName,
          days: parseInt(days)
        })
      });
      const data = await res.json();
      if (data.success) {
        SoundFX.playChime("success");
        alert(data.message);
        refreshAllData();
      } else {
        alert("Issue error: " + data.error);
      }
    } catch (err) {
      console.error("Issue failed:", err);
    }
  });

  // 2. Add New Book Form
  const formAdd = document.getElementById("formAddBook");
  formAdd?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("newBookTitle").value;
    const author = document.getElementById("newBookAuthor").value;
    const floor = document.getElementById("newBookFloor").value;
    const rack = document.getElementById("newBookRack").value;
    const tier = document.getElementById("newBookTier").value;
    const copies = document.getElementById("newBookCopies").value;

    try {
      const res = await fetch("/api/admin/add-book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: title,
          author: author,
          floor: parseInt(floor),
          aisle: rack.split("/")[0]?.trim() || "Aisle B-2",
          rack: rack.split("/")[1]?.trim() || "Rack R-01",
          shelf_tier: parseInt(tier),
          copies: parseInt(copies)
        })
      });
      const data = await res.json();
      if (data.success) {
        SoundFX.playChime("success");
        alert(data.message);
        formAdd.reset();
        refreshAllData();
      } else {
        alert("Add error: " + data.error);
      }
    } catch (err) {
      console.error("Add book failed:", err);
    }
  });

  // 3. Broadcast Announcement Form
  const formBroadcast = document.getElementById("formBroadcast");
  formBroadcast?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("broadcastTitle").value;
    const msg = document.getElementById("broadcastMessage").value;

    try {
      const res = await fetch("/api/admin/broadcast", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, message: msg })
      });
      const data = await res.json();
      if (data.success) {
        SoundFX.playChime("alert");
        alert(data.message);
        formBroadcast.reset();
        refreshAllData();
      }
    } catch (err) {
      console.error("Broadcast failed:", err);
    }
  });

  // 4. Reset Demo DB Button
  document.getElementById("btnResetDb")?.addEventListener("click", async () => {
    if (confirm("Reset the entire library database to initial demonstration state?")) {
      try {
        const res = await fetch("/api/seed", { method: "POST" });
        const data = await res.json();
        if (data.success) {
          SoundFX.playChime("success");
          alert("Database reset successfully!");
          refreshAllData();
        }
      } catch (err) {
        console.error("Reset failed:", err);
      }
    }
  });
}

// ============================================================================
// Modal Utilities
// ============================================================================
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.add("active");
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove("active");
}

window.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("active");
  }
});
