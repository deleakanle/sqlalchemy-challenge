# Import the dependencies.
import os
import numpy as np
import sqlalchemy
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy .orm import Session
from datetime import datetime, timedelta
from sqlalchemy.ext.automap import automap_base


#################################################
# Database Setup
#################################################

basedir = os.path.abspath(os.path.dirname(__file__))

engine = create_engine("sqlite:///"+os.path.join(basedir,"Resources/hawaii.sqlite"))

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """List all available api routes"""
    return(
        f"Available Routes:<br>"
        f"/api/v1.0/precipitation<br>"
        f"/api/v1.0/stations<br>"
        f"/api/v1.0/tobs<br>"
        f"/api/v1.0/2013-03-13<br>"
         f"/api/v1.0/2013-03-13/2017-03-13"
         )

@app.route("/api/v1.0/precipitation")
def preicipitation():
    
    # Create our ession (link) from Python to the DB
    session = Session(engine)

    # Query all dates and precipitation data
    precipitation_list = session.query(Measurement.date, Measurement.prcp)\
        .filter(Measurement.date >= '2016-08-23')\
        .all()

    session.close()

    # Convert the query results from your precipitation analysis\ 
    # (i.e. retrieve only the last 12 months of data) to a dictionary\ 
    # using date as the key and prcp as the value.

    # Create a dictionary from the row data
    precipitation_dict = {}
    for date, prcp in precipitation_list:
        if date in precipitation_dict:
            precipitation_dict[date].append(prcp)
        else:
            precipitation_dict[date] = [prcp]

    # Return the results in a JSON format.
    return jsonify(precipitation_dict) 

@app.route("/api/v1.0/stations")
def stations():
    #  Create our session (link) from Python to the DB
    session = Session(engine)

    # Query all station names
    stations = session.query(Station.station, Station.name, Station.latitude, Station.longitude, Station.elevation).all()
    
    # Close the session.
    session.close()

    # Return a JSON list of stations from the dataset.
    
    # Iterate through the query and return values to a new list.
    stations_dict = {}
    for row in stations:
        stations_dict[row[0]] = [row[1:]]

    # Return the results in a JSON format.
    return jsonify(stations_dict)

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query the dates and temperature observations of the most-active station\ 
    # for the previous year of data.

    # Query the stations to find the one with the most rows of data.
    station_activity = session.query(Measurement.station, func.count(Measurement.station))\
        .group_by(Measurement.station)\
        .order_by(func.count(Measurement.station).desc())\
        .first()
    
    most_active = str(station_activity[0])
    
    # Query all of the dates and temp observations.
    # Note: The date is from a previous query that found\ 
    # the date a year prior from the station's most recent date
    year_temps = session.query(Measurement.date, Measurement.tobs)\
        .filter(Measurement.station == most_active)\
        .filter(Measurement.date >= '2016-08-18')\
        .all()
    
    # Close the session.
    session.close()

    # Return a JSON list of stations from the dataset.

    #  Iterate through the row data and append it to a list
    year_temps_dict = {}
    for date, temps in year_temps:
        year_temps_dict[date] = temps

    # Return the results in a JSON format.
    return jsonify(year_temps_dict)

