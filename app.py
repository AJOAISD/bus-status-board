from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

DATA_DIR = "data"  # directory to store district databases
os.makedirs(DATA_DIR, exist_ok=True)

# Function to ensure district DB exists
def init_district_db(district):
    db_file = os.path.join(DATA_DIR, f"{district}.db")
    if not os.path.isfile(db_file):
        with sqlite3.connect(db_file) as conn:
            c = conn.cursor()
            # Create buses table
            c.execute('''CREATE TABLE IF NOT EXISTS buses (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            bus_number TEXT NOT NULL,
                            driver TEXT NOT NULL,
                            status TEXT NOT NULL,
                            notes TEXT DEFAULT '')''')
            # Create runs table
            c.execute('''CREATE TABLE IF NOT EXISTS runs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            run_date TEXT NOT NULL,
                            run_time TEXT NOT NULL,
                            group_name TEXT NOT NULL,
                            destination TEXT NOT NULL,
                            driver TEXT NOT NULL,
                            bus_number TEXT NOT NULL)''')
            conn.commit()
    return db_file

# ---------- Routes ----------

@app.route("/district/<district>/")
def index(district):
    db_file = init_district_db(district)
    with sqlite3.connect(db_file) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM buses ORDER BY bus_number")
        buses = c.fetchall()
    return render_template("index.html", buses=buses, district=district)


@app.route("/district/<district>/admin", methods=["GET", "POST"])
def admin(district):
    db_file = init_district_db(district)
    with sqlite3.connect(db_file) as conn:
        c = conn.cursor()

        if request.method == "POST":
            action = request.form.get("action")

            # --- Bus actions ---
            if action == "update":
                bus_id = request.form.get("bus_id")
                driver = request.form.get("driver")
                status = request.form.get("status")
                notes = request.form.get("notes")
                c.execute("UPDATE buses SET driver=?, status=?, notes=? WHERE id=?",
                          (driver, status, notes, bus_id))
                conn.commit()
            elif action == "add":
                bus_number = request.form.get("bus_number")
                driver = request.form.get("driver")
                status = request.form.get("status")
                notes = request.form.get("notes")
                c.execute("INSERT INTO buses (bus_number, driver, status, notes) VALUES (?, ?, ?, ?)",
                          (bus_number, driver, status, notes))
                conn.commit()
            elif action == "delete":
                bus_id = request.form.get("bus_id")
                c.execute("DELETE FROM buses WHERE id=?", (bus_id,))
                conn.commit()

            # --- Runs actions ---
            elif action == "add_run":
                run_date = request.form.get("run_date")
                run_time = request.form.get("run_time")
                group_name = request.form.get("group_name")
                destination = request.form.get("destination")
                driver = request.form.get("driver")
                bus_number = request.form.get("bus_number")
                c.execute("""INSERT INTO runs (run_date, run_time, group_name, destination, driver, bus_number)
                             VALUES (?, ?, ?, ?, ?, ?)""",
                          (run_date, run_time, group_name, destination, driver, bus_number))
                conn.commit()
            elif action == "delete_run":
                run_id = request.form.get("run_id")
                c.execute("DELETE FROM runs WHERE id=?", (run_id,))
                conn.commit()

            return redirect(url_for("admin", district=district))

        # Load both tables for the template
        c.execute("SELECT * FROM buses ORDER BY bus_number")
        buses = c.fetchall()

        c.execute("SELECT * FROM runs ORDER BY run_date, run_time")
        runs = c.fetchall()

    return render_template("admin.html", buses=buses, runs=runs, district=district)


@app.route("/district/<district>/runs")
def runs(district):
    db_file = init_district_db(district)
    with sqlite3.connect(db_file) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM runs ORDER BY run_date, run_time")
        runs_data = c.fetchall()
    return render_template("runs.html", runs=runs_data, district=district)


# Optional landing page to list districts
@app.route("/")
def landing():
    # List all district DBs automatically
    districts = [f.replace(".db","") for f in os.listdir(DATA_DIR) if f.endswith(".db")]
    return render_template("landing.html", districts=districts)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
