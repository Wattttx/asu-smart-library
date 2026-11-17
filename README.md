# Assam Skill University Central Library
## Smart Book Search, Indoor Shelf Locator & Real-Time Seat Occupancy System

An intelligent, full-stack library management and navigation system developed specifically for **Assam Skill University (ASU)** Central Library at the Mangaldai Campus, Darrang, Assam.

---

## 🌟 Key Problems Solved

1. **Wasted Time Finding Books**:
   - Students no longer wander down aisles trying to match call numbers.
   - The interactive **Shelf Locator Map** highlights the exact Floor, Aisle, Rack, and Shelf Tier (1-4) with turn-by-turn walking directions from the Central Foyer.
2. **Seat Hunting & Ghosting**:
   - Real-time seat occupancy visualization across Floor 1 and Floor 2 (Quiet Study Carrels, Collaborative Pods, Digital AI Workstations, and Research Cubicles).
   - Instant digital seat reservation with a **15-minute grace period check-in** and printable/scannable QR Boarding Pass to prevent hoarding.
3. **Forgotten Due Dates & Late Penalties**:
   - Proactive multi-channel reminder dispatcher (Simulated SMS gateway, Institutional Webmail, and In-App notification feed).
   - Automated ₹2.00/day fine calculation and 1-click 14-day online loan renewal.
4. **Vocational & Academic Skill Repository**:
   - Quick gateway access to IEEE Xplore, DELNET Inter-Library Loan, NPTEL/SWAYAM courseware, and ASU Mid-Semester Question Papers (PYQs).

---

## 🏗️ System Architecture

- **Backend**:
  - Python standard library multi-threaded HTTP server (`ThreadingTCPServer`) with RESTful JSON API.
  - SQLite relational database with pre-seeded data for 24+ skill books, 48 interactive desks, active loans, waitlists, and announcements.
  - Zero third-party Python dependencies (runs on pure Python 3.8+ out of the box).
- **Frontend**:
  - Pure HTML5, Modern Responsive CSS, and Vanilla JavaScript SPA.
  - Interactive SVG Indoor Floor Plans (real-time glowing beacons, animated walking routes).
  - Client-side Scalable Vector Graphics (SVG) QR Code Generator.
  - Synthesized Web Audio API harmonic sound chimes for notifications and reservation confirmations.

---

## 🚀 How to Run

### Option 1: Via Windows Command Line or PowerShell
```powershell
cd C:\Users\HP\.gemini\antigravity\scratch\asu_smart_library
python server.py 8080
```

### Option 2: Double-click Launcher
Double-click `run.bat` in the project directory.

Once started, open your web browser and navigate to:
**`http://localhost:8080`**

---

## 📑 Core REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/stats` | Real-time library metrics, seat occupancy %, inventory counts |
| `GET` | `/api/books?q=...&floor=...&category=...` | Search catalog with multi-field search and filters |
| `GET` | `/api/books/<id>` | Full book details, reservation queue, shelf coordinates & walking route |
| `POST` | `/api/books/<id>/reserve` | Reserve a copy or join the waitlist queue |
| `GET` | `/api/seats?floor=1` | Real-time seat list with status (`AVAILABLE`, `OCCUPIED`, `RESERVED`) |
| `POST` | `/api/seats/<id>/reserve` | Reserve study desk, generates 15-min grace timer & QR code |
| `POST` | `/api/seats/<id>/checkin` | Confirm arrival using check-in pass code |
| `POST` | `/api/seats/<id>/release` | Vacate desk and return to available pool |
| `GET` | `/api/borrowings?student_id=...` | Active student book loans with live overdue fine calculator |
| `POST` | `/api/borrowings/<id>/renew` | Extend loan due date by 14 days |
| `POST` | `/api/notifications/dispatch-reminders` | Automated cron simulation to dispatch SMS and Email alerts |
| `POST` | `/api/admin/issue-book` | Circulation desk checkout |
| `POST` | `/api/admin/return-book` | Circulation desk return & fine settlement |
| `POST` | `/api/admin/add-book` | Catalog new book with floor, aisle, rack & tier mapping |
| `POST` | `/api/seed` | Reset database to clean demo state |

---

## 🧪 Automated Testing
Run the backend unit test suite:
```powershell
python test_api.py
```
Outputs:
```
Ran 7 tests in 0.079s
OK
```
