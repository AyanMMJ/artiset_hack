import hashlib
import io
import os
import subprocess
import sys
import traceback

import pyodbc
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY", "your_secret_key_here"
)  # Use environment variable for secret key

# MongoDB setup
client = MongoClient(
    "mongodb+srv://vankyrs:rukHnjdLGabqQGnA@problestatement.ztrbltk.mongodb.net/?retryWrites=true&w=majority&appName=ProbleStatement"
)
db = client["Problems"]
collection = db["Statements"]

# SQL Server setup
connection_string = "Driver={ODBC Driver 17 for SQL Server};Server=RAMESH\\MSSQLSERVER01;Database=students;Trusted_Connection=yes;"


def get_connection():
    return pyodbc.connect(connection_string)


@app.route("/")
def login():
    return render_template("login.html")


# For signing up
@app.route("/signup")
def signup():
    return render_template("signup.html")


# Register route function
@app.route("/register", methods=["POST"])
def register():
    fname = request.form.get("fname")
    lname = request.form.get("lname")
    email = request.form.get("email")
    college = request.form.get("college")
    mobile = request.form.get("mobile")
    password = request.form.get("password")
    password_hash = generate_password_hash(password)

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT email, mobile FROM students WHERE email = ? OR mobile = ?",
            (email, mobile),
        )
        existing_user = cursor.fetchone()

        if existing_user:
            flash("User already registered, please login.")
            return redirect(url_for("login"))

        cursor.execute(
            "INSERT INTO students (fname, lname, email, college, mobile, PasswordHash) VALUES (?, ?, ?, ?, ?, ?)",
            (fname, lname, email, college, mobile, password_hash),
        )

        conn.commit()
        flash("Registration successful. Please login.")
        return redirect(url_for("login"))

    except Exception as e:
        conn.rollback()
        flash(f"An error occurred during registration: {str(e)}")
        return render_template("signup.html")

    finally:
        cursor.close()
        conn.close()


# Also for login page
@app.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email")
    password = request.form.get("password")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT fname, PasswordHash FROM students WHERE email = ?", email
        )
        user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            session["user"] = user[0]
            return redirect(url_for("homepage"))
        else:
            flash("Invalid email or password. Please try again.")
            return redirect(url_for("login"))

    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for("login"))

    finally:
        cursor.close()
        conn.close()


# Route for adding problem statement
@app.route("/addps", methods=["GET"])
def add_problem_statement():
    return render_template("addps.html")


# Route for submitting the problrm (Dynamic allocation and result evaluation)
@app.route("/submit_problem", methods=["POST"])
def submit_problem():
    problem_statement = request.form["problem_statement"]
    test_inputs = request.form.getlist("test_input[]")
    expected_outputs = request.form.getlist("expected_output[]")

    try:
        # Construct the document to insert into MongoDB
        document = {
            "problem_statement": problem_statement,
            "test_cases": [
                {"input": test_input, "output": expected_output}
                for test_input, expected_output in zip(test_inputs, expected_outputs)
            ],
        }

        # Insert into MongoDB
        collection.insert_one(document)

        return redirect(url_for("homepage"))

    except Exception as e:
        flash(f"An error occurred while submitting the problem: {str(e)}")
        return redirect(url_for("homepage"))


# Route for homepage
@app.route("/homepage")
def homepage():
    if "user" in session:
        try:
            problems = list(collection.find({}))
            return render_template(
                "index.html", user=session["user"], problems=problems
            )
        except Exception as e:
            flash(f"An error occurred while fetching problems: {str(e)}")
            return render_template("index.html", user=session["user"], problems=[])
    else:
        flash("You are not logged in.")
        return redirect(url_for("login"))


# Logout section to close the user sessions
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# Section for code execution when run button in clicked
@app.route("/execute_code", methods=["POST"])
def execute_code():
    try:
        data = request.json
        code = data["code"]
        language = data["language"]
        print(code)
        if language == "python":
            result = subprocess.run(
                ["python", "-c", code], capture_output=True, text=True, timeout=10
            )
        elif language == "javascript":
            result = subprocess.run(
                ["node", "-e", code], capture_output=True, text=True, timeout=10
            )
        elif language == "java":
            with open("UserCode.java", "w") as file:
                file.write(code)
            compile_result = subprocess.run(
                ["javac", "UserCode.java"], capture_output=True, text=True
            )
            if compile_result.returncode == 0:
                result = subprocess.run(
                    ["java", "UserCode"], capture_output=True, text=True, timeout=10
                )
            else:
                return jsonify({"error": compile_result.stderr})
        if result.returncode == 0:
            return jsonify({"output": result.stdout})
        else:
            return jsonify({"error": result.stderr})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)})


# Section to check the code against custom input from the mongodb
# When submit button is clicked
@app.route("/check_code", methods=["POST"])
def check_code():
    try:
        score = 0
        data = request.json
        code = data["code"]
        language = data["language"]
        # Retrieve all problems from MongoDB
        problems = list(collection.find({}))
        results = []
        for problem in problems:
            test_cases = problem.get(
                "test_cases", []
            )  # Retrieve test cases for each problem
            for test in test_cases:
                cus_input = test.get("input", "").strip()
                expected_output = test.get(
                    "output", ""
                ).strip()  # Get expected output from test case
                # Execute code and capture output
                if language == "python":
                    command = ["python", "-c", code]
                    result = subprocess.run(
                        command, input=cus_input, capture_output=True, text=True
                    )
                    if result.returncode == 0:
                        actual_output = result.stdout.strip()
                        print(actual_output, "===", expected_output)
                        if actual_output == expected_output:
                            results.append({"status": "Passed"})
                        else:
                            results.append(
                                {
                                    "status": "Failed",
                                    "expected_output": expected_output,
                                    "actual_output": actual_output,
                                }
                            )
                    else:
                        results.append(
                            {"status": "Failed", "error": result.stderr.strip()}
                        )
                else:
                    results.append(
                        {
                            "status": "Failed",
                            "error": f"Unsupported language: {language}",
                        }
                    )
        return jsonify({"results": results})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
