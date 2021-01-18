## Code example: parsing and plotting

This example assumes a little bit of experience with established tools from the
Python ecosystem.

Create a file called `plot.py`:

```python
import sys
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use("ggplot")

df = pd.read_csv(
    sys.argv[1],
    index_col=["time_iso8601"],
    parse_dates=["time_iso8601"],
    date_parser=lambda col: pd.to_datetime(col, utc=True),
)
df.index.name = "time"

df["DE-BW"].plot(
    title="DE-BW confirmed cases (RKI data)", marker="x", grid=True, figsize=[12, 9]
)
plt.tight_layout()
plt.savefig("bw_cases_over_time.png", dpi=70)
```

Run it, provide `cases-rki-by-state.csv` as an argument:

```bash
python plot.py cases-rki-by-state.csv
```

This creates a file `bw_cases_over_time.png` which may look like the following:

<img src="https://i.imgur.com/ksbYcdQ.png" width="600" />