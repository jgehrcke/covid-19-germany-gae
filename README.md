This is the code behind https://covid19-germany.appspot.com

Further resources:

- Blog post [Covid-19 HTTP API: German case numbers](https://gehrcke.de/2020/03/covid-19-http-api-for-german-case-numbers/)
- Blog post [Covid-19 HTTP API: case numbers as time series, for individual German states](https://gehrcke.de/2020/03/covid-19-http-api-german-states-timeseries)
- Discussion on [a GitHub issue](https://github.com/iceweasel1/COVID-19-Germany/issues/10)

Feedback welcome.

## How to use the HTTP/JSON API

### Get the time series information for a specific German state:

First, construct the URL based on this pattern:

`https://covid19-germany.appspot.com/timeseries/<state>/<metric>`:

For `<state>` use the [ISO_3166](https://en.wikipedia.org/wiki/ISO_3166-2:DE) code, for `<metric>` use `cases` or `deaths`.

For example, to fetch the time evolution of the number of confirmed Covid-19 cases for Bayern (Bavaria):

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
