# MIT License

# Copyright (c) 2020 - 2021 Dr. Jan-Philip Gehrcke -- https://gehrcke.de

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
This module is part of https://github.com/jgehrcke/covid-19-germany-gae
"""

import logging

import pandas as pd

log = logging.getLogger(__file__)


def parse_csv_timeseries(path):
    log.info("parse CSV file at %s", path)
    df = pd.read_csv(
        path,
        index_col=["time_iso8601"],
        # Rely on this column to have ISO 8601 timestamp notation.
        parse_dates=["time_iso8601"],
        # Allow for parsing ISO 8601 timestamp with mixed timezones.
        date_parser=lambda col: pd.to_datetime(col, utc=True),
    )
    df.index.name = "time"
    return df


def write_csv_timeseries(df, path, float_format=None):
    """
    For when `float_format` might matter, see for instance:
        https://github.com/pandas-dev/pandas/issues/13159
        https://github.com/pandas-dev/pandas/issues/16452

    Use this with e.g. `float_format='%.6f'`
    """
    # Take control of string-encoding the tz-aware timestamps.
    df.index = df.index.strftime("%Y-%m-%dT%H:%M:%S%z")
    # Change index label name to express that these strings are using ISO 8601
    # notation.
    df.index.name = "time_iso8601"
    log.info("write time series data to CSV file %s", path)
    with open(path, "wb") as f:
        f.write(df.to_csv(float_format=float_format).encode("utf-8"))
