# COVID-19 case count in Germany by state, over time

The data set is provided via an **HTTP (JSON) API** as well as through a comma-separated value (**CSV**) file.

How is this different from other data sources?

- It exposes historical data for individual states (Bundesländer), manually curated from RKI ["situation reports"](https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Situationsberichte/Archiv.html). I did not find any other up-to-date structured data source for that.
- https://covid19-germany.appspot.com/now consults multiple sources to be as
  fresh as possible (as of the time of writing: ZEIT ONLINE, Berliner
  Morgenpost). See [attribution](https://github.com/jgehrcke/covid-19-germany-gae#attribution).

For the HTTP API the primary motivation is:

- convenience (easy to consume for you in the tooling of your choice!)
- interface stability
- data _credibility_ and data _freshness_
- availability

## Quick overview

- [CSV file](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/data.csv)
- HTTP API endpoint for the current state: https://covid19-germany.appspot.com/now
- HTTP API endpoint for historical data: https://covid19-germany.appspot.com/timeseries/DE-BY/cases

More details below.

## Contact and questions

You probably have many questions, just as I did (and still do). Your feedback and questions are highly appreciated!
Please use the [GitHub issue tracker](https://github.com/jgehrcke/covid-19-germany-gae/issues) (preferred)
or contact me via mail at jgehrcke@googlemail.com.

## Sources and information flow

These are official numbers published by individual state health ministries in
Germany.

The numbers from the individual (hundreds of) public German health offices
(Gesundheitsämter) are first collected and aggregated on the state level, by
the individual state health ministries. From here, they are further collected
and published through ["situation reports"](https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Situationsberichte/Archiv.html)
by the Robert Koch-Institut (yielding the data points in this database before
March 17), but also by ZEIT ONLINE (yielding the data points in my database
from March 17 on).

In [this blog](https://gehrcke.de/2020/03/deutschlands-covid-19-fallzahlen-des-rki-und-der-who-haben-inzwischen-2-3-tage-verzogerung/)
post I explain why as of the time of writing (March 18) the numbers reported in
the RKI and WHO situation reports lag behind by 1-3 days.

## Further resources:

- Blog post [Covid-19 HTTP API: German case numbers](https://gehrcke.de/2020/03/covid-19-http-api-for-german-case-numbers/)
- Blog post [Covid-19 HTTP API: case numbers as time series, for individual German states](https://gehrcke.de/2020/03/covid-19-http-api-german-states-timeseries)
- [Blog post about delay of RKI numbers](https://gehrcke.de/2020/03/deutschlands-covid-19-fallzahlen-des-rki-und-der-who-haben-inzwischen-2-3-tage-verzogerung/) (German)
- Discussion on [a GitHub issue](https://github.com/iceweasel1/COVID-19-Germany/issues/10)

## CSV file details

- The column names use the [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166-2:DE) code for individual state.
- The points in time are encoded using localized ISO8601 time string notation.

### Example: parsing and plotting

```python
import pandas as pd
import matplotlib.pyplot as plt


df = pd.read_csv("data.csv", index_col=["time_iso8601"], parse_dates=["time_iso8601"])
df.index.name = "time"

df["DE-BW_cases"].plot(
    title="DE-BW confirmed cases", marker="x", grid=True, figsize=[12, 9]
)
plt.savefig("bw_cases_over_time.png", dpi=200)
```

## HTTP API details

- The HTTP API is served under https://covid19-germany.appspot.com
- It is served by Google App Engine from a European data center
- The code behind this can be found in the `gae` directory in this repository.

### How to use the HTTP/JSON API

#### Get historical data for a specific German state/Bundesland:

First, construct the URL based on this pattern:

`https://covid19-germany.appspot.com/timeseries/<state>/<metric>`:

For `<state>` use the [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166-2:DE) code, for `<metric>` use `cases` or `deaths`.

For example, to fetch the time evolution of the number of confirmed COVID-19 cases for Bayern (Bavaria):

```
$ curl -s https://covid19-germany.appspot.com/timeseries/DE-BY/cases | jq
{
  "data": {
    "2020-03-10T12:00:00+01:00": "314",
    "2020-03-11T12:00:00+01:00": "366",
    "2020-03-12T12:00:00+01:00": "500",
    "2020-03-13T12:00:00+01:00": "558",
    "2020-03-14T12:00:00+01:00": "681",
    "2020-03-15T12:00:00+01:00": "886",
    "2020-03-16T12:00:00+01:00": "1067",
    "2020-03-17T21:00:00+01:00": "1352",
    "2020-03-18T23:00:00+01:00": "1798"
  },
  "meta": {
    "info": "https://gehrcke.de/2020/03/covid-19-http-api-german-states-timeseries",
    "source": "Official numbers published by public health offices (Gesundheitsaemter) in Germany"
  }
}
```

The points in time are encoded using localized ISO8601 time string notation.
Any decent datetime library can parse that into timezone-aware native timestamp
representations.

### Get the current snapshot for all of Germany (no time series)

```
$ curl -s https://covid19-germany.appspot.com/now | jq
{
  "current_totals": {
    "cases": 12223,
    "deaths": 31,
    "recovered": 99,
    "tested": "unknown"
  },
  "meta": {
    "contact": "Dr. Jan-Philip Gehrcke, jgehrcke@googlemail.com",
    "source": "ZEIT ONLINE (aggregated data from individual ministries of health in Germany)",
    "time_source_last_consulted_iso8601": "2020-03-19T03:47:01+00:00",
    "time_source_last_updated_iso8601": "2020-03-18T22:11:00+01:00"
  }
}
```

Notably, the [Berliner Morgenpost](https://interaktiv.morgenpost.de/corona-virus-karte-infektionen-deutschland-weltweit/)
seems to also do a great job at _quickly_ aggregating the state-level data.
This API endpoint chooses either that source or ZEIT ONLINE depending on
the higher case count.

## Attribution

Shout-out to as well as from ZEIT ONLINE for continuously collecting and
publishing the state-level data with little delay.

Notably, the [Berliner Morgenpost](https://interaktiv.morgenpost.de/corona-virus-karte-infektionen-deutschland-weltweit/)
seems to do a similarly well job of _quickly_ aggregating the state-level data.

Quick aggregation is important during the phase of exponential growth.
