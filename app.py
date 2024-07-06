import hashlib
import io
import os
import subprocess
import sys

import pyodbc
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__, template_folder="templates")
app.secret_key = 'your_secret_key_here'  # Replace with a secure secret key

# MongoDB setup
# client = MongoClient("mongodb+srv://vankyrs:ddOPZFb5ecQJINEr@cluster0.l00bd5w.mongodb.net/Problems?retryWrites=true&w=majority&appName=Cluster0")
# db = client['Problems']  # Get the database directly
# collection = db["Question"]

client = MongoClient("mongodb+srv://vankyrs:rukHnjdLGabqQGnA@problestatement.ztrbltk.mongodb.net/?retryWrites=true&w=majority&appName=ProbleStatement ")
db = client['Problems']
collection = db['Statements']

# SQL Server setup
connection_string = 'Driver={ODBC Driver 17 for SQL Server};Server=RAMESH\\MSSQLSERVER01;Database=students;Trusted_Connection=yes;'

def get_connection():
    return pyodbc.connect(connection_string)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/register', methods=['POST'])
def register():
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    email = request.form.get('email')
    college = request.form.get('college')
    mobile = request.form.get('mobile')
    password = request.form.get('password')
    password_hash = generate_password_hash(password)
    
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT email, mobile FROM students WHERE email = ? OR mobile = ?", (email, mobile))
        existing_user = cursor.fetchone()

        if existing_user:
            flash("User already registered, please login.")
            return redirect(url_for('login'))
        
        cursor.execute(
            "INSERT INTO students (fname, lname, email, college, mobile, PasswordHash) VALUES (?, ?, ?, ?, ?, ?)",
            (fname, lname, email, college, mobile, password_hash)
        )
        
        conn.commit()
        flash("Registration successful. Please login.")
        return redirect(url_for('login'))
    
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred during registration: {str(e)}")
        return render_template("signup.html")
    
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT fname, PasswordHash FROM students WHERE email = ?", email)
        user = cursor.fetchone()

        if user and check_password_hash(user[1], password):
            session['user'] = user[0]
            return redirect(url_for('homepage'))
        else:
            flash("Invalid email or password. Please try again.")
            return redirect(url_for('login'))

    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('login'))

    finally:
        cursor.close()
        conn.close()

@app.route('/homepage')
def homepage():
    if 'user' in session:
        problems = list(collection.find({}))
        return render_template('index.html', user=session['user'], problems=problems)
    else:
        flash('You are not logged in.')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route("/execute", methods=["POST"])
def execute():
    try:
        data = request.json
        code = data.get("code")
        language = data.get("language", "python")

        if language == "python":
            result = execute_python_code(code)
            return jsonify({"result": result})
        elif language == "java":
            result = execute_java_code(code)
            return jsonify({"result": result})
        else:
            return jsonify({"error": "Unsupported language."})

    except Exception as e:
        return jsonify({"error": str(e)})

def execute_python_code(code):
    try:
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()

        exec(code)  # Unsafe for untrusted code
        result = redirected_output.getvalue()
        if not result.strip():
            result = "No output."

        sys.stdout = old_stdout
        return result

    except Exception as e:
        return f"Error: {str(e)}"

def execute_java_code(code):
    try:
        with open("TempProgram.java", "w") as f:
            f.write(code)

        compile_result = subprocess.run(["javac", "TempProgram.java"], capture_output=True, text=True)
        if compile_result.returncode != 0:
            result = f"Compilation Error: {compile_result.stderr}"
        else:
            run_result = subprocess.run(["java", "TempProgram"], capture_output=True, text=True)
            if run_result.returncode == 0:
                result = run_result.stdout
            else:
                result = f"Runtime Error: {run_result.stderr}"

        os.remove("TempProgram.java")
        if os.path.exists("TempProgram.class"):
            os.remove("TempProgram.class")

        return result.strip()

    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


#pass: rukHnjdLGabqQGnA
#mongodb+srv://vankyrs:rukHnjdLGabqQGnA@problestatement.ztrbltk.mongodb.net/?retryWrites=true&w=majority&appName=ProbleStatement    