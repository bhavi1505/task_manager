from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secretkey"

DATABASE = "database.db"

def get_db():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    return conn

# ---------------- DATABASE INIT ----------------
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        created_by INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        assigned_to INTEGER,
        project_id INTEGER,
        deadline TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()

        user = c.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        ).fetchone()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[4]
            return redirect("/dashboard")

    return render_template("login.html")

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_db()
        c = conn.cursor()

        existing = c.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if existing:
            return "Email already exists"

        c.execute(
            "INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
            (name, email, password, role)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("signup.html")

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    c = conn.cursor()

    role = session["role"]
    user_id = session["user_id"]

    if role == "Admin":
        tasks = c.execute("SELECT * FROM tasks").fetchall()
    else:
        tasks = c.execute(
            "SELECT * FROM tasks WHERE assigned_to=?",
            (user_id,)
        ).fetchall()

    total = len(tasks)
    completed = len([t for t in tasks if t[6] == "Completed"])
    pending = len([t for t in tasks if t[6] != "Completed"])

    return render_template(
        "dashboard.html",
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        role=role
    )

# ---------------- CREATE PROJECT ----------------
@app.route("/create_project", methods=["GET", "POST"])
def create_project():
    if session.get("role") != "Admin":
        return redirect("/dashboard")

    if request.method == "POST":
        name = request.form["name"]

        conn = get_db()
        c = conn.cursor()

        c.execute(
            "INSERT INTO projects (name, created_by) VALUES (?, ?)",
            (name, session["user_id"])
        )

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("create_project.html")

# ---------------- CREATE TASK ----------------
@app.route("/create_task", methods=["GET", "POST"])
def create_task():
    if session.get("role") != "Admin":
        return redirect("/dashboard")

    conn = get_db()
    c = conn.cursor()

    users = c.execute("SELECT id, name FROM users").fetchall()
    projects = c.execute("SELECT id, name FROM projects").fetchall()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        assigned_to = request.form["assigned_to"]
        project_id = request.form["project_id"]
        deadline = request.form["deadline"]

        c.execute("""
        INSERT INTO tasks
        (title, description, assigned_to, project_id, deadline, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            assigned_to,
            project_id,
            deadline,
            "Pending"
        ))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template(
        "create_task.html",
        users=users,
        projects=projects
    )

# ---------------- UPDATE STATUS ----------------
@app.route("/update_status/<int:id>")
def update_status(id):
    conn = get_db()
    c = conn.cursor()

    c.execute(
        "UPDATE tasks SET status='Completed' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
