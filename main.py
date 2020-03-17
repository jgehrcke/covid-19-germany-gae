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
import time
from datetime import datetime

import requests

from google.cloud import firestore
import google.cloud.exceptions
from flask import Flask, jsonify

# firebase_admin.initialize_app()
CACHE = firestore.Client().collection("cache")

CACHE_MAX_AGE_SECONDS = 300

ZEIT_JSON_URL = os.environ["ZEIT_JSON_URL"]

app = Flask(__name__)

logging.basicConfig(
    format="%(asctime)s,%(msecs)-6.1f|%(module)s# %(message)s", datefmt="%H:%M:%S"
)
log = logging.getLogger()
log.setLevel(logging.INFO)


@app.route("/germany/now")
def germany_now():
    ckey = "gernow"
    cdoc = CACHE.document(ckey)
    cdata = cdoc.get()

    if cdata.exists:
        log.info("cache hit")
        data = cdata.to_dict()
        if (time.time() - data["timestamp"]) > CACHE_MAX_AGE_SECONDS:
            log.info("cache expiry")
            count = get_case_count_germany()
            cdoc.update({"count": count, "timestamp": time.time()})
        count = data["count"]
    else:
        log.info("cache miss")
        count = get_case_count_germany()
        cdoc.set({"count": count, "timestamp": time.time()})

    return jsonify({"total_cases_confirmed_until_now": count})


@app.route("/")
def rootpath():
    return "brorona"


def get_case_count_germany():
    url = f"{ZEIT_JSON_URL}?time={int(time.time())}"
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
