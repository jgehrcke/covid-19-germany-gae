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
import json
from time import time
from datetime import datetime

import pandas as pd
import requests
import pytz

from google.cloud import firestore
import google.cloud.exceptions
from flask import Flask, jsonify, abort, Response
import flask

app = Flask(__name__)

app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

ZEIT_JSON_URL = os.environ["ZEIT_JSON_URL"]
BE_MOPO_CSV_URL = os.environ["BE_MOPO_CSV_URL"]

FIRESTORE = firestore.Client().collection("cache")
FS_NOW_DOC = FIRESTORE.document("gernow-2")
FS_TIMESERIES_DOC = FIRESTORE.document("gerhistory-2")


log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


@app.route("/_tasks/update_now")
def task_update_now():
    if flask.request.headers.get("X-Appengine-Cron") or app.debug:
        CACHE_NOW.refresh()
        return "Accepted, Sir", 202
    abort(403, "go away")


@app.route("/_tasks/update_timeseries")
def task_update_timeseries():
    if flask.request.headers.get("X-Appengine-Cron") or app.debug:
        CACHE_TIMESERIES.refresh()
        return "Accepted, Sir", 202
    abort(403, "go away")


@app.route("/")
def rootpath():
    return 'For documentation see <a href="https://github.com/jgehrcke/covid-19-germany-gae">github.com/jgehrcke/covid-19-germany-gae</a>'


@app.route("/now")
def germany_now():
    # Cached value is JSON text, encoded into a byte sequences via.
    return Response(CACHE_NOW.get(), content_type="application/json; charset=utf-8")


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

    df = CACHE_TIMESERIES.get()

    # Construct column name like DE-BW_c
    column_name = state + METRIC_SUFFIX_MAP[metric]
    output_dict = {
        "data": [{time: value} for time, value in df[column_name].to_dict().items()],
        "meta": TIMESERIES_JSON_OUTPUT_META_DICT,
    }
    return jsonify(output_dict)


class Cache:
    """
    This cache is special in that it is not invalidated. It is only refreshed
    explicitly, and read. A warning/error is emitted when it it stale upon
    reading.

    The read path is simple, and does not include transient error paths.

    The write path is complex, but is never part of processing consumer HTTP
    requests. The write path is triggered only by GAE cron jobs.

    If a fresh instance of this app comes up and neither has a local file
    system cache entry nor can it consult the external sources (for which ever
    rare reason) then fall back to using the last known good state in
    Firestore.
    """

    def __init__(self, name, fbdoc):
        # Warn when the entry is older than that upon reading
        self.maxage_seconds = 15 * 60
        self.fbdoc = fbdoc

        self.picklekey = f"{name}.pickle"

        # The currenly held value: None: not initialized. 2-tuple: first item
        # time, second item payload Remember: tuple is immutalbe (atomic
        # switching happens). A note on thread safety: on CPython the lookup of
        # `self.current_value` is through a dictionary, and changing the value
        # is atopic. Looking the value up is atomic, too. Even if unpacking the
        # value upon lookup through tuple unpacking there is no danger to get a
        # corrupted view.
        self.current_value = (None, None)

    def get(self):

        (valtime, val) = self.current_value

        if val is None:
            # During app init this code path can be entered by more than one
            # thread. Could be optimized, but does not lead to incorrect
            # behavior: we let more than one racer start, and all of the racers
            # will try setting the initial value. The slowest one wins (that's
            # not how things are in real life, right?).
            log.info("%s: not yet set, _refresh()", self)
            self.refresh()

            # `refresh()` above either errors out or has the guaranteed side
            # effect of leaving behind a `current_value`.
            (valtime, val) = self.current_value

        age_seconds = time() - valtime
        if age_seconds > self.maxage_seconds:
            log.warning("%s cache is stale: %s s", self, age_seconds)

        return val

    def _set_value_from_firestore_backup(self):
        log.info("%s: falling back to fetching firestore state", self)
        old_backup_dict = self.fbdoc.get().to_dict()
        backup_value = pickle.loads(old_backup_dict[self.picklekey])
        backup_time = old_backup_dict["time"]
        age_seconds = time() - backup_time
        log.info("%s: got value from firestore (age: %s s", self, age_seconds)

        # Atomically set what we've got.
        self.current_value = (backup_time, backup_value)

    def refresh(self):

        curtime = time()
        log.info("%s: refresh triggered", self)

        # `newval` can be a dict, or a pandas dataframe, anything pickleable.
        try:
            newval = self.fetch_func()
        except Exception as err:
            log.exception("%s: error during fetch", self)
            if self.current_value is not None:
                log.info("%s: keep current cache value", self)
            else:
                self._set_value_from_firestore_backup()
                # Consumers rely on the fact that when _refresh() does not
                # error out, that the current value is _not_ the initial value
                # anymore, i.e. that either the actual refresh or the restore
                # from backup have succeeded.
                return

        # Atomically set what we've got (for other racers to potentially
        # consume this already).
        self.current_value = (curtime, newval)

        byteseq = pickle.dumps(newval, protocol=pickle.HIGHEST_PROTOCOL)
        log.info("%s: write backup to firestore, %s bytes", self, len(byteseq))
        backup_dict = {"time": curtime, self.picklekey: byteseq}

        try:
            # I have seen this fail transiently with
            # google.api_core.exceptions.ServiceUnavailable: 503 Connection reset by peer
            FS_NOW_DOC.set(backup_dict)
        except Exception as err:
            log.exception("%s: err during firestore set(): %s", self, err)
            # Not being able to set a fresh backup is sad, but not fatal.

    def __str__(self):
        return self.__class__.__name__


