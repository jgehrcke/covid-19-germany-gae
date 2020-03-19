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
import io
import tempfile
from time import time
from datetime import datetime

import pandas as pd
import requests
import pytz

from google.cloud import firestore
import google.cloud.exceptions
from flask import Flask, jsonify, abort


ZEIT_JSON_URL = os.environ["ZEIT_JSON_URL"]

app = Flask(__name__)

FBCACHE = firestore.Client().collection("cache")
FBCACHE_NOW_DOC = FBCACHE.document("gernow")
FBCACHE_TIMESERIES_DOC = FBCACHE.document("gerhistory")
FIRSTREQUEST = True

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


@app.route("/")
def rootpath():
    return 'For documentation see <a href="https://github.com/jgehrcke/covid-19-germany-gae">github.com/jgehrcke/covid-19-germany-gae</a>'


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
        return fetch_now_data()

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
            "source": data["source"],
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


STATE_WHITELIST = [
    "DE-BW",
    "DE-BY",
    "DE-BE",
    "DE-BB",
    "DE-HB",
    "DE-HH",
    "DE-HE",
    "DE-MV",
    "DE-NI",
    "DE-NW",
    "DE-RP",
    "DE-SL",
    "DE-SN",
    "DE-ST",
    "DE-SH",
    "DE-TH",
]


METRIC_WHITELIST = ["cases", "deaths"]

METRIC_SUFFIX_MAP = {"cases": "_c", "deaths": "_d"}

TIMESERIES_JSON_OUTPUT_META_DICT = {
    "source": "Official numbers published by public health offices (Gesundheitsaemter) in Germany",
    "info": "https://gehrcke.de/2020/03/covid-19-http-api-german-states-timeseries",
}


@app.route("/timeseries/<state>/<metric>")
def get_timeseries(state, metric):

    if state not in STATE_WHITELIST:
        abort(400, f"Bad state name. Must be one of: {', '.join(STATE_WHITELIST)}")

    if metric not in METRIC_WHITELIST:
        abort(400, f"Bad metric name. Must be one of: {', '.join(METRIC_WHITELIST)}")

    df = get_timeseries_dataframe()

    # Construct column name like DE-BW_c
    column_name = state + METRIC_SUFFIX_MAP[metric]
    output_dict = {
        "data": df[column_name].to_dict(),
        "meta": TIMESERIES_JSON_OUTPUT_META_DICT,
    }
    return jsonify(output_dict)


def get_timeseries_dataframe():
    """
    From, in that order
    - file system cache or (if empty or not fresh)
    - google sheets (HTTP API, csv) or (if not available or erroneous)
    - firebase (fallback)
    """

    maxage_minutes = 15
    cpath = os.path.join(tempfile.gettempdir(), "timeseries.df.cache.pickle")

    # Read from cache if it exists and is not too old.
    if os.path.exists(cpath):
        if time() - os.stat(cpath).st_mtime < 60 * maxage_minutes:
            with open(cpath, "rb") as f:
                log.info("read dataframe from file cache %s", cpath)
                return pd.read_pickle(cpath)

    try:
        df = fetch_timeseries_gsheet_and_construct_dataframe()
    except Exception as err:
        # TODO: if that fails read from firestore (last good state backup)
        raise

    # Atomic switch (in case there are concurrently running threads
    # reading/writing this, too).
    tmppath = cpath + "new"
    log.info("write dataframe (atomic rename) to file cache %s:", tmppath)
    with open(tmppath, "wb") as f:
        df.to_pickle(tmppath)
    os.rename(tmppath, cpath)

    with open(cpath, "rb") as f:
        byteseq = f.read()
        log.info(
            "write dataframe to firebase (last good state backup), %s bytes",
            len(byteseq),
        )
        FBCACHE_TIMESERIES_DOC.set({"dataframe.pickle": byteseq})

    return df


def fetch_timeseries_gsheet_and_construct_dataframe():
    dockey = os.environ["FEDSTATE_TIMESERIES_GSHEET_KEY"]
    docid = os.environ["FEDSTATE_TIMESERIES_GSHEET_ID"]
    url = (
        f"https://docs.google.com/spreadsheets/d/{dockey}/export?format=csv&gid={docid}"
    )
    log.info("read csv data from google sheets: %s", url)
    resp = requests.get(url)
    resp.raise_for_status()

    df = pd.read_csv(io.StringIO(resp.text))
    df = df.dropna()
    # print(df)

    # datetimes = []
    datetime_strings = []
    for _, row in df.iterrows():
        ts = datetime(
            2020,
            int(row["month"]),
            int(row["day"]),
            int(row["hour"]),
            int(row["min"]),
            0,
            0,
        )

        ts = pytz.timezone("Europe/Amsterdam").localize(ts)
        tsstring = ts.isoformat()
        # datetimes.append(ts)
        datetime_strings.append(tsstring)

    # Using the iso8601 time strings as index has the advantage that individual
    # colunmns (Series objects) are JSON-encode-ready by just doing
    df.index = datetime_strings
    df.drop(["month", "day", "hour", "min"], axis=1, inplace=True)
    return df




def get_fresh_now_data_from_zeit():
    url = f"{ZEIT_JSON_URL}?time={int(time())}"
    log.info("try to get current case count for germany from zeit online")

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

    return {
        "cases": ttls["count"],
        "deaths": ttls["dead"],
        "recovered": ttls["recovered"],
        "time_source_last_updated_iso8601": t_source_last_updated.isoformat(),
        "t_obtained_from_source": time(),
        "source": "ZEIT ONLINE (aggregated data from individual ministries of health in Germany)",
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
