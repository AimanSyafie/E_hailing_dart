from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle = db.Column(db.String(100))
    rating = db.Column(db.Float)

@app.route('/')
def home():
    drivers = Driver.query.all()
    return render_template('dashboard.html', drivers=drivers)

if __name__ == "__main__":
    app.run(debug=True)
