import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import dates

plt.style.use("ggplot")

csv_filepath = sys.argv[1]
day_of_interest = sys.argv[2]

df = pd.read_csv(
    csv_filepath,
    index_col=["commit_time_iso8601"],
    parse_dates=["commit_time_iso8601"],
    date_parser=lambda col: pd.to_datetime(col, utc=True),
)
df.index.name = "time"

# There may be duplicate rows / samples (for commits to the repo that did not
# change the file in question). Remove duplicates, and also make it so that
# that there is one data point per day (this drops many rows, and forward-fills
# for some days).
df = df.drop_duplicates().resample("1D").pad()

title = f"Deaths (all Germany) on {day_of_interest}, evolution in RKI database"

df["deaths_sum"].plot(
    title=title, marker="x", grid=True, figsize=[12, 9], color="black"
)

plt.xlabel("date of RKI database query")
plt.ylabel("sum_deaths_germany_2020-03-30")
plt.tight_layout()
# plt.show()
plt.savefig(f"sum_deaths_germany_{day_of_interest}_evolution_rki_db.png", dpi=90)


# Get time differences (unit: seconds) in the df's datetimeindex. `dt`
# is a magic accessor that yields an array of time deltas.
dt_seconds = pd.Series(df.index).diff().dt.total_seconds()
# Construct new series with original datetimeindex as index and time
# differences (unit: days) as values.
dt_days = pd.Series(dt_seconds) / 86400.0
dt_days.index = df.index
change_per_day = df["deaths_sum"].diff().div(dt_days)
df["deaths_sum_change_per_day"] = change_per_day

plt.figure()
df["deaths_sum_change_per_day"].plot(
    title="", linewidth=0, marker="x", figsize=[12, 9], color="black", logy=True
)
plt.xlabel("date")
plt.ylabel("daily change of sum_deaths_germany_2020-03-30")
plt.tight_layout()
plt.savefig(
    f"sum_deaths_germany_{day_of_interest}_evolution_rki_db_changeperday.png", dpi=90
)
