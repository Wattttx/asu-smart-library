"""
Assam Skill University Central Library - Database Engine & Initial Data Seeder
Handles SQLite connection, schema definition, and comprehensive pre-seeded data
for books, seats, borrowings, reservations, and notification alerts.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "library.db")

def get_db():
    target_path = DB_PATH
    # In serverless environments like Vercel or AWS Lambda, the root filesystem is read-only.
    # We copy the seeded database to /tmp so write transactions (bookings, loans) succeed.
    if os.environ.get("VERCEL") or not os.access(os.path.dirname(DB_PATH) or ".", os.W_OK):
        tmp_db = "/tmp/library.db"
        if not os.path.exists(tmp_db):
            import shutil
            if os.path.exists(DB_PATH):
                shutil.copyfile(DB_PATH, tmp_db)
            else:
                # Initialize fresh in /tmp if template missing
                target_path = tmp_db
                conn = sqlite3.connect(tmp_db)
                conn.row_factory = sqlite3.Row
                conn.close()
                init_db_path(tmp_db)
                seed_data_path(tmp_db, force=True)
                return sqlite3.connect(tmp_db)
        target_path = tmp_db

    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Books Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isbn TEXT UNIQUE,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        category TEXT NOT NULL,
        department TEXT NOT NULL,
        call_no TEXT NOT NULL,
        edition TEXT,
        publisher TEXT,
        year INTEGER,
        floor INTEGER NOT NULL,
        aisle TEXT NOT NULL,
        rack TEXT NOT NULL,
        shelf_tier INTEGER NOT NULL,
        total_copies INTEGER NOT NULL,
        available_copies INTEGER NOT NULL,
        summary TEXT,
        tags TEXT,
        cover_color TEXT DEFAULT '#0f766e',
        rating REAL DEFAULT 4.5
    )
    """)

    # Seats Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS seats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        seat_number TEXT UNIQUE NOT NULL,
        floor INTEGER NOT NULL,
        zone TEXT NOT NULL,
        seat_type TEXT NOT NULL,
        has_power BOOLEAN DEFAULT 1,
        has_lan BOOLEAN DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'AVAILABLE', -- AVAILABLE, OCCUPIED, RESERVED, MAINTENANCE
        current_student_id TEXT,
        current_student_name TEXT,
        reserved_until TEXT,
        checked_in BOOLEAN DEFAULT 0,
        checkin_code TEXT,
        pos_x INTEGER,
        pos_y INTEGER
    )
    """)

    # Borrowings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS borrowings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        student_dept TEXT NOT NULL,
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        return_date TEXT,
        renewal_count INTEGER DEFAULT 0,
        fine_amount REAL DEFAULT 0.0,
        status TEXT NOT NULL DEFAULT 'BORROWED', -- BORROWED, RETURNED, OVERDUE
        FOREIGN KEY (book_id) REFERENCES books (id)
    )
    """)

    # Book Reservations / Holds Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS book_reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        student_id TEXT NOT NULL,
        student_name TEXT NOT NULL,
        reserve_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, READY_FOR_PICKUP, CANCELLED, FULFILLED
        queue_position INTEGER DEFAULT 1,
        pickup_deadline TEXT,
        FOREIGN KEY (book_id) REFERENCES books (id)
    )
    """)

    # Notification & Due-Date Reminders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        channel TEXT NOT NULL, -- IN_APP, EMAIL, SMS, WHATSAPP
        urgency TEXT NOT NULL DEFAULT 'NORMAL', -- NORMAL, URGENT, OVERDUE, SUCCESS
        timestamp TEXT NOT NULL,
        read BOOLEAN DEFAULT 0,
        action_type TEXT,
        action_payload TEXT
    )
    """)

    # Announcements Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        priority TEXT DEFAULT 'INFO', -- INFO, WARNING, CRITICAL
        timestamp TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def seed_data(force=False):
    conn = get_db()
    cursor = conn.cursor()

    if not force:
        cursor.execute("SELECT COUNT(*) FROM books")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

    # Clear existing tables if force seeding
    cursor.execute("DELETE FROM books")
    cursor.execute("DELETE FROM seats")
    cursor.execute("DELETE FROM borrowings")
    cursor.execute("DELETE FROM book_reservations")
    cursor.execute("DELETE FROM notifications")
    cursor.execute("DELETE FROM announcements")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('books', 'seats', 'borrowings', 'book_reservations', 'notifications', 'announcements')")

    now = datetime.now()

    # Pre-seeded Books (Tailored to Assam Skill University's Core Schools & Vocations)
    books_data = [
        # School of Computing & AI (Floor 1, Aisle B)
        (
            "978-1617294433", "Deep Learning with Python", "François Chollet",
            "Artificial Intelligence", "School of Computing & AI", "006.31 CHO",
            "2nd Edition", "Manning Publications", 2021,
            1, "Aisle B-1", "Rack R-02", 3, 5, 2,
            "Written by Keras creator François Chollet, this book introduces the fields of deep learning using Python and the powerful Keras library.",
            "AI, Deep Learning, Neural Networks, Python, Computer Science", "#0284c7", 4.9
        ),
        (
            "978-0134610993", "Artificial Intelligence: A Modern Approach", "Stuart Russell, Peter Norvig",
            "Artificial Intelligence", "School of Computing & AI", "006.3 RUS",
            "4th Edition", "Pearson Education", 2020,
            1, "Aisle B-1", "Rack R-01", 2, 8, 4,
            "The leading reference text in Artificial Intelligence, covering search algorithms, knowledge representation, probabilistic reasoning, and machine learning.",
            "AI, Machine Learning, Algorithms, Logic, Robotics", "#1e40af", 4.8
        ),
        (
            "978-1492032649", "Designing Data-Intensive Applications", "Martin Kleppmann",
            "Cloud & Data Engineering", "School of Computing & AI", "005.74 KLE",
            "1st Edition", "O'Reilly Media", 2017,
            1, "Aisle B-2", "Rack R-01", 2, 6, 3,
            "The definitive guide to the principles and tradeoffs of data systems, distributed databases, stream processing, and scalable architectures.",
            "Distributed Systems, Big Data, SQL, NoSQL, Kafka, Scalability", "#d97706", 4.9
        ),
        (
            "978-1098125974", "Hands-On Machine Learning with Scikit-Learn, Keras & TensorFlow", "Aurélien Géron",
            "Machine Learning", "School of Computing & AI", "006.31 GER",
            "3rd Edition", "O'Reilly Media", 2022,
            1, "Aisle B-2", "Rack R-02", 4, 7, 1,
            "Through a series of recent breakthroughs, deep learning has boosted the entire field of machine learning. Covers end-to-end ML projects.",
            "Scikit-Learn, TensorFlow, PyTorch, Deep Learning, MLOps", "#10b981", 4.9
        ),
        (
            "978-0262033848", "Introduction to Algorithms (CLRS)", "Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein",
            "Computer Science & Algorithms", "School of Computing & AI", "005.1 COR",
            "4th Edition", "MIT Press", 2022,
            1, "Aisle B-3", "Rack R-02", 2, 10, 5,
            "The world-renowned algorithmic standard covering dynamic programming, greedy algorithms, graph algorithms, NP-completeness, and data structures.",
            "Algorithms, Data Structures, Complexity, Graph Theory", "#4338ca", 4.8
        ),
        (
            "978-1118531648", "Computer Vision: Algorithms and Applications", "Richard Szeliski",
            "Computer Vision", "School of Computing & AI", "006.37 SZE",
            "2nd Edition", "Springer", 2022,
            1, "Aisle B-1", "Rack R-03", 1, 4, 2,
            "Comprehensive text on 3D reconstruction, feature matching, image segmentation, and deep learning-based vision systems.",
            "Computer Vision, Image Processing, OpenCV, Spatial AI", "#6366f1", 4.7
        ),
        (
            "978-1492094043", "Natural Language Processing with Transformers", "Lewis Tunstall, Leandro von Werra, Thomas Wolf",
            "Generative AI & NLP", "School of Computing & AI", "006.35 TUN",
            "1st Edition", "O'Reilly Media", 2022,
            1, "Aisle B-2", "Rack R-03", 2, 5, 0, # Currently all loaned out to test reservation queue!
            "Build and train transformer models with Hugging Face, from BERT to GPT-style LLMs for real-world production tasks.",
            "NLP, Transformers, Hugging Face, LLMs, Text Classification", "#8b5cf6", 4.9
        ),
        (
            "978-0133591620", "Modern Operating Systems", "Andrew S. Tanenbaum, Herbert Bos",
            "Systems & Architecture", "School of Computing & AI", "005.43 TAN",
            "4th Edition", "Pearson", 2014,
            1, "Aisle B-3", "Rack R-01", 1, 6, 4,
            "Covers virtual memory, file systems, security, multiprocessing, virtualization, and modern Android/Linux operating design.",
            "OS, Kernel, Linux, Memory Management, Concurrency", "#0f766e", 4.6
        ),

        # School of Advanced Manufacturing & Robotics (Floor 1, Aisle A)
        (
            "978-0133489798", "Introduction to Robotics: Mechanics and Control", "John J. Craig",
            "Robotics Engineering", "School of Manufacturing & Robotics", "629.892 CRA",
            "4th Edition", "Pearson", 2018,
            1, "Aisle A-1", "Rack R-01", 3, 6, 2,
            "Introduces kinematics, inverse kinematics, dynamics, trajectory generation, and robot control systems with MATLAB examples.",
            "Robotics, Kinematics, Dynamics, Manipulators, Motion Control", "#b45309", 4.8
        ),
        (
            "978-0471649908", "Robot Modeling and Control", "Mark W. Spong, Seth Hutchinson, M. Vidyasagar",
            "Robotics & Control", "School of Manufacturing & Robotics", "629.892 SPO",
            "2nd Edition", "Wiley", 2020,
            1, "Aisle A-1", "Rack R-02", 2, 5, 3,
            "Rigorous treatment of robotic manipulators, control architecture, feedback linearization, and force control.",
            "Robotics, Control Theory, Actuators, Sensors, Feedback", "#b91c1c", 4.7
        ),
        (
            "978-1292076683", "Mechatronics: Electronic Control Systems in Mechanical Engineering", "W. Bolton",
            "Mechatronics", "School of Manufacturing & Robotics", "621.3 BOL",
            "7th Edition", "Pearson Education", 2019,
            1, "Aisle A-2", "Rack R-01", 2, 7, 4,
            "Integrates mechanical, electronic, control systems, and computer engineering for automated smart machines and industrial production lines.",
            "Mechatronics, PLC, Sensors, Microcontrollers, Pneumatics", "#047857", 4.6
        ),
        (
            "978-1493921126", "Additive Manufacturing Technologies: 3D Printing, Rapid Prototyping", "Ian Gibson, David Rosen, Brent Stucker",
            "Advanced Manufacturing", "School of Manufacturing & Robotics", "670.285 GIB",
            "3rd Edition", "Springer", 2021,
            1, "Aisle A-2", "Rack R-02", 1, 4, 1,
            "Fundamental processes of 3D printing: stereolithography, selective laser sintering, direct metal deposition, and industrial prototyping.",
            "3D Printing, Prototyping, Materials, Laser Sintering, CAD/CAM", "#6d28d9", 4.7
        ),
        (
            "978-0831131586", "CNC Machining Handbook: Basic Theory & CNC Programming", "James Madison",
            "Manufacturing & Machining", "School of Manufacturing & Robotics", "671.35 MAD",
            "2nd Edition", "Industrial Press", 2018,
            1, "Aisle A-3", "Rack R-01", 2, 5, 3,
            "Practical guide to G-code programming, multi-axis machining centers, tool paths, and precision manufacturing quality control.",
            "CNC, G-Code, Machining, Milling, Tooling, Lathes", "#475569", 4.5
        ),
        (
            "978-9386173003", "Industrial Automation and Robotics", "A.K. Gupta, S.K. Arora",
            "Automation", "School of Manufacturing & Robotics", "629.8 GUP",
            "3rd Edition", "University Science Press", 2020,
            1, "Aisle A-3", "Rack R-02", 3, 6, 3,
            "PLC architectures, SCADA systems, hydraulic & pneumatic actuators, and industrial robotic cells.",
            "SCADA, PLC, Industrial Automation, Sensors, Factory 4.0", "#0369a1", 4.5
        ),

        # School of Sustainable Technologies & Green Energy (Floor 2, Aisle C)
        (
            "978-1260464078", "Electric Vehicle Engineering", "Per Enge, Nick Enge, Stephen Zoepf",
            "Electric Vehicles & Mobility", "School of Green Energy", "629.229 ENG",
            "1st Edition", "McGraw Hill", 2021,
            2, "Aisle C-1", "Rack R-01", 2, 5, 2,
            "Comprehensive textbook explaining the electrical, mechanical, and energy storage systems behind modern electric vehicles.",
            "EV, Batteries, Inverters, Regenerative Braking, Motor Drives", "#059669", 4.8
        ),
        (
            "978-8120351110", "Solar Photovoltaic Technology and Systems", "Chetan Singh Solanki",
            "Renewable Energy", "School of Green Energy", "621.312 SOL",
            "1st Edition", "PHI Learning", 2018,
            2, "Aisle C-1", "Rack R-02", 3, 8, 5,
            "Manual for technicians, engineers, and researchers on grid-tied and off-grid solar PV design, MPPT, and rooftop installation.",
            "Solar, Photovoltaics, Inverters, Clean Tech, Grid Tied", "#ea580c", 4.7
        ),
        (
            "978-0128044407", "Battery Management Systems for Electric Vehicles", "H.J. Bergveld, W.S. Kruijt",
            "Battery Tech & Storage", "School of Green Energy", "621.312 BER",
            "2nd Edition", "Elsevier", 2022,
            2, "Aisle C-2", "Rack R-02", 2, 4, 1,
            "State-of-charge (SoC) estimation, thermal management, cell balancing, and safety architectures for Lithium-ion packs.",
            "Battery, Lithium-ion, BMS, Safety, Energy Storage", "#0891b2", 4.8
        ),
        (
            "978-1118180198", "Smart Grid: Fundamentals of Design and Analysis", "James Momoh",
            "Power Systems & Smart Grids", "School of Green Energy", "621.31 MOM",
            "1st Edition", "IEEE Press / Wiley", 2019,
            2, "Aisle C-3", "Rack R-01", 3, 5, 3,
            "Covers microgrids, demand response, phasor measurement units, cyber-physical grid security, and renewable integration.",
            "Smart Grid, Microgrid, Power Systems, Renewable Integration", "#2563eb", 4.6
        ),

        # School of Healthcare & Allied Medical Sciences (Floor 2, Aisle D)
        (
            "978-0071477475", "Biomedical Instrumentation: Technology and Applications", "R.S. Khandpur",
            "Biomedical Technology", "School of Healthcare Sciences", "610.28 KHA",
            "2nd Edition", "McGraw Hill", 2020,
            2, "Aisle D-1", "Rack R-01", 2, 6, 3,
            "ECG, EEG, patient monitoring systems, MRI, CT scanners, ultrasound transducers, and medical safety regulations.",
            "Biomedical, Medical Devices, ECG, Imaging, Diagnostics", "#be185d", 4.7
        ),
        (
            "978-9351528654", "Medical Laboratory Technology: Methods and Interpretations", "Ramnik Sood",
            "Clinical Lab Sciences", "School of Healthcare Sciences", "616.075 SOO",
            "6th Edition", "Jaypee Brothers Medical Pub", 2019,
            2, "Aisle D-2", "Rack R-01", 3, 8, 4,
            "Standard clinical protocols for hematology, clinical pathology, biochemistry, microbiology, and histology.",
            "Pathology, Hematology, Biochemistry, Diagnostics, Lab Skills", "#9333ea", 4.6
        ),
        (
            "978-0124159587", "Food Process Engineering and Technology", "Zeki Berk",
            "Agro-Tech & Food Processing", "School of Healthcare Sciences", "664.02 BER",
            "3rd Edition", "Academic Press", 2018,
            2, "Aisle D-1", "Rack R-02", 1, 5, 2,
            "Thermal processing, dehydration, freeze-drying, extrusion, membrane filtration, and preservation techniques.",
            "Food Technology, Processing, Quality, Preservation, Agriculture", "#15803d", 4.6
        ),

        # General Skill, Entrepreneurship & Northeast Heritage (Ground Floor, Aisle G)
        (
            "978-8132104087", "Skill Development in India: Vocational Education Perspectives", "Santosh Mehrotra",
            "Skill Ecosystem & TVET", "School of Entrepreneurship", "370.113 MEH",
            "1st Edition", "SAGE Publications", 2021,
            0, "Aisle G-1", "Rack R-01", 2, 7, 5,
            "Analysis of India's demographic dividend, National Skills Qualification Framework (NSQF), and industry apprenticeship models.",
            "Vocational Education, NSQF, TVET, Skilling, Policy", "#b45309", 4.5
        ),
        (
            "978-9381563205", "Biodiversity and Indigenous Knowledge of Assam & NE India", "P.C. Bhattacharjee, B.K. Baruah",
            "Assam Heritage & Ecology", "General Reference", "577.095 BHA",
            "1st Edition", "Guwahati Academic Press", 2019,
            0, "Aisle G-1", "Rack R-02", 1, 5, 3,
            "Documentation of ethnobotanical traditions, agro-biodiversity, medicinal flora, and indigenous craft traditions of the Brahmaputra valley.",
            "Assam, Heritage, Flora, Ecology, Traditional Knowledge", "#047857", 4.8
        ),
        (
            "978-9351439226", "Intellectual Property Rights and Patent Law in India", "V.K. Ahuja",
            "IPR & Patents", "School of Entrepreneurship", "346.048 AHU",
            "3rd Edition", "LexisNexis", 2020,
            0, "Aisle G-2", "Rack R-01", 2, 6, 4,
            "Comprehensive review of Patent Act, designs, trademark protection, Geographical Indications (like Muga Silk, Assam Tea), and startup filing.",
            "Patents, IPR, Startups, Copyright, Assam GI", "#c2410c", 4.6
        )
    ]

    cursor.executemany("""
    INSERT INTO books (
        isbn, title, author, category, department, call_no, edition, publisher, year,
        floor, aisle, rack, shelf_tier, total_copies, available_copies, summary, tags,
        cover_color, rating
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, books_data)

    # Pre-seeded Seats (48 seats across Floor 1 & Floor 2)
    # Floor 1:
    # - Quiet Carrels: S-101 to S-116
    # - Digital AI/Robotics Workstations: D-101 to D-108
    # Floor 2:
    # - Collaborative Pods: P-201 to P-208 (4 seat pods)
    # - Discussion / Seminar Rooms: DR-201 to DR-204
    # - Postgrad / Researcher Carrels: R-201 to R-212

    seats_data = []

    # Floor 1: Quiet Carrels (S-101 .. S-116)
    for i in range(1, 17):
        seat_no = f"S-10{i:02d}" if i < 10 else f"S-1{i}"
        status = "AVAILABLE"
        stud_id = None
        stud_name = None
        res_until = None
        checked_in = 0
        code = f"CHK-F1-{100+i}"

        # Some realistic active occupancies
        if i == 2:
            status = "OCCUPIED"
            stud_id = "ASU/2026/CS-014"
            stud_name = "Debojit Hazarika"
            res_until = (now + timedelta(hours=1, minutes=45)).strftime("%Y-%m-%d %H:%M")
            checked_in = 1
        elif i == 5:
            status = "RESERVED"
            stud_id = "ASU/2026/AI-104"
            stud_name = "Ankur Barman"
            res_until = (now + timedelta(minutes=11)).strftime("%Y-%m-%d %H:%M")
            checked_in = 0
        elif i == 9:
            status = "OCCUPIED"
            stud_id = "ASU/2026/RO-008"
            stud_name = "Juri Das"
            res_until = (now + timedelta(hours=2, minutes=10)).strftime("%Y-%m-%d %H:%M")
            checked_in = 1
        elif i == 14:
            status = "MAINTENANCE"

        col = (i - 1) % 4
        row = (i - 1) // 4
        px = 80 + col * 70
        py = 100 + row * 65

        seats_data.append((
            seat_no, 1, "Quiet Study Zone A", "Individual Carrel",
            1, 1, status, stud_id, stud_name, res_until, checked_in, code, px, py
        ))

    # Floor 1: Digital Lab Workstations (D-101 .. D-108)
    for i in range(1, 9):
        seat_no = f"D-10{i}"
        status = "AVAILABLE"
        stud_id = None
        stud_name = None
        res_until = None
        checked_in = 0
        code = f"CHK-DL-{100+i}"

        if i == 1:
            status = "OCCUPIED"
            stud_id = "ASU/2026/CS-088"
            stud_name = "Pranab Saikia"
            res_until = (now + timedelta(hours=3, minutes=15)).strftime("%Y-%m-%d %H:%M")
            checked_in = 1
        elif i == 4:
            status = "OCCUPIED"
            stud_id = "ASU/2026/AI-033"
            stud_name = "Trishna Devi"
            res_until = (now + timedelta(minutes=40)).strftime("%Y-%m-%d %H:%M")
            checked_in = 1

        col = (i - 1) % 4
        row = (i - 1) // 4
        px = 420 + col * 75
        py = 100 + row * 85

        seats_data.append((
            seat_no, 1, "Digital AI & GPU Lab", "High-Performance Workstation",
            1, 1, status, stud_id, stud_name, res_until, checked_in, code, px, py
        ))

    # Floor 2: Collaborative Pods (P-201 .. P-208)
    for i in range(1, 9):
        seat_no = f"P-20{i}"
        status = "AVAILABLE"
        stud_id = None
        stud_name = None
        res_until = None
        checked_in = 0
        code = f"CHK-POD-{200+i}"

        if i == 2:
            status = "OCCUPIED"
            stud_id = "ASU/2026/MT-022"
            stud_name = "Priyanshu Sharma (Team Mecha)"
            res_until = (now + timedelta(hours=1, minutes=20)).strftime("%Y-%m-%d %H:%M")
            checked_in = 1
        elif i == 6:
            status = "RESERVED"
            stud_id = "ASU/2026/EV-015"
            stud_name = "Dipika Kalita"
            res_until = (now + timedelta(minutes=9)).strftime("%Y-%m-%d %H:%M")
            checked_in = 0

        col = (i - 1) % 4
        row = (i - 1) // 4
        px = 80 + col * 85
        py = 100 + row * 95

        seats_data.append((
            seat_no, 2, "Collaborative Learning Pods", "4-Seater Smart Pod",
            1, 1, status, stud_id, stud_name, res_until, checked_in, code, px, py
        ))

    # Floor 2: Discussion Rooms (DR-201 .. DR-204)
    for i in range(1, 5):
        seat_no = f"DR-20{i}"
        status = "AVAILABLE"
        stud_id = None
        stud_name = None
        res_until = None
        checked_in = 0
        code = f"CHK-DR-{200+i}"

        if i == 1:
            status = "OCCUPIED"
            stud_id = "ASU/FAC/RO-002"
            stud_name = "Dr. Manash Borah (Robotics Lab Meet)"
            res_until = (now + timedelta(minutes=55)).strftime("%Y-%m-%d %H:%M")
            checked_in = 1

        px = 450 + (i - 1) * 75
        py = 110

        seats_data.append((
            seat_no, 2, "Discussion & Seminar Rooms", "Conference Pod (8-10 Pax)",
            1, 1, status, stud_id, stud_name, res_until, checked_in, code, px, py
        ))

    # Floor 2: Postgrad & Research Carrels (R-201 .. R-212)
    for i in range(1, 13):
        seat_no = f"R-2{i:02d}"
        status = "AVAILABLE"
        stud_id = None
        stud_name = None
        res_until = None
        checked_in = 0
        code = f"CHK-RES-{200+i}"

        if i == 3:
            status = "OCCUPIED"
            stud_id = "ASU/PHD/2025/03"
            stud_name = "Pallab Goswami (Green Hydrogen Research)"
            res_until = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M")
            checked_in = 1

        col = (i - 1) % 4
        row = (i - 1) // 4
        px = 450 + col * 70
        py = 220 + row * 65

        seats_data.append((
            seat_no, 2, "Scholars & Research Wing", "Private Research Carrel",
            1, 1, status, stud_id, stud_name, res_until, checked_in, code, px, py
        ))

    cursor.executemany("""
    INSERT INTO seats (
        seat_number, floor, zone, seat_type, has_power, has_lan, status,
        current_student_id, current_student_name, reserved_until, checked_in,
        checkin_code, pos_x, pos_y
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, seats_data)

    # Pre-seeded Borrowings
    # Scenario:
    # 1. Ankur Barman (Current logged in student demo)
    #    - Book 1: "Deep Learning with Python" (due in 2 days -> Orange reminder alert)
    #    - Book 2: "Introduction to Robotics" (overdue by 3 days -> Overdue alert, ₹6 fine)
    # 2. Priyanshu Sharma
    #    - Book 1: "Mechatronics: Electronic Control Systems" (due in 8 days -> Safe)
    # 3. Dipika Kalita
    #    - Book 1: "Electric Vehicle Engineering" (due in 1 day -> Urgent reminder)

    borrowings_data = [
        # Book 1: Deep Learning with Python (id 1)
        (
            1, "ASU/2026/AI-104", "Ankur Barman", "School of Computing & AI",
            (now - timedelta(days=12)).strftime("%Y-%m-%d"),
            (now + timedelta(days=2)).strftime("%Y-%m-%d"),
            None, 0, 0.0, "BORROWED"
        ),
        # Book 2: Introduction to Robotics (id 9) - OVERDUE
        (
            9, "ASU/2026/AI-104", "Ankur Barman", "School of Computing & AI",
            (now - timedelta(days=17)).strftime("%Y-%m-%d"),
            (now - timedelta(days=3)).strftime("%Y-%m-%d"),
            None, 0, 6.0, "OVERDUE"
        ),
        # Book 3: Mechatronics (id 11)
        (
            11, "ASU/2026/MT-022", "Priyanshu Sharma", "School of Manufacturing & Robotics",
            (now - timedelta(days=6)).strftime("%Y-%m-%d"),
            (now + timedelta(days=8)).strftime("%Y-%m-%d"),
            None, 1, 0.0, "BORROWED"
        ),
        # Book 4: Electric Vehicle Engineering (id 15)
        (
            15, "ASU/2026/EV-015", "Dipika Kalita", "School of Green Energy",
            (now - timedelta(days=13)).strftime("%Y-%m-%d"),
            (now + timedelta(days=1)).strftime("%Y-%m-%d"),
            None, 0, 0.0, "BORROWED"
        ),
        # Book 5: Designing Data-Intensive Applications (Returned history)
        (
            3, "ASU/2026/AI-104", "Ankur Barman", "School of Computing & AI",
            (now - timedelta(days=40)).strftime("%Y-%m-%d"),
            (now - timedelta(days=26)).strftime("%Y-%m-%d"),
            (now - timedelta(days=27)).strftime("%Y-%m-%d"),
            0, 0.0, "RETURNED"
        )
    ]

    cursor.executemany("""
    INSERT INTO borrowings (
        book_id, student_id, student_name, student_dept, issue_date,
        due_date, return_date, renewal_count, fine_amount, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, borrowings_data)

    # Pre-seeded Book Reservations (Queue)
    # "Natural Language Processing with Transformers" has 0 available copies and 2 waitlisted students
    reservations_data = [
        (
            7, "ASU/2026/AI-104", "Ankur Barman",
            (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
            "PENDING", 1, None
        ),
        (
            7, "ASU/2026/CS-014", "Debojit Hazarika",
            (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
            "PENDING", 2, None
        )
    ]

    cursor.executemany("""
    INSERT INTO book_reservations (
        book_id, student_id, student_name, reserve_date, status, queue_position, pickup_deadline
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, reservations_data)

    # Pre-seeded Notifications & Alerts
    notifications_data = [
        (
            "ASU/2026/AI-104",
            "⚠️ Overdue Alert: 'Introduction to Robotics'",
            "This book is 3 days overdue. A late fee of ₹2.00/day (Current: ₹6.00) applies. Please return or renew at Central Library Circulation Desk.",
            "SMS", "OVERDUE",
            (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
            0, "RENEW_BOOK", '{"borrowing_id": 2}'
        ),
        (
            "ASU/2026/AI-104",
            "⏰ Due Date Reminder: 2 Days Left",
            "Your borrowed book 'Deep Learning with Python' is due on " + (now + timedelta(days=2)).strftime("%b %d, %Y") + ". Click to renew online if no hold exists.",
            "EMAIL", "URGENT",
            (now - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"),
            0, "RENEW_BOOK", '{"borrowing_id": 1}'
        ),
        (
            "ASU/2026/AI-104",
            "🪑 Seat Reserved: S-105 (Quiet Zone A)",
            "Your study carrel S-105 is reserved. Grace period active (15 minutes). Scan QR at desk S-105 or enter check-in code 'CHK-F1-105' to confirm arrival.",
            "IN_APP", "NORMAL",
            (now - timedelta(minutes=4)).strftime("%Y-%m-%d %H:%M"),
            0, "CHECKIN_SEAT", '{"seat_id": 5}'
        ),
        (
            "ASU/2026/AI-104",
            "📚 Reservation Waitlist Confirmed: NLP with Transformers",
            "You are Position #1 in the queue for 'Natural Language Processing with Transformers'. You will be notified instantly when the copy is checked in.",
            "IN_APP", "SUCCESS",
            (now - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"),
            1, "VIEW_BOOK", '{"book_id": 7}'
        )
    ]

    cursor.executemany("""
    INSERT INTO notifications (
        student_id, title, message, channel, urgency, timestamp, read, action_type, action_payload
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, notifications_data)

    # Pre-seeded Announcements
    announcements_data = [
        (
            "Central Library Extended Hours for Mid-Semester Exams",
            "The Central Library reading halls and Digital AI Lab will remain open until 11:30 PM on weekdays throughout the exam session.",
            "INFO",
            (now - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
        ),
        (
            "DELNET & IEEE Xplore High-Speed IP Gateway Active",
            "Students can now access over 5,000+ IEEE journals and conference proceedings directly from any library WiFi terminal.",
            "INFO",
            (now - timedelta(days=3)).strftime("%Y-%m-%d %H:%M")
        ),
        (
            "Automated Seat Release Policy Enforced",
            "Reminder: Seats reserved through the Smart Library Portal must be checked in within 15 minutes of reservation time, else they are automatically released to waitlisted students.",
            "WARNING",
            (now - timedelta(days=5)).strftime("%Y-%m-%d %H:%M")
        )
    ]

    cursor.executemany("""
    INSERT INTO announcements (title, message, priority, timestamp)
    VALUES (?, ?, ?, ?)
    """, announcements_data)

    conn.commit()
    conn.close()
    print("Database initialized and seeded successfully.")

if __name__ == "__main__":
    init_db()
    seed_data(force=True)