class CacheTimeseries(Cache):
    def fetch_func(self):
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


class CacheNow(Cache):
    def fetch_func(self):
        def _to_json_doc(data):
            log.info("%s: serialize data to JSON", self)
            # Generate timezone-aware ISO 8601 timestring indicating when the
            # external source was last polled. Put it into Germany's timezone.
            t_consulted_ger_tz_iso8601 = datetime.fromtimestamp(
                int(data["t_obtained_from_source"]),
                tz=pytz.timezone("Europe/Amsterdam"),
            ).isoformat()

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

            return json.dumps(output_dict, indent=2, ensure_ascii=False).encode("utf-8")

        data_zo = None
        data_mopo = None

        try:
            data_zo = get_fresh_now_data_from_zeit()
        except Exception as err:
            log.exception("err during ZO /now fetch: %s", err)

        try:
            data_mopo = get_fresh_now_data_from_be_mopo()
        except Exception as err:
            log.exception("err during BM /now fetch: %s", err)

        # If one of the sources let us down, short-cut to returning data from
        # the other right away.
        if data_zo is None:
            return _to_json_doc(data_zo)

        if data_mopo is None:
            return _to_json_doc(data_mopo)

        # Got data from both. Use more recent or use higher case count?
        if data_zo["time_source_last_updated"] > data_mopo["time_source_last_updated"]:
            log.info("zeit online data appears to be more recent")
        else:
            log.info("bemopo data appears to be more recent")

        if data_zo["cases"] > data_mopo["cases"]:
            log.info("zeit online data reports more cases")
            return _to_json_doc(data_zo)

        else:
            log.info("bemopo data reports more cases")
            return _to_json_doc(data_mopo)


def get_fresh_now_data_from_zeit():
    def _parse_zo_timestring_into_dt(timestring):
        # This is the third iteration already, as ZO changes their implementation
        # often. They came to reason and now use ISO 8601.
        return datetime.strptime(timestring, "%Y-%m-%dT%H:%M:%S%z")

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

    t_source_last_updated = _parse_zo_timestring_into_dt(data["lastUpdate"])

    return {
        "cases": ttls["count"],
        "deaths": ttls["dead"],
        "recovered": ttls["recovered"],
        "time_source_last_updated_iso8601": t_source_last_updated.isoformat(),
        "time_source_last_updated": t_source_last_updated.timestamp(),
        "t_obtained_from_source": time(),
        "source": "ZEIT ONLINE (aggregated data from individual Landkreise in Germany)",
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


CACHE_NOW = CacheNow("now", FS_NOW_DOC)
CACHE_TIMESERIES = CacheTimeseries("ts", FS_TIMESERIES_DOC)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
