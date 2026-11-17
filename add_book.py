"""
Assam Skill University Central Library - Add Book Utility
CLI script to insert new academic and vocational books directly into the SQLite database.

Usage:
  1. Interactive mode:
     python add_book.py
  2. Direct programmatic usage:
     from add_book import insert_book
     insert_book(title="...", author="...", ...)
"""

import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")

def insert_book(
    title: str,
    author: str,
    category: str = "Computing & Engineering",
    department: str = "School of Computing & AI",
    call_no: str = "005.0 ASU",
    floor: int = 1,
    aisle: str = "Aisle B-2",
    rack: str = "Rack R-02",
    shelf_tier: int = 2,
    copies: int = 4,
    isbn: str = None,
    publisher: str = "ASU Academic Press",
    year: int = 2024,
    edition: str = "1st Edition",
    summary: str = "Standard reference textbook cataloged at Assam Skill University Central Library.",
    tags: str = "Engineering, Skill, Reference",
    cover_color: str = "#0f766e",
    rating: float = 4.8
) -> int:
    """Inserts a new book into the library database and maps its shelf coordinates."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not isbn:
        import time
        isbn = f"978-ASU-{int(time.time())}"

    cursor.execute("""
        INSERT INTO books (
            isbn, title, author, category, department, call_no, edition, publisher, year,
            floor, aisle, rack, shelf_tier, total_copies, available_copies, summary, tags,
            cover_color, rating
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        isbn, title, author, category, department, call_no, edition, publisher, year,
        floor, aisle, rack, shelf_tier, copies, copies, summary, tags,
        cover_color, rating
    ))

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def main():
    print("=" * 65)
    print(" Assam Skill University Central Library - New Book Cataloging")
    print("=" * 65)

    try:
        title = input("Book Title: ").strip()
        if not title:
            print("Error: Book title cannot be empty.")
            return

        author = input("Author(s): ").strip() or "Various Authors"
        category = input("Category [Artificial Intelligence]: ").strip() or "Artificial Intelligence"
        dept = input("Department [School of Computing & AI]: ").strip() or "School of Computing & AI"
        call_no = input("Dewey Call No [006.3 ASU]: ").strip() or "006.3 ASU"
        
        floor_input = input("Floor (0, 1, or 2) [1]: ").strip() or "1"
        floor = int(floor_input)
        
        aisle = input("Aisle [Aisle B-2]: ").strip() or "Aisle B-2"
        rack = input("Rack [Rack R-01]: ").strip() or "Rack R-01"
        
        tier_input = input("Shelf Tier (1: Bottom, 2: Chest, 3: Eye, 4: Top) [2]: ").strip() or "2"
        shelf_tier = int(tier_input)
        
        copies_input = input("Number of Copies [4]: ").strip() or "4"
        copies = int(copies_input)

        summary = input("Short Summary (optional): ").strip()
        if not summary:
            summary = f"Curriculum reference material for {dept} students."

        book_id = insert_book(
            title=title,
            author=author,
            category=category,
            department=dept,
            call_no=call_no,
            floor=floor,
            aisle=aisle,
            rack=rack,
            shelf_tier=shelf_tier,
            copies=copies,
            summary=summary
        )

        print("\n" + "=" * 65)
        print(f" SUCCESS: Book registered successfully with Database ID #{book_id}!")
        print(f" Location: Floor {floor} > {aisle} > {rack} > Tier {shelf_tier}")
        print(f" Total Stock: {copies} available copies")
        print("=" * 65)

    except KeyboardInterrupt:
        print("\nOperation cancelled.")
    except Exception as e:
        print(f"\nFailed to insert book: {e}")

if __name__ == "__main__":
    main()