@app.route("/api/v1.0/<start>")
def start_route(start):
    """You can add your own start date by replacing the date in the URL 
    using the format of YYYY-MM-DD. If your start date is in the data set, 
    you will get the minimum, average, and maximum temperatures 
    beginning from that date to the most recent date of the data set."""

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query the data to get all of the dates and temps in the range.
    query = session.query(Measurement.date, Measurement.tobs).filter(Measurement.date >= start).all()
    
    # Close the session.
    session.close()

    # Query the data to get the oldest and most recent dates to create the range.
    oldest_date = session.query(func.min(Measurement.date)).first()[0]
    oldest_datetime = datetime.strptime(oldest_date, '%Y-%m-%d')

    recent_date = session.query(func.max(Measurement.date)).first()[0]
    recent_datetime  = datetime.strptime(recent_date, '%Y-%m-%d')

    start_datetime = datetime.strptime(start, '%Y-%m-%d')

    if start_datetime < oldest_datetime or start_datetime > recent_datetime:
        return jsonify({"Error": "Date is out of data set range."}), 404
    

    
    # To find the min, avg, max for an entire range (given specified start and end dates),
    # first find the min, avg, max for the entire range. 
    def range(d,e):
        temps_list = []
        for i, j in query:
            temps_list.append(j)
        minimum = min(temps_list)
        average = np.mean(temps_list)
        maximum = max(temps_list)
        # Then put those values into a dictionary.
        start_dict = {'Minimum':minimum, 'Average':average, 'Maximum':maximum}
        # Iterate through the query to find which dates correspond to the values.
        # Create new dictionaries to show that data.
        for i,j in query:
            if j == minimum:
                start_dict['Minimum'] = {'Date':i,'Temp':j}
            if j == average:
                start_dict['Average'] = {'Date':i,'Temp':j}
            if j == maximum:
                start_dict['Maximum'] = {'Date':i,'Temp':j}
        return(start_dict)
    
    start_results = range(start,oldest_date)
    
    #  Return a JSON list.
    return jsonify(start_results)

@app.route("/api/v1.0/<start>/<end>")
def start_end_route(start, end):
    """ Add your own start date by replacing the dates in the URL 
    using the format of YYYY-MM-DD. If your dates are in the data set, 
    you will get the minimum, average, and maximum temperatures 
    beginning from your start date to your end date."""

    # Create our session (link) from Python to the DB
    session = Session(engine)

    # Query the data to get all of the dates and temps in the range.
    query = session.query(Measurement.date, Measurement.tobs)\
            .filter(Measurement.date >= start)\
            .filter(Measurement.date <= end)\
            .all()
    
    # Close the session.
    session.close()

    #  Query the data to get the oldest and most recent dates to create the range.
    oldest_date = session.query(func.min(Measurement.date)).first()[0]
    oldest_datetime = datetime.strptime(oldest_date, '%Y-%m-%d')

    recent_date = session.query(func.max(Measurement.date)).first()[0]
    recent_datetime  = datetime.strptime(recent_date, '%Y-%m-%d')

    start_datetime = datetime.strptime(start, '%Y-%m-%d')
    end_datetime = datetime.strptime(end, '%Y-%m-%d')

    if start_datetime < oldest_datetime or start_datetime > recent_datetime:
        return jsonify({"Error": "Date is out of data set range."}), 404
    else: None

    if end_datetime < oldest_datetime or end_datetime > recent_datetime:
        return jsonify({"Error": "Date is out of data set range."}), 404
    else: None

    if start_datetime > end_datetime:
        return jsonify({"Error": "Start date is after end date."}), 404
    else: None

    
    #  To find the min, avg, max for an entire range (given specified start and end dates),
    # first find the min, avg, max for the entire range. 
    def range(d,e):
        temps_list = []
        for i, j in query:
            temps_list.append(j)
        minimum = min(temps_list)
        average = np.mean(temps_list)
        maximum = max(temps_list)
        # 5.1 Then put those values into a dictionary.
        start_dict = {'Minimum':minimum, 'Average':average, 'Maximum':maximum}
        # 5.2 Iterate through the query to find which dates correspond to the values.
        # Create new dictionaries to show that data.
        for i,j in query:
            if j == minimum:
                start_dict['Minimum'] = {'Date':i, 'Temp':j}
            if j == average:
                start_dict['Average'] = {'Date':i,'Temp':j}
            if j == maximum:
                start_dict['Maximum'] = {'Date':i,'Temp':j}
        return(start_dict)
    
    end_results = range(start,end)
    
    # Return a JSON list.
    return jsonify(end_results)


if __name__ == '__main__':
    app.run(debug=True)


