# MIT License

# Copyright (c) 2020 Dr. Jan-Philip Gehrcke

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
This program is part of https://github.com/jgehrcke/covid-19-germany-gae
"""

import os
import logging
import sys
import re
from time import time
from datetime import datetime

import requests
import pytz

from google.cloud import firestore
import google.cloud.exceptions
from flask import Flask, jsonify


ZEIT_JSON_URL = os.environ["ZEIT_JSON_URL"]

app = Flask(__name__)
FBCACHE = firestore.Client().collection("cache")
FBCACHE_NOW_DOC = FBCACHE.document("gernow")
FIRSTREQUEST = True

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)

# Note(JP): serve this from a thread pool and add another cross-thread caching
# layer using https://github.com/dgilland/cacheout. For serving from multiple
# threads use the GAE entrypoint configuration parameter, and either serve via
# gunicorn's threaded worker or use uwsgi's thread worker.


@app.route("/now")
def germany_now():

    cache_max_age_seconds = 300

    # Clear db cache upon first request after re-deployment.
    global FIRSTREQUEST
    if FIRSTREQUEST:
        try:
            log.info('invalidate cache for "now" doc')
            FBCACHE_NOW_DOC.delete()
        except Exception as err:
            log.warning("cache invalidation failed: %s", err)
        FIRSTREQUEST = False

    t_current = time()

    def _get_data():
        """
        Fetch fresh data from external source.
        Create the dictionary to be injected via firebase client.
        """
        cases, deaths, recovered, t_source_last_updated = get_fresh_data()
        return {
            "cases": cases,
            "deaths": deaths,
            "recovered": recovered,
            "time_source_last_updated_iso8601": t_source_last_updated.isoformat(),
            "t_obtained_from_source": t_current,  #
        }

    cdata = FBCACHE_NOW_DOC.get()

    if cdata.exists:

        log.info("db cache hit")
        data = cdata.to_dict()

        if (
            "t_obtained_from_source" not in data
            or (t_current - data["t_obtained_from_source"]) > cache_max_age_seconds
        ):
            log.info("db cache expired, get fresh data")
            data = _get_data()
            log.info("got data dict: %s", data)
            FBCACHE_NOW_DOC.update(data)

    else:
        log.info("db cache miss, get fresh data, store to db")
        data = _get_data()
        log.info("got data dict: %s", data)
        FBCACHE_NOW_DOC.set(data)

    # mangle `data` dict (obtained from DB cache) into the state that we want
    # to return to HTTP clients. It's OK to not deep-copy here, any mutation
    # allowed.
    output_dict = {
        "current_totals": {
            "cases": data["cases"],
            "deaths": data["deaths"],
            "recovered": data["recovered"],
            "tested": "unknown",
        },
        "meta": {
            "source": "ZEIT ONLINE (aggregated data from individual ministries of health in Germany)",
            "contact": "Dr. Jan-Philip Gehrcke, jgehrcke@googlemail.com",
            "time_source_last_updated_iso8601": data[
                "time_source_last_updated_iso8601"
            ],
            "time_source_last_consulted_iso8601": datetime.fromtimestamp(
                int(data["t_obtained_from_source"]), pytz.utc
            ).isoformat(),
        },
    }

    # Generate HTTP response with JSON body
    return jsonify(output_dict)


@app.route("/")
def rootpath():
    return "Brorona! See /now"


def get_fresh_data():
    url = f"{ZEIT_JSON_URL}?time={int(time())}"
    log.info("try to get current case count for germany")

    # today = datetime.utcnow().strftime("%Y-%m-%d")

    resp = requests.get(url, timeout=(3.05, 10))
    resp.raise_for_status()
    data = resp.json()

    # First let's see that data is roughly in the shape that's expected
    ttls = data["totals"]
    assert "count" in ttls
    assert "dead" in ttls
    assert "recovered" in ttls

    # Now let's see when this was last updated.
    # This timestamp is a string of the following format:
    #
    #    '17. März 2020, 21:22 Uhr'
    #
    # This is pretty horrible as an interface, but of course we can work
    # on that, yolo! But let's not plan into the future longer than May.
    # Who would need that, right?
    t = data["changeTimestamp"]
    t = t.replace("März", "03").replace("April", "04").replace("Mai", "05")
    t = t.replace(",", "").replace(".", "")

    try:
        t_source_last_updated = datetime.strptime(t, "%d %m %Y %H:%M Uhr")
    except ValueError as err:
        log.error(
            "could not parse changeTimestamp %s: %s", data["changeTimestamp"], err
        )

    # `t_source_last_updated` is so far not timezone-aware (no timezone set).
    # Set the Amsterdam/Berlin tz explicitly (which is what the authors of this
    # JSON doc imply).
    t_source_last_updated = pytz.timezone("Europe/Amsterdam").localize(
        t_source_last_updated
    )

    return ttls["count"], ttls["dead"], ttls["recovered"], t_source_last_updated


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
