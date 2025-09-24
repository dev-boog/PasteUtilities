from flask import Flask, render_template, request, abort, session, redirect, url_for, flash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import os
import string
import random

app = Flask(__name__)
app.secret_key = "random_secret_here"

limiter = Limiter(
    key_func=get_remote_address,
    app=app
)

SUDO_USER = "admin"

# Ensure the pastes directory exists
if not os.path.exists("pastes"):
    os.makedirs("pastes")

@app.route("/", methods=["GET", "POST"])
@limiter.limit("100 per minute", methods=["POST"])
def home():
    
    # Load all pastes with title and ID
    paste_list = []
    for paste_file in os.listdir("pastes"):
        if paste_file.endswith(".txt"):
            title, paste_id_ext = paste_file.rsplit("-", 1)
            paste_id = paste_id_ext[:-4]  # remove ".txt"
            paste_list.append({"title": title, "id": paste_id})

    # Create a new paste
    if request.method == "POST":
        title = request.form.get("paste-title", "").strip()
        content = request.form.get("paste-content", "").strip()
        if not title or not content:
            return render_template("index.html", files=paste_list, paste_count=len(paste_list))
        
        # Generate unique ID
        paste_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        file_name = f"{title}-{paste_id}.txt"
        file_path = os.path.join("pastes", file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return redirect(url_for("view_paste", paste_id=paste_id))

    return render_template("index.html", files=paste_list, paste_count=len(paste_list))

# View paste
@app.route("/paste/<paste_id>")
def view_paste(paste_id):
    # Protections
    if '..' in paste_id or '/' in paste_id or '\\' in paste_id: 
        abort(400, "Invalid paste ID.")

    # Find paste file by ID
    file_path = None
    title = None
    for paste_file in os.listdir("pastes"):
        if paste_file.endswith(f"-{paste_id}.txt"):
            file_path = os.path.join("pastes", paste_file)
            title = paste_file.rsplit("-", 1)[0]
            break

    if not file_path or not os.path.exists(file_path):
        abort(404, "Paste not found.")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return render_template("paste.html", title=title, content=content)


# Admin dashboard
@app.route("/admin", methods=["GET", "POST"])
def admin_dashboard():
    if 'admin_logged_in' not in session:
        if request.method == "POST": 
            password = request.form.get("password", "")
            if password == SUDO_USER:
                session['admin_logged_in'] = True
                return redirect(url_for("admin_dashboard"))
            else:
                return "Invalid password", 403
        return render_template("admin_login.html") 

    # Count total pastes
    paste_count = len(os.listdir("pastes"))
    return render_template("admin.html", paste_count=paste_count)


# Logout as admin
@app.route("/logout")
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_dashboard'))


if __name__ == "__main__":
    app.run(debug=True)
