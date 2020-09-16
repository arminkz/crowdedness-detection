import json
import random
import time
from datetime import datetime
import calendar
import pprint
from flask import Flask, Response, render_template
from flask_mqtt import Mqtt
from flask_pymongo import PyMongo

# init Flask
app = Flask(__name__)
app.config['MQTT_CLIENT_ID'] = 'webserver'
app.config['MQTT_BROKER_URL'] = '127.0.0.1'
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_REFRESH_TIME'] = 1.0  # refresh time in seconds
app.config['MQTT_USERNAME'] = ''
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 5
app.config['MQTT_TLS_ENABLED'] = False
app.config['MQTT_CLEAN_SESSION'] = True
app.config["MONGO_URI"] = "mongodb://localhost:27017/crowd-db"

mongo = PyMongo(app)

mqtt = Mqtt(app)

random.seed()  # Initialize the random number generator


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    mqtt.subscribe('+/wifi')


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    today = datetime.now()

    record = mongo.db.sensor_data.find_one({"dayOfWeek": int(today.weekday()),
                                            "dayOfMonth": int(today.strftime('%d')),
                                            "hour": today.hour})
    if record is None:
        mongo.db.sensor_data.insert_one({"dayOfWeek": int(today.weekday()),
                                         "dayOfMonth": int(today.strftime('%d')),
                                         "hour": today.hour,
                                         "packets": int(message.payload.decode())})
    else:
        mongo.db.sensor_data.update_one({"dayOfWeek": int(today.weekday()),
                                         "dayOfMonth": int(today.strftime('%d')),
                                         "hour": today.hour},
                                        {"$inc": {"packets": int(message.payload.decode())}})


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/chart-data')
def chart_data():
    def generate_random_data():
        while True:
            json_data = json.dumps(
                {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'value': random.random() * 100})
            yield f"data:{json_data}\n\n"
            time.sleep(1)

    # SSE generator
    return Response(generate_random_data(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(host="localhost", port=8000, use_reloader=False)
