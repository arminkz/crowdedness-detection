import json
import random
import time
import config
from predictor import predict
from datetime import datetime
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
    def send_crowd_data():
        while True:
            today = datetime.now()
            data = []
            pdata = []
            for r in mongo.db.sensor_data.find().sort([("dayOfMonth", -1), ("hour", -1)]).skip(1).limit(5):
                data.append({'time': r['hour'], 'value': r['packets']})

            # predict next 5 hours
            predict_input = []
            last = mongo.db.sensor_data.find().sort([("dayOfMonth", -1), ("hour", -1)]).limit(1)[0]
            pdom = last['dayOfMonth']
            pdow = last['dayOfWeek']
            phour = last['hour']
            for h in range(5):
                predict_input.append({'dayOfMonth': pdom, 'dayOfWeek': pdow, 'hour': phour})
                phour += 1
                if phour > 24:
                    pdow += 1
                    phour = 0
                    if pdow > 6:
                        pdom = (pdom + 1) % 30
                        pdow = 0
            predict_out = predict(predict_input)
            for po in range(len(predict_input)):
                po_hour = predict_input[po]['hour']
                pdata.append({'time': po_hour, 'value': predict_out[po]})

            json_data = json.dumps({'past': list(reversed(data)), 'future': pdata})

            yield f"data:{json_data}\n\n"
            time.sleep(120)

    # SSE generator
    return Response(send_crowd_data(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(host="localhost", port=8000, use_reloader=False)
