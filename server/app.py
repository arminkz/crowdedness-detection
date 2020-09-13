import json
import random
import time
from datetime import datetime

from flask import Flask, Response, render_template

app = Flask(__name__)
app.config["DEBUG"] = True
random.seed()  # Initialize the random number generator


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
    app.run(host="localhost", port=8000, debug=True, threaded=True)
