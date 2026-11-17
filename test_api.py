"""
Assam Skill University Central Library - Automated Backend Test Suite
Directly tests database operations, queries, and business logic.
"""

import unittest
from datetime import datetime, timedelta
import json
import sqlite3
import os

from database import init_db, seed_data, get_db

class TestSmartLibraryBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        seed_data(force=True)

    def setUp(self):
        self.conn = get_db()
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_books_exist(self):
        self.cursor.execute("SELECT COUNT(*) FROM books")
        count = self.cursor.fetchone()[0]
        self.assertGreaterEqual(count, 20, "Should have seeded at least 20 academic skill books")

    def test_seats_exist_and_counts(self):
        self.cursor.execute("SELECT COUNT(*) FROM seats")
        count = self.cursor.fetchone()[0]
        self.assertEqual(count, 48, "Should have seeded exactly 48 seats across Floor 1 and Floor 2")

    def test_search_by_keyword(self):
        q = "%Robotics%"
        self.cursor.execute("""
            SELECT title, aisle, rack FROM books 
            WHERE title LIKE ? OR category LIKE ? OR tags LIKE ?
        """, (q, q, q))
        rows = self.cursor.fetchall()
        self.assertGreater(len(rows), 0, "Should find robotics titles")

    def test_overdue_fine_calculation(self):
        # Find Ankur's overdue book
        self.cursor.execute("""
            SELECT b.*, bk.title 
            FROM borrowings b
            JOIN books bk ON b.book_id = bk.id
            WHERE b.student_id = 'ASU/2026/AI-104' AND b.status = 'OVERDUE'
        """)
        overdue = self.cursor.fetchone()
        self.assertIsNotNone(overdue, "Should have a pre-seeded overdue loan for demo")
        self.assertGreater(overdue["fine_amount"], 0, "Fine amount should be positive for overdue book")

    def test_seat_reservation_flow(self):
        # Find an available seat
        self.cursor.execute("SELECT id, seat_number FROM seats WHERE status = 'AVAILABLE' LIMIT 1")
        seat = self.cursor.fetchone()
        self.assertIsNotNone(seat)
        seat_id = seat["id"]

        # Reserve it
        now = datetime.now()
        grace = (now + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M")
        code = f"CHK-TEST-{seat['seat_number']}"
        self.cursor.execute("""
            UPDATE seats 
            SET status = 'RESERVED',
                current_student_id = 'ASU/TEST/001',
                current_student_name = 'Test Student',
                reserved_until = ?,
                checked_in = 0,
                checkin_code = ?
            WHERE id = ?
        """, (grace, code, seat_id))
        self.conn.commit()

        # Verify reserved
        self.cursor.execute("SELECT status, checkin_code FROM seats WHERE id = ?", (seat_id,))
        updated = self.cursor.fetchone()
        self.assertEqual(updated["status"], "RESERVED")
        self.assertEqual(updated["checkin_code"], code)

        # Check in
        self.cursor.execute("""
            UPDATE seats
            SET status = 'OCCUPIED', checked_in = 1
            WHERE id = ?
        """, (seat_id,))
        self.conn.commit()

        self.cursor.execute("SELECT status, checked_in FROM seats WHERE id = ?", (seat_id,))
        checked = self.cursor.fetchone()
        self.assertEqual(checked["status"], "OCCUPIED")
        self.assertEqual(checked["checked_in"], 1)

        # Release seat
        self.cursor.execute("""
            UPDATE seats
            SET status = 'AVAILABLE', current_student_id = NULL, current_student_name = NULL,
                reserved_until = NULL, checked_in = 0, checkin_code = NULL
            WHERE id = ?
        """, (seat_id,))
        self.conn.commit()

        self.cursor.execute("SELECT status FROM seats WHERE id = ?", (seat_id,))
        released = self.cursor.fetchone()
        self.assertEqual(released["status"], "AVAILABLE")

    def test_due_date_alerts(self):
        self.cursor.execute("SELECT COUNT(*) FROM notifications WHERE channel IN ('SMS', 'EMAIL', 'IN_APP')")
        alerts_count = self.cursor.fetchone()[0]
        self.assertGreater(alerts_count, 0, "Should have pre-seeded reminder alerts")

    def test_api_stats_endpoint(self):
        from server import LibraryRequestHandler
        import io

        class DummyHandler(LibraryRequestHandler):
            def __init__(self):
                self.headers = {}
                self.rfile = io.BytesIO()
                self.wfile = io.BytesIO()

            def send_response(self, code):
                self.response_code = code

            def send_header(self, k, v):
                pass

            def end_headers(self):
                pass

        # Test GET /api/stats
        handler = DummyHandler()
        handler.handle_api_get("/api/stats", {})
        self.assertEqual(handler.response_code, 200)
        output = json.loads(handler.wfile.getvalue().decode())
        self.assertTrue(output["success"])
        self.assertIn("total_titles", output)
        self.assertEqual(output["total_seats"], 48)

        # Test GET /api/books with filter
        handler = DummyHandler()
        handler.handle_api_get("/api/books", {"q": ["Robotics"]})
        self.assertEqual(handler.response_code, 200)
        b_output = json.loads(handler.wfile.getvalue().decode())
        self.assertTrue(b_output["success"])
        self.assertGreater(len(b_output["books"]), 0)

        # Test GET /api/seats
        handler = DummyHandler()
        handler.handle_api_get("/api/seats", {"floor": ["1"]})
        self.assertEqual(handler.response_code, 200)
        s_output = json.loads(handler.wfile.getvalue().decode())
        self.assertTrue(s_output["success"])
        self.assertEqual(len(s_output["seats"]), 24)

if __name__ == "__main__":
    unittest.main()
