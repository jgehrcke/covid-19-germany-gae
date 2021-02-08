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
Timeseries analytics.

This module is part of https://github.com/jgehrcke/covid-19-germany-gae
"""


import logging

import pandas as pd


log = logging.getLogger(__file__)


def build_daily_change_rate_rolling_window(
    df, column, window_width_days, sum_over_time_window=False
):
    """
    `column`: supposed to be a column name (must be present in `df`) that
    contains a time series (e.g. case count, or death count).

    `window_width_days`: rolling window width, in days

    `sum_over_time_window`: if set to True, return a series that contains the
    sum over the entire rolling window width,i.e. the values of the returned
    series have the unit [X per N days]. If set to `False` (the default),
    normalize by the rolling window width, i.e. the values of the returned
    series have the unit [X per day].
    """

    # Get time differences (unit: seconds) in the  `df`s DatetimeIndex. `dt`
    # is a magic accessor that yields an array of time deltas:
    # https://pandas.pydata.org/docs/reference/api/pandas.Series.dt.html
    dt_seconds = pd.Series(df.index).diff().dt.total_seconds()

    # Construct new series with original DatetimeIndex as index and time
    # differences as values. But this time with unit [days].
    dt_days = pd.Series(dt_seconds) / 86400.0
    dt_days.index = df.index

    # To show what the previous three lines of code actually did:
    #
    # Example input `df`:
    #
    #                         1001 ...  sum_cases
    # time                            ...
    # 2020-03-02 17:00:00+00:00     0 ...        209
    # 2020-03-03 17:00:00+00:00     0 ...        294
    # 2020-03-04 17:00:00+00:00     0 ...        448
    # ...                         ... ...        ...
    # 2021-01-14 17:00:00+00:00   712 ...    2008598
    # 2021-01-15 17:00:00+00:00   736 ...    2025312
    # 2021-01-16 17:00:00+00:00   745 ...    2033518
    #
    # Example resulting `dt_days` series:
    #
    # time
    # 2020-03-02 17:00:00+00:00    NaN
    # 2020-03-03 17:00:00+00:00    1.0
    # 2020-03-04 17:00:00+00:00    1.0
    #                             ...
    # 2021-01-14 17:00:00+00:00    1.0
    # 2021-01-15 17:00:00+00:00    1.0
    # 2021-01-16 17:00:00+00:00    1.0
    #
    # That is, the values in this series indeed represent the number of days
    # (as floats) between adjacent data points. The very first data point has
    # the value `NaN`, and the resulting series has the same index as the input
    # Dataframe (therefor also the same length).

    # Calculate the value change _per day_.
    change_per_day = df[column].diff().div(dt_days)

    # To stay with the example above and with '1001' being the data column,
    # this is the `change_per_day` series:
    #
    # time
    # 2020-03-02 17:00:00+00:00     NaN
    # 2020-03-03 17:00:00+00:00     0.0
    # 2020-03-04 17:00:00+00:00     0.0
    # 2020-03-05 17:00:00+00:00     0.0
    # 2020-03-06 17:00:00+00:00     0.0
    #                              ...
    # 2021-01-12 17:00:00+00:00    12.0
    # 2021-01-13 17:00:00+00:00    18.0
    # 2021-01-14 17:00:00+00:00    31.0
    # 2021-01-15 17:00:00+00:00    24.0
    # 2021-01-16 17:00:00+00:00     9.0
    #
    # For example, between 2021-01-15 17:00 and 2021-01-16 17:00 there
    # is a change from 736 to 745 (i.e. of +9) in the input Dataframe, and
    # correspondingly we see the data point `2021-01-16 17:00:00+00:00 -- 9.0`
    # in `change_per_day`. Good.

    # Insert the new series (reflecting change per day) as a new column
    # into the original dataframe (this mutates the dataframe).
    # df[f"{column}_change_per_day"] = change_per_day

    # print(df)
    # df[f"{column}_change_per_day"]
    # sys.exit()

    # Perform rolling window analysis.
    #
    # Before doing so, translate the data points in the time series to regular
    # intervals (assume dirty data, assume irregular distance between data
    # points): Resample into regular intervals (increase resolution to 1 hour,
    # but that doesn't matter too much) and forward-fill values. With this
    # forward-fill technique, the discrete jumps in raw data are retained.
    # Update: remove resampling for now -- pro: no strong reason to have it (at
    # least not written down here!), con: see issue #369
    #
    # change_per_day_rs =
    # change_per_day.resample("1H").pad()

    # print(type(df_change))
    # sys.exit()

    # Should be >= 7 to be meaningful.
    window = change_per_day.rolling(window="%sD" % window_width_days)

    # Manually build rolling window SUM (cumulative count for cases during
    # those N days). This uses the fact that after the resample above
    # there's N data points per day.
    if sum_over_time_window:
        output_series = window.sum()
    else:
        output_series = window.sum() / (window_width_days)

    return output_series
