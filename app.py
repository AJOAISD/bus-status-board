from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# --- Database Setup ---
def init_db():
    with sqlite3.connect("buses.db") as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS buses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bus_number TEXT NOT NULL,
                        driver TEXT NOT NULL,
                        status TEXT NOT NULL)''')

        c.execute('''CREATE TABLE IF NOT EXISTS runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_date TEXT NOT NULL,
                        run_time TEXT NOT NULL,
                        group_name TEXT NOT NULL,
                        destination TEXT NOT NULL,
                        driver TEXT NOT NULL,
                        bus_number TEXT NOT NULL)''')
        conn.commit()


@app.route("/")
def index():
    with sqlite3.connect("buses.db") as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM buses ORDER BY CAST(bus_number AS INTEGER)")
        buses = c.fetchall()
    return render_template("index.html", buses=buses)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    with sqlite3.connect("buses.db") as conn:
        c = conn.cursor()

        if request.method == "POST":
            action = request.form.get("action")

            # --- Bus actions ---
            if action == "update":
                bus_id = request.form.get("bus_id")
                driver = request.form.get("driver")
                status = request.form.get("status")
                c.execute("UPDATE buses SET driver=?, status=? WHERE id=?",
                          (driver, status, bus_id))
                conn.commit()
            elif action == "add":
                bus_number = request.form.get("bus_number")
                driver = request.form.get("driver")
                status = request.form.get("status")
                c.execute("INSERT INTO buses (bus_number, driver, status) VALUES (?, ?, ?)",
                          (bus_number, driver, status))
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

            return redirect(url_for("admin"))

        # Load both tables for the template
        c.execute("SELECT * FROM buses ORDER BY CAST(bus_number AS INTEGER)")
        buses = c.fetchall()

        c.execute("SELECT * FROM runs ORDER BY run_date, run_time")
        runs = c.fetchall()

    return render_template("admin.html", buses=buses, runs=runs)



@app.route("/runs", methods=["GET", "POST"])
def runs():
    with sqlite3.connect("buses.db") as conn:
        c = conn.cursor()

        if request.method == "POST":
            action = request.form.get("action")

            if action == "add_run":
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

            return redirect(url_for("runs"))

        c.execute("SELECT * FROM runs ORDER BY run_date, run_time")
        runs = c.fetchall()
    return render_template("runs.html", runs=runs)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0")
