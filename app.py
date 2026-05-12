from flask import Flask, render_template, request, redirect, session
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'secretkey'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'transport_dashboard'

mysql = MySQL(app)

@app.route('/')
def index():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute('SELECT COUNT(*) AS total_rides FROM rides')
    total_rides = cursor.fetchone()['total_rides']

    cursor.execute('SELECT SUM(ride_fare) AS total_revenue FROM rides')
    revenue = cursor.fetchone()['total_revenue']

    cursor.execute("SELECT COUNT(*) AS active_drivers FROM drivers WHERE status='Active'")
    active_drivers = cursor.fetchone()['active_drivers']

    cursor.execute('SELECT AVG(driver_rating) AS avg_rating FROM drivers')
    avg_rating = cursor.fetchone()['avg_rating']

    return render_template(
        'dashboard.html',
        total_rides=total_rides,
        revenue=revenue,
        active_drivers=active_drivers,
        avg_rating=avg_rating
    )

@app.route('/drivers')
def drivers():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM drivers')
    drivers = cursor.fetchall()
    return render_template('drivers.html', drivers=drivers)

@app.route('/bookings')
def bookings():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM rides')
    rides = cursor.fetchall()
    return render_template('bookings.html', rides=rides)

if __name__ == '__main__':
    app.run(debug=True)
