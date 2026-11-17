"""
Assam Skill University Central Library - Smart Book & Seat Availability Server
High-performance REST API and Static File Server built with Python standard library.
Zero external dependencies required.
"""

import http.server
import socketserver
import json
import os
import sys
import urllib.parse
from datetime import datetime, timedelta
import sqlite3
import mimetypes

from database import get_db, init_db, seed_data

PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Custom JSON encoder to serialize sqlite3.Row and datetimes
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, sqlite3.Row):
            return dict(obj)
        if isinstance(obj, (datetime, timedelta)):
            return str(obj)
        return super().default(obj)

def json_response(handler, status_code, data):
    body = json.dumps(data, cls=CustomJSONEncoder).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
    handler.end_headers()
    handler.wfile.write(body)

def text_response(handler, status_code, text, content_type="text/plain; charset=utf-8"):
    body = text.encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)

class LibraryRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # API routing
        if path.startswith("/api/"):
            try:
                self.handle_api_get(path, query)
            except Exception as e:
                json_response(self, 500, {"error": str(e), "success": False})
            return

        # Fallback to static files
        if path == "/" or path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/"):
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = {}
                if content_length > 0:
                    raw_body = self.rfile.read(content_length).decode("utf-8")
                    if raw_body:
                        post_data = json.loads(raw_body)
                self.handle_api_post(path, post_data)
            except Exception as e:
                json_response(self, 500, {"error": str(e), "success": False})
            return

        json_response(self, 404, {"error": "Not Found", "success": False})

    # =========================================================================
    # GET API Endpoints
    # =========================================================================
    def handle_api_get(self, path, query):
        conn = get_db()
        cursor = conn.cursor()

        # Update overdue borrowings dynamically
        today_str = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            UPDATE borrowings
            SET status = 'OVERDUE',
                fine_amount = ROUND((julianday(?) - julianday(due_date)) * 2.0, 2)
            WHERE status = 'BORROWED' AND due_date < ?
        """, (today_str, today_str))
        conn.commit()

        # 1. Overall Library Stats
        if path == "/api/stats":
            cursor.execute("SELECT COUNT(*), SUM(total_copies), SUM(available_copies) FROM books")
            book_row = cursor.fetchone()
            total_titles = book_row[0] or 0
            total_inventory = book_row[1] or 0
            available_books = book_row[2] or 0
            borrowed_books = total_inventory - available_books

            cursor.execute("""
                SELECT 
                    COUNT(*) as total_seats,
                    SUM(CASE WHEN status = 'OCCUPIED' THEN 1 ELSE 0 END) as occupied_seats,
                    SUM(CASE WHEN status = 'RESERVED' THEN 1 ELSE 0 END) as reserved_seats,
                    SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) as available_seats,
                    SUM(CASE WHEN status = 'MAINTENANCE' THEN 1 ELSE 0 END) as maintenance_seats
                FROM seats
            """)
            seat_row = cursor.fetchone()

            # Floor-wise seat occupancy
            cursor.execute("""
                SELECT floor,
                       COUNT(*) as total,
                       SUM(CASE WHEN status = 'OCCUPIED' THEN 1 ELSE 0 END) as occupied,
                       SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) as available
                FROM seats GROUP BY floor
            """)
            floor_stats = [dict(r) for r in cursor.fetchall()]

            # Active borrowings & overdues
            cursor.execute("SELECT COUNT(*) FROM borrowings WHERE status = 'OVERDUE'")
            overdue_count = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(fine_amount) FROM borrowings WHERE status = 'OVERDUE'")
            total_fine = cursor.fetchone()[0] or 0.0

            # Hourly seat occupancy trend (realistic ASU library distribution)
            hourly_trend = [
                {"hour": "08:00", "occupancy": 15},
                {"hour": "10:00", "occupancy": 48},
                {"hour": "12:00", "occupancy": 76},
                {"hour": "14:00", "occupancy": 88},
                {"hour": "16:00", "occupancy": 92},
                {"hour": "18:00", "occupancy": 74},
                {"hour": "20:00", "occupancy": 52},
                {"hour": "22:00", "occupancy": 28}
            ]

            stats = {
                "success": True,
                "library_name": "Assam Skill University Central Library",
                "campus": "Mangaldai Campus, Darrang, Assam",
                "total_titles": total_titles,
                "total_inventory": total_inventory,
                "available_books": available_books,
                "borrowed_books": borrowed_books,
                "total_seats": seat_row["total_seats"],
                "occupied_seats": seat_row["occupied_seats"],
                "reserved_seats": seat_row["reserved_seats"],
                "available_seats": seat_row["available_seats"],
                "maintenance_seats": seat_row["maintenance_seats"],
                "occupancy_rate": round((seat_row["occupied_seats"] / max(1, seat_row["total_seats"])) * 100, 1),
                "overdue_count": overdue_count,
                "pending_fines": round(total_fine, 2),
                "floor_stats": floor_stats,
                "hourly_trend": hourly_trend,
                "digital_terminals": 40,
                "delnet_active": True,
                "ieee_active": True
            }
            conn.close()
            json_response(self, 200, stats)
            return

        # 2. Books Search and Catalog
        if path == "/api/books":
            q = query.get("q", [""])[0].strip()
            category = query.get("category", [""])[0].strip()
            department = query.get("department", [""])[0].strip()
            floor = query.get("floor", [""])[0].strip()
            avail_only = query.get("available_only", ["0"])[0].strip()
            sort = query.get("sort", ["rating"])[0].strip()

            sql = "SELECT * FROM books WHERE 1=1"
            params = []

            if q:
                sql += """ AND (
                    title LIKE ? OR 
                    author LIKE ? OR 
                    category LIKE ? OR 
                    department LIKE ? OR 
                    call_no LIKE ? OR 
                    isbn LIKE ? OR 
                    tags LIKE ?
                )"""
                term = f"%{q}%"
                params.extend([term, term, term, term, term, term, term])

            if category:
                sql += " AND category = ?"
                params.append(category)

            if department:
                sql += " AND department = ?"
                params.append(department)

            if floor:
                sql += " AND floor = ?"
                params.append(int(floor))

            if avail_only == "1":
                sql += " AND available_copies > 0"

            if sort == "title":
                sql += " ORDER BY title ASC"
            elif sort == "available":
                sql += " ORDER BY available_copies DESC"
            elif sort == "call_no":
                sql += " ORDER BY call_no ASC"
            else:
                sql += " ORDER BY rating DESC, title ASC"

            cursor.execute(sql, params)
            books = [dict(r) for r in cursor.fetchall()]

            # Also fetch distinct categories and departments for filter pills
            cursor.execute("SELECT DISTINCT category FROM books ORDER BY category")
            categories = [r[0] for r in cursor.fetchall()]
            cursor.execute("SELECT DISTINCT department FROM books ORDER BY department")
            departments = [r[0] for r in cursor.fetchall()]

            conn.close()
            json_response(self, 200, {
                "success": True,
                "count": len(books),
                "books": books,
                "categories": categories,
                "departments": departments
            })
            return

        # 3. Single Book Details
        if path.startswith("/api/books/"):
            try:
                book_id = int(path.split("/api/books/")[1])
            except ValueError:
                conn.close()
                json_response(self, 400, {"error": "Invalid book ID", "success": False})
                return

            cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            if not book:
                conn.close()
                json_response(self, 404, {"error": "Book not found", "success": False})
                return

            book_dict = dict(book)

            # Check reservations queue
            cursor.execute("""
                SELECT * FROM book_reservations 
                WHERE book_id = ? AND status = 'PENDING' 
                ORDER BY queue_position ASC
            """, (book_id,))
            reservations = [dict(r) for r in cursor.fetchall()]
            book_dict["reservation_queue"] = reservations

            # Floor walking path calculation
            floor_name = "Ground Floor (Floor 0)" if book_dict["floor"] == 0 else f"Floor {book_dict['floor']}"
            book_dict["location_breadcrumb"] = f"{floor_name} > {book_dict['aisle']} > {book_dict['rack']} > Shelf Tier {book_dict['shelf_tier']}"
            book_dict["walking_guide"] = [
                f"Enter the Central Library Main Entrance on Ground Floor.",
                f"Take the Central Atrium Staircase or Elevator to {floor_name}.",
                f"Proceed to the School stack area: {book_dict['department']}.",
                f"Navigate to {book_dict['aisle']} and locate {book_dict['rack']}.",
                f"Find Shelf Tier {book_dict['shelf_tier']} (Numbered 1: Bottom to 4: Top). Look for Dewey Call Tag: {book_dict['call_no']}."
            ]

            conn.close()
            json_response(self, 200, {"success": True, "book": book_dict})
            return

        # 4. Seats List & Occupancy
        if path == "/api/seats":
            floor = query.get("floor", [""])[0].strip()
            zone = query.get("zone", [""])[0].strip()
            status = query.get("status", [""])[0].strip()
            has_power = query.get("has_power", [""])[0].strip()

            sql = "SELECT * FROM seats WHERE 1=1"
            params = []

            if floor:
                sql += " AND floor = ?"
                params.append(int(floor))
            if zone:
                sql += " AND zone = ?"
                params.append(zone)
            if status:
                sql += " AND status = ?"
                params.append(status)
            if has_power:
                sql += " AND has_power = ?"
                params.append(int(has_power))

            sql += " ORDER BY floor ASC, seat_number ASC"
            cursor.execute(sql, params)
            seats = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT DISTINCT zone FROM seats ORDER BY zone")
            zones = [r[0] for r in cursor.fetchall()]

            conn.close()
            json_response(self, 200, {
                "success": True,
                "count": len(seats),
                "seats": seats,
                "zones": zones
            })
            return

        # 5. Borrowings List
        if path == "/api/borrowings":
            student_id = query.get("student_id", [""])[0].strip()
            status = query.get("status", [""])[0].strip()

            sql = """
                SELECT b.*, bk.title as book_title, bk.author as book_author, 
                       bk.call_no as book_call_no, bk.isbn as book_isbn,
                       bk.floor as book_floor, bk.aisle as book_aisle,
                       bk.cover_color
                FROM borrowings b
                JOIN books bk ON b.book_id = bk.id
                WHERE 1=1
            """
            params = []

            if student_id:
                sql += " AND b.student_id = ?"
                params.append(student_id)
            if status:
                sql += " AND b.status = ?"
                params.append(status)

            sql += " ORDER BY CASE WHEN b.status = 'OVERDUE' THEN 1 WHEN b.status = 'BORROWED' THEN 2 ELSE 3 END, b.due_date ASC"
            cursor.execute(sql, params)
            borrowings = [dict(r) for r in cursor.fetchall()]

            conn.close()
            json_response(self, 200, {"success": True, "borrowings": borrowings})
            return

        # 6. Notifications List
        if path == "/api/notifications":
            student_id = query.get("student_id", [""])[0].strip()
            sql = "SELECT * FROM notifications WHERE 1=1"
            params = []

            if student_id:
                sql += " AND (student_id = ? OR student_id = 'ALL')"
                params.append(student_id)

            sql += " ORDER BY id DESC"
            cursor.execute(sql, params)
            notifications = [dict(r) for r in cursor.fetchall()]

            conn.close()
            json_response(self, 200, {"success": True, "notifications": notifications})
            return

        # 7. Campus Announcements
        if path == "/api/announcements":
            cursor.execute("SELECT * FROM announcements ORDER BY id DESC")
            announcements = [dict(r) for r in cursor.fetchall()]
            conn.close()
            json_response(self, 200, {"success": True, "announcements": announcements})
            return

        conn.close()
        json_response(self, 404, {"error": "API route not found", "success": False})

    # =========================================================================
    # POST API Endpoints
    # =========================================================================
    def handle_api_post(self, path, data):
        conn = get_db()
        cursor = conn.cursor()
        now = datetime.now()

        # 1. Reserve Book
        if path.startswith("/api/books/") and path.endswith("/reserve"):
            parts = path.split("/")
            book_id = int(parts[3])
            student_id = data.get("student_id", "ASU/2026/AI-104")
            student_name = data.get("student_name", "Ankur Barman")

            cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            if not book:
                conn.close()
                json_response(self, 404, {"error": "Book not found", "success": False})
                return

            book = dict(book)
            if book["available_copies"] > 0:
                # Decrement copy and hold for pickup
                new_avail = book["available_copies"] - 1
                cursor.execute("UPDATE books SET available_copies = ? WHERE id = ?", (new_avail, book_id))
                
                pickup_time = (now + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
                cursor.execute("""
                    INSERT INTO book_reservations (book_id, student_id, student_name, reserve_date, status, queue_position, pickup_deadline)
                    VALUES (?, ?, ?, ?, 'READY_FOR_PICKUP', 0, ?)
                """, (book_id, student_id, student_name, now.strftime("%Y-%m-%d %H:%M"), pickup_time))

                # Add notification
                cursor.execute("""
                    INSERT INTO notifications (student_id, title, message, channel, urgency, timestamp, read, action_type, action_payload)
                    VALUES (?, ?, ?, 'IN_APP', 'SUCCESS', ?, 0, 'VIEW_BOOK', ?)
                """, (
                    student_id,
                    f"📖 Book Ready for Pickup: {book['title']}",
                    f"Your reserved copy of '{book['title']}' is ready at Central Circulation Desk (Ground Floor). Please collect before {pickup_time}.",
                    now.strftime("%Y-%m-%d %H:%M"),
                    json.dumps({"book_id": book_id})
                ))

                conn.commit()
                conn.close()
                json_response(self, 200, {
                    "success": True,
                    "message": f"Copy held for pickup at Circulation Desk until {pickup_time}!",
                    "status": "READY_FOR_PICKUP",
                    "available_copies": new_avail
                })
                return
            else:
                # Waitlist queue
                cursor.execute("SELECT COUNT(*) FROM book_reservations WHERE book_id = ? AND status = 'PENDING'", (book_id,))
                q_pos = cursor.fetchone()[0] + 1

                cursor.execute("""
                    INSERT INTO book_reservations (book_id, student_id, student_name, reserve_date, status, queue_position)
                    VALUES (?, ?, ?, ?, 'PENDING', ?)
                """, (book_id, student_id, student_name, now.strftime("%Y-%m-%d %H:%M"), q_pos))

                cursor.execute("""
                    INSERT INTO notifications (student_id, title, message, channel, urgency, timestamp, read, action_type, action_payload)
                    VALUES (?, ?, ?, 'IN_APP', 'NORMAL', ?, 0, 'VIEW_BOOK', ?)
                """, (
                    student_id,
                    f"⏳ Waitlist Confirmed: #{q_pos} in queue",
                    f"All copies of '{book['title']}' are currently issued. You are position #{q_pos} in line. We will alert you immediately when returned.",
                    now.strftime("%Y-%m-%d %H:%M"),
                    json.dumps({"book_id": book_id})
                ))

                conn.commit()
                conn.close()
                json_response(self, 200, {
                    "success": True,
                    "message": f"Added to waitlist queue at position #{q_pos}.",
                    "status": "WAITLISTED",
                    "queue_position": q_pos
                })
                return

        # 2. Reserve Seat
        if path.startswith("/api/seats/") and path.endswith("/reserve"):
            parts = path.split("/")
            seat_id = int(parts[3])
            student_id = data.get("student_id", "ASU/2026/AI-104")
            student_name = data.get("student_name", "Ankur Barman")
            duration_minutes = int(data.get("duration_minutes", 120))

            cursor.execute("SELECT * FROM seats WHERE id = ?", (seat_id,))
            seat = cursor.fetchone()
            if not seat:
                conn.close()
                json_response(self, 404, {"error": "Seat not found", "success": False})
                return

            seat = dict(seat)
            if seat["status"] != "AVAILABLE":
                conn.close()
                json_response(self, 400, {"error": f"Seat is currently {seat['status']}", "success": False})
                return

            # Check-in deadline is 15 mins from now
            grace_period_until = (now + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M")
            checkin_code = f"CHK-ASU-{seat['seat_number'].replace('-', '')}"

            cursor.execute("""
                UPDATE seats 
                SET status = 'RESERVED',
                    current_student_id = ?,
                    current_student_name = ?,
                    reserved_until = ?,
                    checked_in = 0,
                    checkin_code = ?
                WHERE id = ?
            """, (student_id, student_name, grace_period_until, checkin_code, seat_id))

            # Send in-app notification & simulated SMS
            cursor.execute("""
                INSERT INTO notifications (student_id, title, message, channel, urgency, timestamp, read, action_type, action_payload)
                VALUES (?, ?, ?, 'IN_APP', 'NORMAL', ?, 0, 'CHECKIN_SEAT', ?)
            """, (
                student_id,
                f"🪑 Seat Reserved: {seat['seat_number']} ({seat['zone']})",
                f"Your desk {seat['seat_number']} is held for 15 minutes until {grace_period_until}. Use Check-In Code: '{checkin_code}' upon arrival.",
                now.strftime("%Y-%m-%d %H:%M"),
                json.dumps({"seat_id": seat_id, "checkin_code": checkin_code})
            ))

            conn.commit()
            conn.close()
            json_response(self, 200, {
                "success": True,
                "message": f"Seat {seat['seat_number']} reserved! Please check in within 15 minutes.",
                "seat_number": seat["seat_number"],
                "checkin_code": checkin_code,
                "grace_period_until": grace_period_until,
                "duration_minutes": duration_minutes
            })
            return

        # 3. Check-In to Seat
        if path.startswith("/api/seats/") and path.endswith("/checkin"):
            parts = path.split("/")
            seat_id = int(parts[3])
            student_id = data.get("student_id", "ASU/2026/AI-104")
            code = data.get("checkin_code", "").strip()

            cursor.execute("SELECT * FROM seats WHERE id = ?", (seat_id,))
            seat = cursor.fetchone()
            if not seat:
                conn.close()
                json_response(self, 404, {"error": "Seat not found", "success": False})
                return

            seat = dict(seat)
            if seat["status"] not in ("RESERVED", "OCCUPIED"):
                conn.close()
                json_response(self, 400, {"error": "Seat is not currently reserved", "success": False})
                return

            if code and code != seat["checkin_code"]:
                conn.close()
                json_response(self, 400, {"error": "Invalid Check-In Code", "success": False})
                return

            # Active study session for 2 hours
            session_end = (now + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            cursor.execute("""
                UPDATE seats
                SET status = 'OCCUPIED',
                    checked_in = 1,
                    reserved_until = ?
                WHERE id = ?
            """, (session_end, seat_id))

            conn.commit()
            conn.close()
            json_response(self, 200, {
                "success": True,
                "message": f"Check-In Confirmed for Seat {seat['seat_number']}. Happy Studying!",
                "session_until": session_end
            })
            return

        # 4. Release / Vacate Seat
        if path.startswith("/api/seats/") and path.endswith("/release"):
            parts = path.split("/")
            seat_id = int(parts[3])

            cursor.execute("SELECT * FROM seats WHERE id = ?", (seat_id,))
            seat = cursor.fetchone()
            if not seat:
                conn.close()
                json_response(self, 404, {"error": "Seat not found", "success": False})
                return

            seat_number = seat["seat_number"]
            cursor.execute("""
                UPDATE seats
                SET status = 'AVAILABLE',
                    current_student_id = NULL,
                    current_student_name = NULL,
                    reserved_until = NULL,
                    checked_in = 0,
                    checkin_code = NULL
                WHERE id = ?
            """, (seat_id,))

            conn.commit()
            conn.close()
            json_response(self, 200, {
                "success": True,
                "message": f"Seat {seat_number} is now released and marked AVAILABLE."
            })
            return

        # 5. Renew Borrowed Book
        if path.startswith("/api/borrowings/") and path.endswith("/renew"):
            parts = path.split("/")
            borrowing_id = int(parts[3])

            cursor.execute("""
                SELECT b.*, bk.title 
                FROM borrowings b 
                JOIN books bk ON b.book_id = bk.id 
                WHERE b.id = ?
            """, (borrowing_id,))
            borrowing = cursor.fetchone()
            if not borrowing:
                conn.close()
                json_response(self, 404, {"error": "Borrowing record not found", "success": False})
                return

            borrowing = dict(borrowing)
            if borrowing["renewal_count"] >= 2:
                conn.close()
                json_response(self, 400, {
                    "error": "Maximum renewal limit (2 extensions) reached. Please return the book to allow other students to borrow.",
                    "success": False
                })
                return

            # Check if another student has waitlisted this book
            cursor.execute("""
                SELECT COUNT(*) FROM book_reservations 
                WHERE book_id = ? AND status = 'PENDING'
            """, (borrowing["book_id"],))
            waitlist_count = cursor.fetchone()[0]

            if waitlist_count > 0:
                conn.close()
                json_response(self, 400, {
                    "error": f"Cannot renew: {waitlist_count} student(s) are waitlisted for this book. Please return by due date.",
                    "success": False
                })
                return

            # Extend due date by 14 days
            current_due = datetime.strptime(borrowing["due_date"], "%Y-%m-%d")
            new_due = (max(now, current_due) + timedelta(days=14)).strftime("%Y-%m-%d")
            new_count = borrowing["renewal_count"] + 1

            cursor.execute("""
                UPDATE borrowings
                SET due_date = ?,
                    renewal_count = ?,
                    status = 'BORROWED',
                    fine_amount = 0.0
                WHERE id = ?
            """, (new_due, new_count, borrowing_id))

            cursor.execute("""
                INSERT INTO notifications (student_id, title, message, channel, urgency, timestamp, read)
                VALUES (?, ?, ?, 'IN_APP', 'SUCCESS', ?, 0)
            """, (
                borrowing["student_id"],
                f"✅ Book Renewed: {borrowing['title']}",
                f"Successfully extended due date to {new_due}. Renewal count: {new_count}/2.",
                now.strftime("%Y-%m-%d %H:%M")
            ))

            conn.commit()
            conn.close()
            json_response(self, 200, {
                "success": True,
                "message": f"Book renewed successfully! New due date: {new_due}",
                "new_due_date": new_due,
                "renewal_count": new_count
            })
            return

        # 6. Automated Due-Date Reminder Dispatcher
        if path == "/api/notifications/dispatch-reminders":
            # Scan all borrowings
            cursor.execute("""
                SELECT b.*, bk.title, bk.author 
                FROM borrowings b
                JOIN books bk ON b.book_id = bk.id
                WHERE b.status IN ('BORROWED', 'OVERDUE')
            """)
            active_loans = [dict(r) for r in cursor.fetchall()]

            dispatched_count = 0
            for loan in active_loans:
                due_dt = datetime.strptime(loan["due_date"], "%Y-%m-%d")
                delta_days = (due_dt.date() - now.date()).days

                if delta_days < 0:
                    # Overdue alert (SMS + Email)
                    fine = abs(delta_days) * 2.0
                    cursor.execute("""
                        INSERT INTO notifications (student_id, title, message, channel, urgency, timestamp, read, action_type, action_payload)
                        VALUES (?, ?, ?, 'SMS', 'OVERDUE', ?, 0, 'RENEW_BOOK', ?)
                    """, (
                        loan["student_id"],
                        f"🚨 ASU LIBRARY OVERDUE ALERT: '{loan['title']}'",
                        f"Your book is {abs(delta_days)} days overdue. Fine accumulated: ₹{fine:.2f}. Please return immediately to avoid library card suspension.",
                        now.strftime("%Y-%m-%d %H:%M"),
                        json.dumps({"borrowing_id": loan["id"]})
                    ))
                    cursor.execute("""
                        INSERT INTO notifications (student_id, title, message, channel, urgency, timestamp, read, action_type, action_payload)
                        VALUES (?, ?, ?, 'EMAIL', 'OVERDUE', ?, 0, 'RENEW_BOOK', ?)
                    """, (
                        loan["student_id"],
                        f"[URGENT] Overdue Notice: Assam Skill University Central Library",
                        f"Dear {loan['student_name']},\n\nThis is an automated notice that '{loan['title']}' was due on {loan['due_date']}.\n\nCurrent Overdue Days: {abs(delta_days)}\nAccrued Penalty: ₹{fine:.2f}\n\nPlease visit the Circulation Desk on Ground Floor to clear.",
                        now.strftime("%Y-%m-%d %H:%M"),
                        json.dumps({"borrowing_id": loan["id"]})
                    ))
                    dispatched_count += 2

                elif delta_days <= 3:
                    # Approaching due date reminder (Email + In-App)
                    cursor.execute("""
                        INSERT INTO notifications (student_id, title, message, channel, urgency, timestamp, read, action_type, action_payload)
                        VALUES (?, ?, ?, 'EMAIL', 'URGENT', ?, 0, 'RENEW_BOOK', ?)
                    """, (
                        loan["student_id"],
                        f"⏰ Friendly Reminder: '{loan['title']}' Due in {delta_days} Days",
                        f"Dear {loan['student_name']}, your book '{loan['title']}' is due on {loan['due_date']}. You can renew online via the ASU Smart Library portal if eligible.",
                        now.strftime("%Y-%m-%d %H:%M"),
                        json.dumps({"borrowing_id": loan["id"]})
                    ))
                    cursor.execute("""
                        INSERT INTO notifications (student_id, title, message, channel, urgency, timestamp, read, action_type, action_payload)
                        VALUES (?, ?, ?, 'SMS', 'NORMAL', ?, 0, 'RENEW_BOOK', ?)
                    """, (
                        loan["student_id"],
                        f"ASU Central Library Reminder",
                        f"Book '{loan['title']}' due in {delta_days} day(s) on {loan['due_date']}. Renew or return to avoid ₹2/day fine.",
                        now.strftime("%Y-%m-%d %H:%M"),
                        json.dumps({"borrowing_id": loan["id"]})
                    ))
                    dispatched_count += 2

            conn.commit()
            conn.close()
            json_response(self, 200, {
                "success": True,
                "message": f"Dispatched {dispatched_count} automated multi-channel reminders (SMS & Email).",
                "dispatched_count": dispatched_count
            })
            return

        # 7. Admin Issue Book (Circulation Desk)
        if path == "/api/admin/issue-book":
            book_id = data.get("book_id")
            student_id = data.get("student_id", "").strip()
            student_name = data.get("student_name", "").strip()
            student_dept = data.get("student_dept", "School of Computing & AI")
            days = int(data.get("days", 14))

            if not book_id or not student_id or not student_name:
                conn.close()
                json_response(self, 400, {"error": "Missing book_id, student_id or student_name", "success": False})
                return

            cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            if not book or book["available_copies"] <= 0:
                conn.close()
                json_response(self, 400, {"error": "No copies available to issue", "success": False})
                return

            issue_date = now.strftime("%Y-%m-%d")
            due_date = (now + timedelta(days=days)).strftime("%Y-%m-%d")

            cursor.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = ?", (book_id,))
            cursor.execute("""
                INSERT INTO borrowings (book_id, student_id, student_name, student_dept, issue_date, due_date, status)
                VALUES (?, ?, ?, ?, ?, ?, 'BORROWED')
            """, (book_id, student_id, student_name, student_dept, issue_date, due_date))

            cursor.execute("""
                INSERT INTO notifications (student_id, title, message, channel, urgency, timestamp, read)
                VALUES (?, ?, ?, 'IN_APP', 'SUCCESS', ?, 0)
            """, (
                student_id,
                f"📚 Book Issued: {book['title']}",
                f"Issued on {issue_date}. Due date is {due_date}. Call No: {book['call_no']}.",
                now.strftime("%Y-%m-%d %H:%M")
            ))

            conn.commit()
            conn.close()
            json_response(self, 200, {
                "success": True,
                "message": f"Book '{book['title']}' issued to {student_name} ({student_id}). Due: {due_date}",
                "due_date": due_date
            })
            return

        # 8. Admin Return Book
        if path == "/api/admin/return-book":
            borrowing_id = data.get("borrowing_id")
            if not borrowing_id:
                conn.close()
                json_response(self, 400, {"error": "Missing borrowing_id", "success": False})
                return

            cursor.execute("""
                SELECT b.*, bk.title, bk.id as book_id
                FROM borrowings b
                JOIN books bk ON b.book_id = bk.id
                WHERE b.id = ?
            """, (borrowing_id,))
            loan = cursor.fetchone()
            if not loan:
                conn.close()
                json_response(self, 404, {"error": "Borrowing not found", "success": False})
                return

            return_date = now.strftime("%Y-%m-%d")
            due_date = datetime.strptime(loan["due_date"], "%Y-%m-%d")
            delta_days = (now.date() - due_date.date()).days
            fine = max(0.0, float(delta_days * 2.0)) if delta_days > 0 else 0.0

            cursor.execute("""
                UPDATE borrowings 
                SET status = 'RETURNED',
                    return_date = ?,
                    fine_amount = ?
                WHERE id = ?
            """, (return_date, fine, borrowing_id))

            cursor.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id = ?", (loan["book_id"],))

            conn.commit()
            conn.close()
            json_response(self, 200, {
                "success": True,
                "message": f"Book '{loan['title']}' returned successfully! Fine settled: ₹{fine:.2f}",
                "fine_amount": fine
            })
            return

        # 9. Admin Add Book to Shelf Catalog
        if path == "/api/admin/add-book":
            try:
                cursor.execute("""
                    INSERT INTO books (
                        isbn, title, author, category, department, call_no, edition, publisher, year,
                        floor, aisle, rack, shelf_tier, total_copies, available_copies, summary, tags, cover_color
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get("isbn", f"978-ASU-{int(now.timestamp())}"),
                    data["title"],
                    data["author"],
                    data.get("category", "Skill Development"),
                    data.get("department", "School of Computing & AI"),
                    data.get("call_no", "005.0 ASU"),
                    data.get("edition", "1st Edition"),
                    data.get("publisher", "ASU Press"),
                    int(data.get("year", 2024)),
                    int(data.get("floor", 1)),
                    data.get("aisle", "Aisle B-1"),
                    data.get("rack", "Rack R-01"),
                    int(data.get("shelf_tier", 2)),
                    int(data.get("copies", 3)),
                    int(data.get("copies", 3)),
                    data.get("summary", "Cataloged in Central Library collection."),
                    data.get("tags", "Reference, Engineering"),
                    data.get("cover_color", "#0f766e")
                ))
                new_id = cursor.lastrowid
                conn.commit()
                conn.close()
                json_response(self, 200, {"success": True, "message": "New book cataloged & mapped to shelf!", "book_id": new_id})
                return
            except Exception as e:
                conn.close()
                json_response(self, 400, {"error": str(e), "success": False})
                return

        # 10. Admin Broadcast Announcement
        if path == "/api/admin/broadcast":
            title = data.get("title", "").strip()
            message = data.get("message", "").strip()
            priority = data.get("priority", "INFO")

            if not title or not message:
                conn.close()
                json_response(self, 400, {"error": "Missing title or message", "success": False})
                return

            cursor.execute("""
                INSERT INTO announcements (title, message, priority, timestamp)
                VALUES (?, ?, ?, ?)
            """, (title, message, priority, now.strftime("%Y-%m-%d %H:%M")))

            conn.commit()
            conn.close()
            json_response(self, 200, {"success": True, "message": "Campus library announcement broadcasted!"})
            return

        # 11. Re-seed database
        if path == "/api/seed":
            conn.close()
            seed_data(force=True)
            json_response(self, 200, {"success": True, "message": "Database refreshed to initial state."})
            return

        conn.close()
        json_response(self, 404, {"error": "API route not found", "success": False})

def run_server(port=PORT, host=None):
    init_db()
    seed_data(force=False)
    if host is None:
        # Bind to 0.0.0.0 when deployed to cloud platforms (Render, Railway, Heroku)
        host = "0.0.0.0" if (os.environ.get("PORT") or os.environ.get("RENDER")) else "127.0.0.1"
    server_address = (host, port)
    httpd = socketserver.ThreadingTCPServer(server_address, LibraryRequestHandler)
    print(f"================================================================")
    print(f" Assam Skill University Central Library - Smart Portal Running")
    print(f" Host: {host} | Port: {port}")
    print(f" URL: http://{host}:{port}/")
    print(f" Static Directory: {STATIC_DIR}")
    print(f"================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    env_port = os.environ.get("PORT")
    p = int(env_port) if env_port else (int(sys.argv[1]) if len(sys.argv) > 1 else PORT)
    run_server(p)
