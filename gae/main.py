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
import pickle
import uuid
from time import time
from datetime import datetime

import pandas as pd
import requests
import pytz

from google.cloud import firestore
import google.cloud.exceptions
from flask import Flask, jsonify, abort


app = Flask(__name__)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

ZEIT_JSON_URL = os.environ["ZEIT_JSON_URL"]
BE_MOPO_CSV_URL = os.environ["BE_MOPO_CSV_URL"]
FBCACHE = firestore.Client().collection("cache")
FBCACHE_NOW_DOC = FBCACHE.document("gernow")
FBCACHE_TIMESERIES_DOC = FBCACHE.document("gerhistory")
FS_CACHE_SUFFIX = uuid.uuid4().hex

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

    data = get_now_data_from_cache()

    # Generate timezone-aware ISO 8601 timestring indicating when the external
    # source was last polled. Put it into Germany's timezone.
    t_consulted_ger_tz_iso8601 = (
        pytz.timezone("Europe/Amsterdam")
        .localize(datetime.fromtimestamp(int(data["t_obtained_from_source"])))
        .isoformat()
    )

    output_dict = {
        "current_totals": {
            "cases": data["cases"],
            "deaths": data["deaths"],
            "recovered": data["recovered"],
            "tested": "unknown",
        },
        "meta": {
            "source": data["source"],
            "info": "https://github.com/jgehrcke/covid-19-germany-gae",
            "contact": "Dr. Jan-Philip Gehrcke, jgehrcke@googlemail.com",
            "time_source_last_updated_iso8601": data[
                "time_source_last_updated_iso8601"
            ],
            "time_source_last_consulted_iso8601": t_consulted_ger_tz_iso8601,
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

METRIC_SUFFIX_MAP = {"cases": "_cases", "deaths": "_deaths"}

TIMESERIES_JSON_OUTPUT_META_DICT = {
    "source": "Official numbers published by public health offices (Gesundheitsaemter) in Germany",
    "info": "https://github.com/jgehrcke/covid-19-germany-gae",
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
        "data": [{time: value} for time, value in df[column_name].to_dict().items()],
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
    cpath = os.path.join(
        tempfile.gettempdir(), f"timeseries.df.cache.pickle-{FS_CACHE_SUFFIX}"
    )

    # Read from cache if it exists and is not too old.
    if os.path.exists(cpath):
        if time() - os.stat(cpath).st_mtime < 60 * maxage_minutes:
            with open(cpath, "rb") as f:
                log.info("read dataframe from file cache %s", cpath)
                return pd.read_pickle(cpath)

    try:
        df = fetch_timeseries_csv_and_construct_dataframe()
    except Exception as err:
        # Fall back to reading from firestore (last good state backup)
        log.exception("err during timeseries fetch: %s", err)
        log.info("falling back to firebase state for timeseries data")
        return pickle.loads(FBCACHE_TIMESERIES_DOC.get().to_dict()["dataframe.pickle"])

    # Atomic switch (in case there are concurrently running threads
    # reading/writing this, too).
    tmppath = cpath + "_new"
    log.info("write dataframe (atomic rename) to file cache %s:", tmppath)
    with open(tmppath, "wb") as f:
        df.to_pickle(tmppath)

    try:
        os.rename(tmppath, cpath)
    except FileNotFoundError:
        # another racer switched the file underneath us
        log.info("atomic file switch: congrats, a rare case happened!")

    with open(cpath, "rb") as f:
        byteseq = f.read()
        log.info(
            "write dataframe to firebase (last good state backup), %s bytes",
            len(byteseq),
        )
        FBCACHE_TIMESERIES_DOC.set({"dataframe.pickle": byteseq})

    return df


def fetch_timeseries_csv_and_construct_dataframe():
    url = "https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/data.csv"
    log.info("read csv data from github: %s", url)
    resp = requests.get(url)
    resp.raise_for_status()

    # Using the iso8601 time strings as index has the advantage that individual
    # colunmns (Series objects) are JSON-encode-ready by just doing
    # `Series.to_dict()` yields an ordered map of timestamp:value pairs.
    df = pd.read_csv(io.StringIO(resp.text), index_col=["time_iso8601"])
    df = df.dropna()
    return df


def get_now_data_from_cache():
    """
    From, in that order
    - file system cache or (if empty or not fresh)
    - google sheets (HTTP API, csv) or (if not available or erroneous)
    - firebase (fallback)
    """
    maxage_minutes = 15
    cpath = os.path.join(tempfile.gettempdir(), f"now.pickle.cache-{FS_CACHE_SUFFIX}")

    # Read from cache if it exists and is not too old.
    if os.path.exists(cpath):
        if time() - os.stat(cpath).st_mtime < 60 * maxage_minutes:
            with open(cpath, "rb") as f:
                log.info("read /now data from file cache %s", cpath)
                return pickle.load(f)

    try:
        datadict = fetch_fresh_now_data()
    except Exception as err:
        # Fall back to reading from firestore (last good state backup)
        log.exception("err during /now fetch: %s", err)
        log.info("falling back to firebase state")
        return pickle.loads(FBCACHE_NOW_DOC.get().to_dict()["now.pickle"])

    # Atomic switch (in case there are concurrently running threads
    # reading/writing this, too).
    tmppath = cpath + "_new"
    log.info("write /now data (atomic rename) to file cache %s:", tmppath)
    with open(tmppath, "wb") as f:
        pickle.dump(datadict, f, protocol=pickle.HIGHEST_PROTOCOL)

    try:
        os.rename(tmppath, cpath)
    except FileNotFoundError:
        # another racer switched the file underneath us
        log.info("atomic file switch: congrats, a rare case happened!")

    with open(cpath, "rb") as f:
        byteseq = f.read()
        log.info(
            "write /now data to firebase (last good state backup), %s bytes",
            len(byteseq),
        )
        FBCACHE_NOW_DOC.set({"now.pickle": byteseq})

    return datadict


def fetch_fresh_now_data():

    data1 = None
    data2 = None

    try:
        data1 = get_fresh_now_data_from_zeit()
    except Exception as err:
        log.exception("err during ZO /now fetch: %s", err)

    try:
        data2 = get_fresh_now_data_from_be_mopo()
    except Exception as err:
        log.exception("err during BM /now fetch: %s", err)

    # If one of the sources let us down, short-cut to returning data from
    # the other right away.
    if data1 is None:
        return data2

    if data2 is None:
        return data1

    # Got data from both. Use more recent or use higher case count?
    if data1["time_source_last_updated"] > data2["time_source_last_updated"]:
        log.info("zeit online data appears to be more recent")
    else:
        log.info("bemopo data appears to be more recent")

    if data1["cases"] > data2["cases"]:
        log.info("zeit online data reports more cases")
        return data1

    else:
        log.info("bemopo data reports more cases")
        return data2


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

    t_source_last_updated = parse_zo_timestring_into_dt(data["changeTimestamp"])

    return {
        "cases": ttls["count"],
        "deaths": ttls["dead"],
        "recovered": ttls["recovered"],
        "time_source_last_updated_iso8601": t_source_last_updated.isoformat(),
        "time_source_last_updated": t_source_last_updated.timestamp(),
        "t_obtained_from_source": time(),
        "source": "ZEIT ONLINE (aggregated data from individual ministries of health in Germany)",
    }


def get_fresh_now_data_from_be_mopo():
    url = f"{BE_MOPO_CSV_URL}?{int(time())}"
    log.info("try to get current case count for germany from berliner mopo")

    for attempt in (1, 2, 3):
        # TODO: back-off, but only when this is not in hot path
        try:
            resp = requests.get(url, timeout=(3.05, 10))
            resp.raise_for_status()
        except Exception as err:
            log.info("attempt %s: failed getting data: %s", attempt, err)

    df = pd.read_csv(io.StringIO(resp.text))
    df = df.dropna()
    df = df[df["parent"].str.match("Deutschland")]
    t_source_last_updated = pd.to_datetime(df["date"]).max()

    return {
        "cases": int(df["confirmed"].sum()),
        "deaths": int(df["deaths"].sum()),
        "recovered": int(df["recovered"].sum()),
        "time_source_last_updated_iso8601": t_source_last_updated.isoformat(),
        "time_source_last_updated": t_source_last_updated.timestamp(),
        "t_obtained_from_source": time(),
        "source": "Berliner Morgenpost (aggregated data from individual ministries of health in Germany)",
    }


def parse_zo_timestring_into_dt(timestring):
    # This timestamp is a string of the following format:
    #
    #    '17. März 2020, 21:22 Uhr'
    #
    # This is pretty horrible as an interface, but of course we can work
    # on that, yolo! But let's not plan into the future longer than May.
    # Who would need that, right?
    #
    # Update: the time format was then changed to
    #
    #    22. März 2020, 13.55 Uhr
    #
    # Update2: and switched back again. Yeah, it's fun to consume an
    # implementation detail.
    ts = timestring
    ts = ts.replace("März", "03").replace("April", "04").replace("Mai", "05")
    ts = ts.replace(",", "").replace(".", "").replace(":", "")

    # This crashes if our parsing is too brittle or if they change their data
    # format. Let it crash in that case. TODO: make error paths robust, don't
    # expose to HTTP clients.
    t = datetime.strptime(ts, "%d %m %Y %H%M Uhr")

    # `t_source_last_updated` is so far not timezone-aware (no timezone set).
    # Set the Amsterdam/Berlin tz explicitly (which is what the authors of this
    # JSON doc imply).
    t = pytz.timezone("Europe/Amsterdam").localize(t)
    return t


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
