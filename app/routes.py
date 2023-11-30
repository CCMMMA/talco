from flask import render_template, request, jsonify, send_file
from app import app, db, logger
from config import Config
from app.models import Measurements, Farms, Timeseries
from io import BytesIO
from shapely.geometry import Polygon
from app.utils import get_index_lat_long, getConc
from datetime import timedelta, datetime, time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import pandas as pd
import re
import json
import uuid
import matplotlib.pyplot as plt
import matplotlib
import os
import multiprocessing


matplotlib.use('agg')
manager = multiprocessing.Manager()
execution_status = manager.dict()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/uploadMeasurements', methods=['POST'])
def uploadMeasurements():
    if 'file' not in request.files:
        return jsonify({'message': 'No file'}), 500

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 500

    if file:
        farmsQuery = Farms.query.all()

        if farmsQuery:
            # Read the file in memory
            file_data = file.read()

            # Detect file type (CSV or Excel) and process accordingly
            if file.filename.endswith('.csv'):
                csv_data = file_data.decode('utf-8')
                df = pd.read_csv(BytesIO(csv_data))
            elif file.filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(BytesIO(file_data))
            else:
                return jsonify({'message': 'Unsupported file format'}), 500

            # Parse the DataFrame and save data to the database
            for _, row in df.iterrows():
                # Check if a record with the same id value exists
                id = row['NUMERO SCHEDA']
                existing_record = Measurements.query.get(id)

                outcome = row['ESITO_pulito']
                if isinstance(outcome, str):
                    outcome = int(re.sub(r'\D', '', outcome))
                if existing_record:
                    # If a record exists, update it with the maximum outcome value
                    existing_record.outcome = max(existing_record.outcome, outcome)
                else:
                    # If no record exists, create a new one
                    if 'COZZA' in row['MATRICE'] and Farms.query.filter_by(site_code=int(row['Codice SITO'])).first():
                        record = Measurements(
                            id=id,
                            year=int(row['ANNO ACCETTAZIONE']),
                            date=row['DATA PRELIEVO'] + timedelta(hours=10),
                            site_code=int(row['Codice SITO']),
                            site_name=row['SITO'],
                            latitude=float(row['LATITUDINE']),
                            longitude=float(row['LONGITUDINE']),
                            animal=row['MATRICE'],
                            outcome=outcome,
                            bacteria=row['PARAMETRO/ANALITA'],
                            unit=row['UNITA MISURA']
                        )
                        db.session.add(record)

            # Commit changes to the database
            db.session.commit()

            return jsonify({'message': 'File uploaded successfully'}), 200
        else:
            return jsonify({'message': 'Upload first farms file!!'}), 500


@app.route('/measurements', methods=['GET'])
def measurements():
    measurementsQuery = Measurements.query.all()
    measurements = []

    if measurementsQuery:
        # Get column names dynamically
        columns = [column.key for column in Measurements.__table__.columns]

        for record in measurementsQuery:
            measurement = {}
            for column in columns:
                measurement[column] = getattr(record, column)

            measurement["timeseries"] = False
            if record.timeseries is not None and len(record.timeseries.values) > 0:
                measurement["timeseries"] = True

            measurements.append(measurement)

    # Sort array by date
    measurements = sorted(measurements, key=lambda x: x['date'])
    return jsonify(measurements)


@app.route('/uploadFarms', methods=['POST'])
def uploadFarms():
    if 'file' not in request.files:
        return jsonify({'message': 'No file'}), 500

    file = request.files['file']

    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 500

    if file:
        # Read the file in memory
        file_data = file.read().decode('utf-8')
        # Covert string to json
        file_data = json.loads(file_data)

        farms = file_data["features"]
        for farm in farms:
            site_code = int(farm['properties']['CODICE'])
            existing_record = Farms.query.get(site_code)
            if not existing_record:
                record = Farms(
                    site_code=site_code,
                    name=farm['properties']['DENOMINAZI'] + '-' + farm['properties']['Comune'],
                    bbox=farm['bbox'],
                    coordinates=farm['geometry']['coordinates']
                )
                db.session.add(record)

        # Commit changes to the database
    db.session.commit()

    return jsonify({'message': 'File uploaded successfully'}), 200


@app.route('/farms', methods=['GET'])
def farms():
    farmsQuery = Farms.query.all()
    farms = []

    if farmsQuery:
        # Get column names dynamically
        columns = [column.key for column in Farms.__table__.columns]

        # Prepare data in a dictionary format
        farms = [{column: getattr(record, column) for column in columns} for record in farmsQuery]

    return jsonify(farms)


@app.route('/get_execution_status', methods=['GET'])
def get_execution_status():
    global execution_status
    execution_status_dict = dict(execution_status)
    return jsonify(execution_status_dict)


