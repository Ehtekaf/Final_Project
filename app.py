import os
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from cs50 import SQL

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///attendance.db")


@app.route("/attendance")
def attendance():
    # Must be logged in
    if session.get("user_id") is None:
        return redirect("/login")

    # Must be a student (faculty shouldn't see this page)
    user = db.execute("SELECT role FROM users WHERE id = ?", session["user_id"])[0]
    if user["role"] != "student":
        return redirect("/faculty_dashboard")  # or wherever faculty should go

    student_id = session["user_id"]

    rows = db.execute("""
        SELECT courses.id AS course_id,
               courses.name AS course_name,
               COUNT(class_sessions.id) AS total_classes,
               SUM(CASE WHEN attendance_records.status = 'present' THEN 1 ELSE 0 END) AS attended
        FROM enrollments
        JOIN courses ON enrollments.course_id = courses.id
        JOIN class_sessions ON class_sessions.course_id = courses.id
        LEFT JOIN attendance_records
            ON attendance_records.session_id = class_sessions.id
            AND attendance_records.student_id = enrollments.student_id
        WHERE enrollments.student_id = ?
        GROUP BY courses.id
    """, student_id)

    for row in rows:
        if row["total_classes"] > 0:
            row["percentage"] = round((row["attended"] / row["total_classes"]) * 100, 2)
        else:
            row["percentage"] = 0
        row["eligible"] = row["percentage"] >= 75

    return render_template("attendance.html", rows=rows)
