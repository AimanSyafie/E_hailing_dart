from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)

app.secret_key = "dart_secret_key"

# =========================================
# DATABASE CONFIGURATION
# =========================================

database_url = os.getenv("DATABASE_URL")

if database_url:
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///transport.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

DB = SQLAlchemy(app)

# =========================================
# DATABASE MODELS
# =========================================

class User(DB.Model):
    __tablename__ = "users"

    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(100), nullable=False)
    email = DB.Column(DB.String(100), unique=True, nullable=False)
    password = DB.Column(DB.String(255), nullable=False)
    role = DB.Column(DB.String(20), nullable=False)


class Driver(DB.Model):
    __tablename__ = "drivers"

    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(100))
    vehicle = DB.Column(DB.String(100))
    plate_number = DB.Column(DB.String(20))
    rating = DB.Column(DB.Float, default=5.0)
    status = DB.Column(DB.String(20), default="Active")
    earnings = DB.Column(DB.Float, default=0)


class Ride(DB.Model):
    __tablename__ = "rides"

    id = DB.Column(DB.Integer, primary_key=True)
    customer_name = DB.Column(DB.String(100))
    driver_name = DB.Column(DB.String(100))
    pickup = DB.Column(DB.String(100))
    dropoff = DB.Column(DB.String(100))
    fare = DB.Column(DB.Float)
    status = DB.Column(DB.String(20))
    created_at = DB.Column(DB.DateTime, default=datetime.utcnow)

# =========================================
# CREATE DATABASE TABLES
# =========================================

with app.app_context():
    DB.create_all()

# =========================================
# HOME PAGE
# =========================================

@app.route("/")
def home():
    return render_template("login.html")

# =========================================
# REGISTER
# =========================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already exists")
            return redirect("/register")

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            role=role
        )

        DB.session.add(new_user)
        DB.session.commit()

        flash("Registration successful")
        return redirect("/")

    return render_template("register.html")

# =========================================
# LOGIN
# =========================================

@app.route("/login", methods=["POST"])
def login():

    email = request.form["email"]
    password = request.form["password"]

    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):

        session["user_id"] = user.id
        session["name"] = user.name
        session["role"] = user.role

        if user.role == "management":
            return redirect("/management")

        elif user.role == "driver":
            return redirect("/driver")

        elif user.role == "customer":
            return redirect("/customer")

    flash("Invalid email or password")
    return redirect("/")

# =========================================
# MANAGEMENT DASHBOARD
# =========================================

@app.route("/management")
def management():

    if session.get("role") != "management":
        return redirect("/")

    total_rides = Ride.query.count()
    total_drivers = Driver.query.count()
    total_customers = User.query.filter_by(role="customer").count()

    revenue = DB.session.query(DB.func.sum(Ride.fare)).scalar()

    if revenue is None:
        revenue = 0

    rides = Ride.query.order_by(Ride.created_at.desc()).all()

    return render_template(
        "management_dashboard.html",
        total_rides=total_rides,
        total_drivers=total_drivers,
        total_customers=total_customers,
        revenue=revenue,
        rides=rides
    )

# =========================================
# DRIVER DASHBOARD
# =========================================

@app.route("/driver")
def driver_dashboard():

    if session.get("role") != "driver":
        return redirect("/")

    rides = Ride.query.filter_by(status="Completed").all()

    earnings = sum([ride.fare for ride in rides])

    return render_template(
        "driver_dashboard.html",
        rides=rides,
        earnings=earnings
    )

# =========================================
# CUSTOMER DASHBOARD
# =========================================

@app.route("/customer")
def customer_dashboard():

    if session.get("role") != "customer":
        return redirect("/")

    rides = Ride.query.all()

    return render_template(
        "customer_dashboard.html",
        rides=rides
    )

# =========================================
# ADD DRIVER
# =========================================

@app.route("/add-driver", methods=["POST"])
def add_driver():

    if session.get("role") != "management":
        return redirect("/")

    driver = Driver(
        name=request.form["name"],
        vehicle=request.form["vehicle"],
        plate_number=request.form["plate"],
        rating=5.0,
        status="Active",
        earnings=0
    )

    DB.session.add(driver)
    DB.session.commit()

    return redirect("/management")

# =========================================
# ADD RIDE
# =========================================

@app.route("/add-ride", methods=["POST"])
def add_ride():

    if session.get("role") != "management":
        return redirect("/")

    ride = Ride(
        customer_name=request.form["customer"],
        driver_name=request.form["driver"],
        pickup=request.form["pickup"],
        dropoff=request.form["dropoff"],
        fare=float(request.form["fare"]),
        status=request.form["status"]
    )

    DB.session.add(ride)
    DB.session.commit()

    return redirect("/management")

# =========================================
# LOGOUT
# =========================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================================
# MAIN
# =========================================

if __name__ == "__main__":
    app.run(debug=True)
