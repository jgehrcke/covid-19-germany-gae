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


CACHE_MAX_AGE_SECONDS = 300
ZEIT_JSON_URL = os.environ["ZEIT_JSON_URL"]

app = Flask(__name__)
CACHE = firestore.Client().collection("cache")

log = logging.getLogger()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d %(levelname)s: %(message)s",
    datefmt="%y%m%d-%H:%M:%S",
)


@app.route("/germany/now")
def germany_now():
    ckey = "gernow"
    cdoc = CACHE.document(ckey)
    cdata = cdoc.get()
    t_current = time()

    if cdata.exists:

        log.info("db cache hit")
        data = cdata.to_dict()

        if (t_current - data["timestamp"]) > CACHE_MAX_AGE_SECONDS:
            log.info("db cache expired, get fresh data")
            count = get_case_count_germany()
            data = {"count": count, "timestamp": t_current}
            cdoc.update(data)

    else:
        log.info("db cache miss, get fresh data, store to db")
        count = get_case_count_germany()
        data = {"count": count, "timestamp": t_current}
        cdoc.set(data)

    return jsonify(
        {
            "total_cases_confirmed_until_now": data["count"],
            "last_update_from_source_iso8601": datetime.fromtimestamp(
                int(data["timestamp"]), pytz.utc
            ).isoformat(),
            "source": "zeit.de",
        }
    )


@app.route("/")
def rootpath():
    return "Brorona! See /germany/now"


def get_case_count_germany():
    url = f"{ZEIT_JSON_URL}?time={int(time())}"
    log.info("try to get current case count for germany")

    today = datetime.utcnow().strftime("%Y-%m-%d")

    resp = requests.get(url, timeout=(3.05, 10))
    resp.raise_for_status()
    data = resp.json()

    for sample in data["chronology"]:
        if "date" in sample:
            if sample["date"] == today:
                log.info("sample for today: %s", sample["count"])
                return sample["count"]

    raise Exception("unexpected data shape: %s", data)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
