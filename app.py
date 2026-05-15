from flask import Flask, render_template, request, redirect, session
import pandas as pd
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)

app.secret_key = "dart_secret_key"

CSV_FILE = "dart_brunei_dashboard.csv"


# =====================================================
# LOAD DATA
# =====================================================

def load_data():

    df = pd.read_csv(
        CSV_FILE,
        low_memory=False
    )

    df.columns = [

        c.strip()
        .replace("_", " ")

        for c in df.columns
    ]

    numeric_cols = [

        "Price BND",

        "Ride Distance (KM)",

        "Driver Earnings BND",

        "Driver Ratings"
    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    if "Date" in df.columns:

        df["Date"] = pd.to_datetime(
            df["Date"],
            errors="coerce"
        )

    return df


# =====================================================
# CACHE DATAFRAME
# =====================================================

GLOBAL_DF = load_data()


# =====================================================
# GLOBAL CHART STYLE
# =====================================================

def style_figure(fig):

    fig.update_layout(

        template="plotly_white",

        title_font_size=18,

        title_font_color="#17233c",

        title_x=0.03,

        font=dict(
            family="Poppins",
            size=12,
            color="#17233c"
        ),

        margin=dict(
            l=20,
            r=20,
            t=50,
            b=20
        ),

        paper_bgcolor="white",

        plot_bgcolor="white",

        height=380
    )

    return fig


# =====================================================
# FILTER DATA
# =====================================================

def filter_data(df, year, month):

    filtered_df = df

    if "Date" in df.columns:

        filtered_df = filtered_df[
            filtered_df["Date"].dt.year == int(year)
        ]

        filtered_df = filtered_df[
            filtered_df["Date"].dt.month == int(month)
        ]

    return filtered_df


# =====================================================
# LOGIN
# =====================================================

@app.route('/', methods=['GET', 'POST'])

def login():

    df = GLOBAL_DF

    error = None

    if request.method == 'POST':

        username = request.form['username']

        password = request.form['password']

        role = request.form['role']

        if password != "dart1234":

            error = "Invalid Username or Password"

            return render_template(
                'login.html',
                error=error
            )

        # MANAGEMENT

        if role == 'management':

            if username == 'admin':

                session['role'] = 'management'

                return redirect('/management')

        # DRIVER

        elif role == 'driver':

            drivers = (

                df['Driver ID']
                .astype(str)
                .str.lower()
                .unique()
            )

            if username.lower() in drivers:

                session['role'] = 'driver'

                session['username'] = username

                return redirect('/driver')

        # CUSTOMER

        elif role == 'customer':

            customers = (

                df['Customer ID']
                .astype(str)
                .str.lower()
                .unique()
            )

            if username.lower() in customers:

                session['role'] = 'customer'

                session['username'] = username

                return redirect('/customer')

        error = "Invalid Username or Password"

    return render_template(
        'login.html',
        error=error
    )


# =====================================================
# MANAGEMENT DASHBOARD
# =====================================================

@app.route('/management')

def management():

    if session.get('role') != 'management':

        return redirect('/')

    df = GLOBAL_DF

    year = request.args.get(
        'year',
        '2025'
    )

    month = request.args.get(
        'month',
        '1'
    )

    filtered_df = filter_data(
        df,
        year,
        month
    )

    # =====================================================
    # KPI
    # =====================================================

    total_bookings = len(filtered_df)

    total_revenue = round(

        filtered_df[
            'Price BND'
        ].sum(),

        2
    )

    cancellation_rate = 4.5

    revenue_growth = 12.5

    # =====================================================
    # REVENUE PER DRIVER
    # =====================================================

    revenue_df = (

        filtered_df.groupby(
            'Driver ID'
        )['Price BND']

        .sum()

        .reset_index()

        .head(10)
    )

    fig_revenue = px.bar(

        revenue_df,

        x='Driver ID',

        y='Price BND',

        title='Revenue per Driver',

        color='Price BND',

        color_continuous_scale='Tealgrn'
    )

    style_figure(fig_revenue)

    revenue_chart = pio.to_html(

        fig_revenue,

        include_plotlyjs='cdn',

        full_html=False
    )

    # =====================================================
    # ACTIVE DRIVERS TOP 7
    # =====================================================

    active_df = (

        filtered_df[
            'Pickup Location'
        ]
        .value_counts()

        .head(7)

        .reset_index()
    )

    active_df.columns = [
        'Location',
        'Drivers'
    ]

    fig_active = px.pie(

        active_df,
        names='Location',
        values='Drivers',
        hole=0.55,

        title='Active Driver per Locations',

      
    )

    style_figure(fig_active)

    active_chart = pio.to_html(

        fig_active,

        include_plotlyjs=False,

        full_html=False
    )

    # =====================================================
    # COMPLETED RIDES
    # =====================================================

    completed_df = (

        filtered_df.groupby(
            'Date'
        )

        .size()

        .reset_index(
            name='Completed Rides'
        )
    )

    fig_completed = px.line(

        completed_df,

        x='Date',

        y='Completed Rides',

        title='Completed Rides Trend',

        markers=True
    )

    style_figure(fig_completed)

    completed_chart = pio.to_html(

        fig_completed,

        include_plotlyjs=False,

        full_html=False
    )

    return render_template(

        'management.html',

        total_bookings=total_bookings,

        total_revenue=total_revenue,

        cancellation_rate=cancellation_rate,

        revenue_growth=revenue_growth,

        revenue_chart=revenue_chart,

        active_chart=active_chart,

        completed_chart=completed_chart
    )


# =====================================================
# DRIVER DASHBOARD
# =====================================================

@app.route('/driver')

def driver():

    if session.get('role') != 'driver':

        return redirect('/')

    df = GLOBAL_DF

    username = session.get('username')

    driver_df = df[

        df['Driver ID']
        .astype(str)
        .str.lower()

        == username.lower()
    ]

    if driver_df.empty:

        return redirect('/')

    driver_name = driver_df['Driver ID'].iloc[0]

    # =====================================================
    # KPI
    # =====================================================

    total_earnings = round(

        driver_df[
            'Driver Earnings BND'
        ].sum(),

        2
    )

    driver_rating = round(

        driver_df[
            'Driver Ratings'
        ].mean(),

        2
    )

    acceptance_rate = 92.5

    cancel_rate = 4.1

    # =====================================================
    # DISTANCE BY PICKUP LOCATION
    # =====================================================

    distance_df = (

        driver_df.groupby(
            'Pickup Location'
        )['Ride Distance (KM)']

        .sum()

        .reset_index()

        .sort_values(
            by='Ride Distance (KM)',
            ascending=False
        )

        .head(7)
    )

    fig_distance = px.bar(

        distance_df,

        x='Ride Distance (KM)',

        y='Pickup Location',

        title='Pickup Locations',

        color='Ride Distance (KM)',

        color_continuous_scale='Tealgrn'
    )

    style_figure(fig_distance)

    distance_chart = pio.to_html(

        fig_distance,

        include_plotlyjs='cdn',

        full_html=False
    )

    # =====================================================
    # TRIPS BY DROP LOCATION
    # =====================================================

    trip_df = (

        driver_df.groupby(
            'Drop Location'
        )

        .size()

        .reset_index(
            name='Trips'
        )

        .sort_values(
            by='Trips',
            ascending=False
        )

        .head(7)
    )

    fig_trip = px.bar(

        trip_df,

        x='Drop Location',

        y='Trips',

        title='Drop Locations',

        color='Trips',

        color_continuous_scale='Purples'
    )

    style_figure(fig_trip)

    trip_chart = pio.to_html(

        fig_trip,

        include_plotlyjs=False,

        full_html=False
    )

    return render_template(

        'driver.html',

        driver_name=driver_name,

        total_earnings=total_earnings,

        driver_rating=driver_rating,

        acceptance_rate=acceptance_rate,

        cancel_rate=cancel_rate,

        distance_chart=distance_chart,

        trip_chart=trip_chart
    )


# =====================================================
# CUSTOMER DASHBOARD
# =====================================================

@app.route('/customer')

def customer():

    if session.get('role') != 'customer':

        return redirect('/')

    df = GLOBAL_DF

    username = session.get('username')

    customer_df = df[

        df['Customer ID']
        .astype(str)
        .str.lower()

        == username.lower()
    ]

    if customer_df.empty:

        return redirect('/')

    customer_name = customer_df['Customer ID'].iloc[0]

    # =====================================================
    # KPI
    # =====================================================

    total_spent = round(

        customer_df[
            'Price BND'
        ].sum(),

        2
    )

    avg_ride_cost = round(

        customer_df[
            'Price BND'
        ].mean(),

        2
    )

    avg_wait = 7.4

    driver_rating = round(

        customer_df[
            'Driver Ratings'
        ].mean(),

        2
    )

    # =====================================================
    # STATIC PEAK HOURS
    # =====================================================

    peak_df = pd.DataFrame({

        'Hour': [

            '7AM',
            '8AM',
            '9AM',
            '12PM',
            '5PM',
            '6PM',
            '7PM'
        ],

        'Trips': [

            35,
            52,
            44,
            28,
            67,
            81,
            59
        ]
    })

    fig_peak = px.bar(

        peak_df,

        x='Hour',

        y='Trips',

        title='Peak Hour Demand',

        color='Trips',

        color_continuous_scale='Purples'
    )

    style_figure(fig_peak)

    peak_chart = pio.to_html(

        fig_peak,

        include_plotlyjs='cdn',

        full_html=False
    )

    # =====================================================
    # PAYMENT METHODS
    # =====================================================

    payment_df = pd.DataFrame({

        'Method': [

            'Cash',
            'Card',
            'E-Wallet'
        ],

        'Count': [

            20,
            55,
            25
        ]
    })

    fig_payment = px.pie(

        payment_df,

        names='Method',

        values='Count',

        hole=0.55,

        title='Payment Methods'
    )

    style_figure(fig_payment)

    payment_chart = pio.to_html(

        fig_payment,

        include_plotlyjs=False,

        full_html=False
    )

    # =====================================================
    # VEHICLE DISTRIBUTION
    # =====================================================

    vehicle_df = pd.DataFrame({

        'Vehicle': [

            'Dart',
            'Dart XL'
        ],

        'Trips': [

            72,
            28
        ]
    })

    fig_vehicle = px.pie(

        vehicle_df,

        names='Vehicle',

        values='Trips',

        hole=0.55,

        title='Vehicle Distribution'
    )

    style_figure(fig_vehicle)

    vehicle_chart = pio.to_html(

        fig_vehicle,

        include_plotlyjs=False,

        full_html=False
    )

    return render_template(

        'customer.html',

        customer_name=customer_name,

        total_spent=total_spent,

        avg_ride_cost=avg_ride_cost,

        avg_wait=avg_wait,

        driver_rating=driver_rating,

        peak_chart=peak_chart,

        payment_chart=payment_chart,

        vehicle_chart=vehicle_chart
    )


# =====================================================
# LOGOUT
# =====================================================

@app.route('/logout')

def logout():

    session.clear()

    return redirect('/')


# =====================================================
# RUN FLASK
# =====================================================

print("RUNNING FLASK")

if __name__ == '__main__':

    app.run(debug=False)