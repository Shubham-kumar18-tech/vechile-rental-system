
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import date, datetime
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-me")

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "vehicles.db"

VEHICLES = [
    ("Honda Activa", "Scooter", 500, "🛵"),
    ("Royal Enfield", "Bike", 1000, "🏍️"),
    ("Maruti Swift", "Car", 2000, "🚗"),
    ("Hyundai Creta", "Car", 3000, "🚙"),
]


def connect_db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connect_db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                price INTEGER NOT NULL,
                icon TEXT NOT NULL
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                vehicle_id INTEGER NOT NULL,
                pickup_date TEXT NOT NULL,
                return_date TEXT NOT NULL,
                days INTEGER NOT NULL,
                total INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Demo Confirmed',
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
            )
        """)

        con.executemany("""
            INSERT OR IGNORE INTO vehicles (name, type, price, icon)
            VALUES (?, ?, ?, ?)
        """, VEHICLES)


@app.route("/")
def home():
    with connect_db() as con:
        vehicles = con.execute(
            "SELECT * FROM vehicles ORDER BY id"
        ).fetchall()

        bookings = con.execute("""
            SELECT b.*, v.name AS vehicle_name
            FROM bookings b
            JOIN vehicles v ON v.id = b.vehicle_id
            ORDER BY b.id DESC
        """).fetchall()

    return render_template(
        "index.html",
        vehicles=vehicles,
        bookings=bookings,
        today=date.today().isoformat()
    )


@app.route("/book", methods=["POST"])
def book():
    name = request.form.get("customer_name", "").strip()
    vehicle_id = request.form.get("vehicle_id", "")
    pickup = request.form.get("pickup_date", "")
    returned = request.form.get("return_date", "")

    if not name or len(name) > 100:
        flash("Please enter a valid name.")
        return redirect(url_for("home") + "#booking")

    try:
        vehicle_id = int(vehicle_id)
        start = date.fromisoformat(pickup)
        end = date.fromisoformat(returned)
    except (ValueError, TypeError):
        flash("Please select a valid vehicle and dates.")
        return redirect(url_for("home") + "#booking")

    if start < date.today():
        flash("Pickup date cannot be in the past.")
        return redirect(url_for("home") + "#booking")

    if end < start:
        flash("Return date must be on or after pickup date.")
        return redirect(url_for("home") + "#booking")

    days = max(1, (end - start).days)

    with connect_db() as con:
        vehicle = con.execute(
            "SELECT * FROM vehicles WHERE id = ?",
            (vehicle_id,)
        ).fetchone()

        if vehicle is None:
            flash("Vehicle not found.")
            return redirect(url_for("home") + "#booking")

        # Reject overlapping date ranges for the same vehicle.
        conflict = con.execute("""
            SELECT id FROM bookings
            WHERE vehicle_id = ?
              AND pickup_date <= ?
              AND return_date >= ?
        """, (vehicle_id, returned, pickup)).fetchone()

        if conflict:
            flash("This vehicle is already booked for those dates.")
            return redirect(url_for("home") + "#booking")

        total = days * vehicle["price"]

        con.execute("""
            INSERT INTO bookings
            (customer_name, vehicle_id, pickup_date,
             return_date, days, total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, vehicle_id, pickup, returned, days, total))

    flash(
        f"Demo booking created! {vehicle['name']} — "
        f"{days} day(s), total ₹{total:,}."
    )
    return redirect(url_for("home") + "#my-bookings")


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
