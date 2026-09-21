
import os

from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "edulearn.db")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "edulearn_secret_key")


# ---------------- DATABASE CONNECTION ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------- CREATE DATABASE ----------------

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student'
        )
    """)

    # Courses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            instructor TEXT NOT NULL,
            duration TEXT NOT NULL,
            price REAL NOT NULL,
            category TEXT NOT NULL,
            image TEXT
        )
    """)

    # Enrollment table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            course_id INTEGER,
            enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    """)

    # Create default admin
    admin = cursor.execute(
        "SELECT * FROM users WHERE email=?",
        ("admin@edulearn.com",)
    ).fetchone()

    if not admin:
        cursor.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "Admin",
            "admin@edulearn.com",
            generate_password_hash("admin123"),
            "admin"
        ))

    # Add sample courses
    course_count = cursor.execute(
        "SELECT COUNT(*) FROM courses"
    ).fetchone()[0]

    if course_count == 0:

        courses = [
            (
                "Python Programming",
                "Learn Python from basics to advanced programming concepts.",
                "Rahul Sharma",
                "8 Weeks",
                2999,
                "Programming",
                "https://images.unsplash.com/photo-1526379095098-d400fd0bf935"
            ),
            (
                "Web Development",
                "Learn HTML, CSS, JavaScript and build modern websites.",
                "Priya Kumar",
                "10 Weeks",
                3999,
                "Web Development",
                "https://images.unsplash.com/photo-1498050108023-c5249f4df085"
            ),
            (
                "Data Analytics",
                "Learn Python, SQL, Excel and data visualization.",
                "Arjun Rao",
                "12 Weeks",
                4999,
                "Data Science",
                "https://images.unsplash.com/photo-1551288049-bebda4e38f71"
            ),
            (
                "Java Programming",
                "Master Java programming and object-oriented concepts.",
                "Anjali Singh",
                "8 Weeks",
                3499,
                "Programming",
                "https://images.unsplash.com/photo-1517694712202-14dd9538aa97"
            ),
            (
                "UI/UX Design",
                "Learn user interface and user experience design.",
                "Sneha Patel",
                "6 Weeks",
                2999,
                "Design",
                "https://images.unsplash.com/photo-1561070791-2526d30994b5"
            ),
            (
                "Machine Learning",
                "Introduction to machine learning and AI concepts.",
                "Vikram Kumar",
                "14 Weeks",
                5999,
                "Data Science",
                "https://images.unsplash.com/photo-1555255707-c07966088b7b"
            )
        ]

        cursor.executemany("""
            INSERT INTO courses
            (title, description, instructor, duration, price, category, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, courses)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def index():

    conn = get_db()

    courses = conn.execute("""
        SELECT * FROM courses
        ORDER BY id DESC
        LIMIT 6
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        courses=courses
    )


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = get_db()

        try:

            conn.execute("""
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
            """, (
                name,
                email,
                hashed_password
            ))

            conn.commit()
            flash("Registration successful. Please login.", "success")

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash("Email already registered.", "danger")

        finally:
            conn.close()

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email=?
        """, (email,)).fetchone()

        conn.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect(url_for("admin"))

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("index"))


# ---------------- COURSES ----------------

@app.route("/courses")
def courses():

    search = request.args.get("search", "")
    category = request.args.get("category", "")

    conn = get_db()

    query = "SELECT * FROM courses WHERE 1=1"
    parameters = []

    if search:

        query += """
            AND (title LIKE ?
            OR description LIKE ?
            OR instructor LIKE ?)
        """

        search_value = "%" + search + "%"

        parameters.extend([
            search_value,
            search_value,
            search_value
        ])

    if category:

        query += " AND category=?"
        parameters.append(category)

    course_list = conn.execute(
        query,
        parameters
    ).fetchall()

    categories = conn.execute("""
        SELECT DISTINCT category
        FROM courses
    """).fetchall()

    conn.close()

    return render_template(
        "courses.html",
        courses=course_list,
        categories=categories,
        search=search,
        selected_category=category
    )


# ---------------- COURSE DETAILS ----------------

@app.route("/course/<int:course_id>")
def course_details(course_id):

    conn = get_db()

    course = conn.execute("""
        SELECT * FROM courses
        WHERE id=?
    """, (course_id,)).fetchone()

    conn.close()

    if not course:
        return "Course not found", 404

    return render_template(
        "course_details.html",
        course=course
    )


# ---------------- ENROLL ----------------

@app.route("/enroll/<int:course_id>", methods=["POST"])
def enroll(course_id):

    if "user_id" not in session:
        flash("Please login to enroll.", "danger")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    existing = conn.execute("""
        SELECT * FROM enrollments
        WHERE user_id=? AND course_id=?
    """, (
        user_id,
        course_id
    )).fetchone()

    if existing:

        flash("You are already enrolled in this course.", "warning")

    else:

        conn.execute("""
            INSERT INTO enrollments
            (user_id, course_id)
            VALUES (?, ?)
        """, (
            user_id,
            course_id
        ))

        conn.commit()

        flash(
            "Course enrolled successfully!",
            "success"
        )

    conn.close()

    return redirect(
        url_for(
            "course_details",
            course_id=course_id
        )
    )


# ---------------- STUDENT DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    enrollments = conn.execute("""
        SELECT
            courses.*,
            enrollments.enrolled_date
        FROM enrollments
        JOIN courses
        ON courses.id = enrollments.course_id
        WHERE enrollments.user_id=?
        ORDER BY enrollments.id DESC
    """, (
        session["user_id"],
    )).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        enrollments=enrollments
    )


# ---------------- ADMIN ----------------

@app.route("/admin")
def admin():

    if session.get("role") != "admin":
        flash("Admin access required.", "danger")
        return redirect(url_for("login"))

    conn = get_db()

    courses = conn.execute("""
        SELECT * FROM courses
    """).fetchall()

    users = conn.execute("""
        SELECT * FROM users
        WHERE role='student'
    """).fetchall()

    enrollment_count = conn.execute("""
        SELECT COUNT(*) FROM enrollments
    """).fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        courses=courses,
        users=users,
        enrollment_count=enrollment_count
    )


# ---------------- ADD COURSE ----------------

@app.route("/admin/add-course", methods=["POST"])
def add_course():

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    title = request.form["title"]
    description = request.form["description"]
    instructor = request.form["instructor"]
    duration = request.form["duration"]
    price = request.form["price"]
    category = request.form["category"]
    image = request.form["image"]

    conn = get_db()

    conn.execute("""
        INSERT INTO courses
        (title, description, instructor, duration,
         price, category, image)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        description,
        instructor,
        duration,
        price,
        category,
        image
    ))

    conn.commit()
    conn.close()

    flash("Course added successfully.", "success")

    return redirect(url_for("admin"))


# ---------------- DELETE COURSE ----------------

@app.route("/admin/delete-course/<int:course_id>")
def delete_course(course_id):

    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute("""
        DELETE FROM courses
        WHERE id=?
    """, (course_id,))

    conn.commit()
    conn.close()

    flash("Course deleted.", "success")

    return redirect(url_for("admin"))


# ---------------- START APPLICATION ----------------

init_db()

if __name__ == "__main__":

    app.run(debug=True)