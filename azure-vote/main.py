from flask import Flask, request, render_template
import os
import random
import redis
import socket
import sys
import logging
from datetime import datetime

from opencensus.ext.azure.log_exporter import AzureLogHandler, AzureEventHandler

az_log_logger = logging.getLogger(f'{__name__}-log')
az_event_logger = logging.getLogger(f'{__name__}-event')

az_log_logger.setLevel(logging.INFO)
az_event_logger.setLevel(logging.INFO)

az_log_logger.addHandler(AzureLogHandler(connection_string='InstrumentationKey=1a84096a-dfc6-4e86-80d8-85b87eba371f;IngestionEndpoint=https://eastasia-0.in.applicationinsights.azure.com/;LiveEndpoint=https://eastasia.livediagnostics.monitor.azure.com/'))
az_event_logger.addHandler(AzureEventHandler(connection_string='InstrumentationKey=1a84096a-dfc6-4e86-80d8-85b87eba371f;IngestionEndpoint=https://eastasia-0.in.applicationinsights.azure.com/;LiveEndpoint=https://eastasia.livediagnostics.monitor.azure.com/'))

app = Flask(__name__)

# Load configurations from environment or config file
app.config.from_pyfile('config_file.cfg')

if ("VOTE1VALUE" in os.environ and os.environ['VOTE1VALUE']):
    button1 = os.environ['VOTE1VALUE']
else:
    button1 = app.config['VOTE1VALUE']

if ("VOTE2VALUE" in os.environ and os.environ['VOTE2VALUE']):
    button2 = os.environ['VOTE2VALUE']
else:
    button2 = app.config['VOTE2VALUE']

if ("TITLE" in os.environ and os.environ['TITLE']):
    title = os.environ['TITLE']
else:
    title = app.config['TITLE']

# Redis Connection
r = redis.Redis()

# Change title to host name to demo NLB
if app.config['SHOWHOST'] == "true":
    title = socket.gethostname()

# Init Redis
if not r.get(button1): r.set(button1,0)
if not r.get(button2): r.set(button2,0)

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'GET':

        # Get current values
        vote1 = r.get(button1).decode('utf-8')
        vote2 = r.get(button2).decode('utf-8')
        properties = {
            'custom_dimensions': {
                'Cats vote': vote1,
                'Dogs vote': vote2
            }
        }
        az_log_logger.info('User voted', extra=properties)

        # Return index with values
        return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

    elif request.method == 'POST':

        if request.form['vote'] == 'reset':

            # Empty table and return results
            r.set(button1,0)
            r.set(button2,0)
            az_log_logger.info('User reset')
            az_event_logger.info('User reset')

            return render_template("index.html", value1=0, value2=0, button1=button1, button2=button2, title=title)

        else:

            # Insert vote result into DB
            vote = request.form['vote']
            r.incr(vote,1)
            az_event_logger.info(f'{vote} voted')

            # Get current values
            vote1 = r.get(button1).decode('utf-8')

            vote2 = r.get(button2).decode('utf-8')

            # Return results
            return render_template("index.html", value1=int(vote1), value2=int(vote2), button1=button1, button2=button2, title=title)

if __name__ == "__main__":
    # app.run() 
    app.run(host='0.0.0.0', threaded=True, debug=True) # remote
