# -*- coding:utf8 -*-
# !/usr/bin/env python
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from future.standard_library import install_aliases

install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

import wikipedia

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processrequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processrequest(req):
    if req.get("result") is None:
        return {}

    if req.get("result").get("action") == "yahooWeatherForecast":
        return processweatheraction(req)
    elif req.get("result").get("action") == "wikiDataInformation":
        return processwikiAction(req)

    else:
        return {}


def processweatheraction(req):
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    yql_query = makeYqlQuery(req)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    result = urlopen(yql_url).read()
    data = json.loads(result)
    res = makeWebhookResult(data)
    return res


# -----------------wiki requests--------starts
def processwikiAction(req):
    result = makeWikiQuery(req)
    if result is None:
        return makeEmptyResult()
    else:
        res = makeWikiWebhookResult(result)
    return res


def makeWikiQuery(req):
    response = ""

    result = req.get("result")
    parameters = result.get("parameters")

    query = ""

    if parameters.get("any") != "":
        query = parameters.get("any")
    elif parameters.get("given-name") != "":
        query = parameters.get("given-name")

    if query is None:
        return None

    try:
        wikipedia.set_lang("en")
        response = wikipedia.summary(query, sentences=1)
    except:
        response = None

    return response


def makeWikiWebhookResult(wikiResponseText):
    speech = "According to Wikipedia: " + wikiResponseText

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "wiki"
    }


def makeEmptyResult():
    return {
        "speech": "Sorry..I didn't get that",
        "displayText": "Sorry..Unable to fetch result",
        # "data": data,
        # "contextOut": [],
        "source": "wiki"
    }


# -----------------wiki requests--------ends


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "') and u = 'c'"


def makeWebhookResult(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    unitsText = units.get('temperature')

    if (units.get('temperature') in ["c", "C"]):
        unitsText = "celcius"

    speech = "Today in " + location.get('city') + ": " + condition.get('text') + \
             ", the temperature is " + condition.get('temp') + " degree " + unitsText

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