def calculateTimeseries(measurement_id, new_uuid, execution_status, total):
    try:
        process_id = os.getpid()

        with app.app_context():
            measurement = Measurements.query.get(measurement_id)

            bbox = measurement.farm.bbox
            min_long = bbox[0]
            min_lat = bbox[1]
            max_long = bbox[2]
            max_lat = bbox[3]

            coordinates = measurement.farm.coordinates[0][0]
            area_poly = Polygon(coordinates)

            index_min_lat, index_max_lat, index_min_long, index_max_long = get_index_lat_long(min_lat, max_lat,
                                                                                              min_long, max_long)

            if measurement.timeseries is None or len(measurement.timeseries.values) != Config.hours + 1:
                data = []
                measurement_date = datetime.combine(measurement.date, time(10, 00, 0))
                for i in range(0, Config.hours + 1):
                    logger.info(f'[{process_id}] [{measurement.id}] Processing step {i}/{Config.hours}')
                    reference_hour = measurement_date - timedelta(hours=i)
                    formatted_hour = reference_hour.strftime("%Y%m%dZ%H%M")

                    year = str(reference_hour.year)
                    month = f'{reference_hour.month:02}'
                    day = f'{reference_hour.day:02}'

                    url = f'{Config.WCM3_URL}{year}/{month}/{day}/wcm3_d03_{formatted_hour}.nc'

                    value = getConc(url, index_min_lat, index_min_long, index_max_lat, index_max_long, area_poly)

                    data.append({
                        "time": reference_hour.isoformat(),
                        "value": float(value)
                    })

                existing_record = Timeseries.query.get(measurement.id)
                if existing_record is None:
                    new_record = Timeseries(id=measurement.id, values=data)
                    db.session.add(new_record)
                else:
                    existing_record.values = data

                db.session.commit()
            else:
                logger.info(f'[{measurement.id}] Skipping ...')

            with manager.Lock():
                execution_status[new_uuid] = {'status': 'Running ...', 'idx': execution_status[new_uuid]['idx'] + 1, 'total': total}
    except Exception as e:
        logger.error(f"[calculateTimeseries] Thread encountered an error: {e}")


@app.route('/createTimeseries', methods=['POST'])
def createTimeseries():
    id = request.args.get('id')

    def getTimeseries():
        try:
            with app.app_context():
                if id is not None:
                    measurement = Measurements.query.get(id)
                    measurements = [measurement] if measurement is not None else []
                    workers = 1
                else:
                    measurements = Measurements.query.all()
                    workers = multiprocessing.cpu_count()

                measurement_ids = [measurement.id for measurement in measurements]
                total = len(measurement_ids)

                with manager.Lock():
                    new_uuid = str(uuid.uuid4())
                    execution_status[new_uuid] = {'status': 'Started', 'idx': 0, 'total': total}

                logger.info(f"workers: {workers}")
                with ProcessPoolExecutor(max_workers=workers) as executor:
                    futures = [executor.submit(calculateTimeseries, measurement_id, new_uuid, execution_status, total) for measurement_id in measurement_ids]
                    for future in futures:
                        future.result()

                    execution_status[new_uuid] = {'status': 'Completed', 'idx': 0}
        except Exception as e:
            logger.error(f"{e}")

    # Start the long-running function in a separate thread
    with ThreadPoolExecutor() as executor:
        executor.submit(getTimeseries)

    execution_status_dict = dict(execution_status)
    return jsonify(execution_status_dict)


@app.route('/getTimeSeries/<id>', methods=['GET'])
def getTimeSeries(id: int):
    measurement = Measurements.query.get(id)

    # Sample data (replace this with your own time series data)
    def get_timeseries_data():
        times = []
        values = []

        if measurement.timeseries:
            values = measurement.timeseries.values
            times = [entry['time'] for entry in values]
            values = [entry['value'] for entry in values]

        df = pd.DataFrame({'time': times, 'values': values})
        return df

    # Function to generate a time series plot
    def generate_plot(data):
        plt.plot(data['time'], data['values'])
        plt.xlabel('Time [h]')
        plt.ylabel('number of particles')
        plt.title(measurement.site_name)
        plt.grid(False)
        plt.tight_layout()

    # Generate sample data (replace this with your own data retrieval logic)
    timeseries = get_timeseries_data()

    # Generate the plot
    generate_plot(timeseries)

    # Save the plot to a BytesIO object
    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    image_stream.seek(0)

    # Clear the plot to avoid memory leaks
    plt.clf()
    plt.close()

    # Return the plot as an image response
    return send_file(image_stream, mimetype='image/png')
