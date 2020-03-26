# COVID-19 case numbers in Germany by state, over time 😷

**Landing page**: https://covid19-germany.appspot.com

This dataset is provided via an **HTTP (JSON) API** as well as through a comma-separated value (**CSV**) file.

How is this different from other datasets?

- The dataset includes **historical data for individual Bundesländer** (states).
- [/now](https://covid19-germany.appspot.com/now) consults multiple sources (and has changed its sources over time) to be as fresh and credible as possible while maintaining a stable interface.

**These are raw COVID-19 case numbers. Please consume them responsibly. Question their conclusiveness. Some directions along which you may want to think:**

- We believe that each "confirmed case" actually corresponds to a polymerase chain reaction (PCR) test for the SARS-CoV2 virus with a positive outcome. I really hope that's true!
- Although Germany seems to perform a large number of tests, we (the public) do not know how the testing rate (and its spatial distribution) evolves over time. In my opinion, one absolutely should know a whole _lot_ about the testing effort itself before starting to draw conclusions from the time evolution of case count numbers.
- Yet, we seem to believe that the change of the number of confirmed COVID-19 cases over time is somewhat expressive: but what does it shed light on, exactly? The amount of testing performed, and its spatial coverage? The efficiency with which the virus spreads through the population ("basic reproduction number")? The actual, absolute number of people infected? The virus' potential to exhibit COVID-19 in an infected human body? If you keep these (and more) ambiguities in mind then I think you're ready to look at these numbers :-) 😷.

---

## Quick overview

- [CSV file](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/data.csv)
- JSON endpoint for the current state: [/now](https://covid19-germany.appspot.com/now)
- JSON endpoint for time series, example for Bayern: [/timeseries/DE-BY/cases](https://covid19-germany.appspot.com/timeseries/DE-BY/cases)
- Endpoints for other states linked from this landing page: https://covid19-germany.appspot.com

## Contact, questions, contributions

You probably have many questions, just as I did (and still do). Your feedback and questions are highly appreciated!
Please use the [GitHub issue tracker](https://github.com/jgehrcke/covid-19-germany-gae/issues) (preferred)
or contact me via mail at jgehrcke@googlemail.com.

## Changelog: data source

In Germany, every step along the chain of reporting (Meldekette) introduces a noticeable delay.
This is not necessary, but sadly the current state of affairs.
The Robert Koch-Institut (RKI) [seems to be working on](https://github.com/jgehrcke/covid-19-germany-gae/issues/47) a more modern reporting system that might mitigate some of these delays along the Meldekette in the future.
Until then, it is fair to assume that case numbers published by RKI have 1-2 days delay over the case numbers published by Landkreise, which themselves have an unknown lag relative to they physical tests. Also see [this discussion](https://github.com/CSSEGISandData/COVID-19/issues/1008).

**Wishlist:** every case should be tracked with its own time line, and transparently change state over time.
The individual cases (and their time lines) should be aggregated on a country-wide level, anonymously, and get published in almost real time, through an official, structured data source, free to consume for everyone.

As discussed, the actual data flow situation is far from this ideal.
Nevertheless, the primary concern of this dataset here is to maximize data _credibility_ while also trying to maximize data _freshness_; a challenging trade-off in this initial phase of pandemic growth in Germany.
That is, the goal is to provide you with the least shitty numbers from a set of generally pretty shitty numbers.
To that end, I took liberty to iterate on the data source behind _this_ dataset — as indicated below.

### `/now` (current state):

- **Since (incl) March 26**: Meldekette step 2: reports by the individual counties (Landkreise), curated by [Tagesspiegel](https://twitter.com/Tagesspiegel) and [Risklayer](https://twitter.com/risklayer).
- **Since (incl) March 24**: Meldekette step 2: reports by the individual counties (Landkreise), curated by ZEIT ONLINE.
- **Since (incl) March 19**: Meldekette step 3: reports by the individual states (Bundesländer), curated by ZEIT ONLINE, and Berliner Morgenpost.

### `/timeseries/...` (historical data):

Update (evening March 24): in the near future I consider incorporating data obtained through a crowd-sourcing effort coordinated by [Risklayer](https://twitter.com/risklayer); that might get us even fresher data from individual counties.

- **Since (incl) March 24**: Meldekette step 2: reports by the individual counties (Landkreise), curated by ZEIT ONLINE.
- **Since (incl) March 18**: Meldekette step 3: reports by the individual states (Bundesländer), curated by ZEIT ONLINE.
- **Before March 18**: Meldekette step 4: RKI ["situation reports"](https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/Situationsberichte/Archiv.html) (PDF documents).

**Note:**

- The `source` identifier in the CSV file changes correspondingly over time.
- A mix of sources in a time series is of course far from ideal.
  However — given the boundary conditions — I think switching to better sources as they come up is fair and useful.
  We might also change (read: _rewrite_) time series data in hindsight.
  Towards enhancing overall credibility.
  That has not happened yet, but that can change as we learn more about the Germany-internal data flow, and about the credibility of individual data sources.

## Quality data sources published by Bundesländer

I tried to discover these step-by-step, they are possibly underrated:

- Bayern: [case numbers, map, LK table](https://www.lgl.bayern.de/gesundheit/infektionsschutz/infektionskrankheiten_a_z/coronavirus/karte_coronavirus/index.htm)
- Berlin: [case numbers, map, intensive care numbers](https://www.berlin.de/corona/fallstatistik/)
- Baden-Württemberg:
  - [case numbers, map, discussion](https://sozialministerium.baden-wuerttemberg.de/de/gesundheit-pflege/gesundheitsschutz/infektionsschutz-hygiene/informationen-zu-coronavirus/)
  - [spreadsheet, xlsx, with historical data](https://sozialministerium.baden-wuerttemberg.de/fileadmin/redaktion/m-sm/intern/downloads/Downloads_Gesundheitsschutz/Tabelle_Coronavirus-Faelle-BW.xlsx)
- Brandenburg: [press releases](https://msgiv.brandenburg.de/msgiv/de/presse/pressemitteilungen/)
- Bremen: [press releases](https://www.gesundheit.bremen.de/sixcms/detail.php?gsid=bremen229.c.32718.de)
- Hamburg: [case numbers](https://www.hamburg.de/coronavirus/), [press releases](https://www.hamburg.de/coronavirus/pressemeldungen/)
- Hessen: [press releases](https://soziales.hessen.de/)
- NRW: [case numbers, LK table](https://www.mags.nrw/coronavirus-fallzahlen-nrw)
- Mecklenburg-Vorpommern: [press releases](https://www.regierung-mv.de/Aktuell/)
- Niedersachsen (pretty well done!):
  - [case numbers, map, LK table](https://www.niedersachsen.de/Coronavirus/aktuelle_lage_in_niedersachsen/)
  - [CSV](https://www.apps.nlga.niedersachsen.de/corona/download.php?csv) / [GeoJSON](https://www.apps.nlga.niedersachsen.de/corona/download.php?json)
  - so close, but no historical data :-(
- Rheinland-Pfalz: [case numbers, LK table](https://msagd.rlp.de/de/unsere-themen/gesundheit-und-pflege/gesundheitliche-versorgung/oeffentlicher-gesundheitsdienst-hygiene-und-infektionsschutz/infektionsschutz/informationen-zum-coronavirus-sars-cov-2/)
- Saarland: [press releases](https://www.saarland.de/254259.htm) only :-( come on, Saarland!
- Sachsen: [case numbers, LK table, intensive care numbers](https://www.coronavirus.sachsen.de/infektionsfaelle-in-sachsen-4151.html)
- Sachsen-Anhalt: [case numbers, LK table, intensive care numbers](https://ms.sachsen-anhalt.de/themen/gesundheit/aktuell/coronavirus/)
- Schleswig-Holstein: [case numbers, LK table](https://www.schleswig-holstein.de/DE/Landesregierung/I/Presse/_documents/Corona-Liste_Kreise.html)
- Thüringen: [case numbers, LK table, intensive car numbers](https://www.landesregierung-thueringen.de/corona-bulletin)

## Plots

Confirmed COVID-19 cases over time with exponential fit, for

- [All Germany](https://covid19-germany.appspot.com/static/plots/plot-DEU.html)
- [Baden-Württemberg](https://covid19-germany.appspot.com/static/plots/plot-DE-BW.html)
- [Bayern](https://covid19-germany.appspot.com/static/plots/plot-DE-BY.html)
- [Brandenburg](https://covid19-germany.appspot.com/static/plots/plot-DE-BB.html)
- [Berlin](https://covid19-germany.appspot.com/static/plots/plot-DE-BE.html)
- [Bremen](https://covid19-germany.appspot.com/static/plots/plot-DE-HB.html)
- [Hamburg](https://covid19-germany.appspot.com/static/plots/plot-DE-HH.html)
- [Hessen](https://covid19-germany.appspot.com/static/plots/plot-DE-HE.html)
- [Mecklenburg-Vorpommern](https://covid19-germany.appspot.com/static/plots/plot-DE-MV.html)
- [Niedersachsen](https://covid19-germany.appspot.com/static/plots/plot-DE-NI.html)
- [Nordrhein-Westfalen](https://covid19-germany.appspot.com/static/plots/plot-DE-NW.html)
- [Rheinland-Pfalz](https://covid19-germany.appspot.com/static/plots/plot-DE-RP.html)
- [Saarland](https://covid19-germany.appspot.com/static/plots/plot-DE-SL.html)
- [Sachsen-Anhalt](https://covid19-germany.appspot.com/static/plots/plot-DE-ST.html)
- [Sachsen](https://covid19-germany.appspot.com/static/plots/plot-DE-SN.html)
- [Schleswig-Holstein](https://covid19-germany.appspot.com/static/plots/plot-DE-SH.html)
- [Thüringen](https://covid19-germany.appspot.com/static/plots/plot-DE-TH.html)

Automatically generated based on this data set, but possibly not every day.

## Further resources:

- In [this blog post](https://gehrcke.de/2020/03/deutschlands-covid-19-fallzahlen-des-rki-und-der-who-haben-inzwischen-2-3-tage-verzogerung/) (German) I try to shed light on why — as of the time of writing (March 18) — the numbers reported in the RKI and WHO situation reports lag behind by 1-3 days.
- Blog post [Covid-19 HTTP API: German case numbers](https://gehrcke.de/2020/03/covid-19-http-api-for-german-case-numbers/)
- Blog post [Covid-19 HTTP API: case numbers as time series, for individual German states](https://gehrcke.de/2020/03/covid-19-http-api-german-states-timeseries)

## CSV file details

- The column names use the [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166-2:DE) code for individual states.
- The points in time are encoded using localized ISO 8601 time string notation.
- I did not incorporate the numbers on `recovered` so far because individual Gesundheitsämter do not have the capacity to carefully track this metric yet (it is rather meaningless).
- Right now my idea is to update this file daily during the (German) evening hours, after ZEIT ONLINE and Berliner Morgenpost have published their last update of the day.
- As a differentiator from other datasets the sample timestamps contain the time of the day so that consumers can at least have a vague impression if the sample represents the state in the morning or evening (a common confusion about the RKI-derived datasets).
  If it's the morning then it's likely to actually be data of the day before. If it's the evening then it's more likely to represent the state of the day.

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

For the HTTP API some of the motivations are **convenience** ( easy to consume in the tooling of your choice!), **interface stability**, and **availability**.

- The HTTP API is served under https://covid19-germany.appspot.com
- It is served by Google App Engine from a European data center
- The code behind this can be found in the `gae` directory in this repository.

**How to get historical data for a specific German state/Bundesland:**

Construct the URL based on this pattern:

`https://covid19-germany.appspot.com/timeseries/<state>/<metric>`:

For `<state>` use the [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166-2:DE) code, for `<metric>` use `cases` or `deaths`.

For example, to fetch the time evolution of the number of confirmed COVID-19 cases for Bayern (Bavaria):

```
$ curl -s https://covid19-germany.appspot.com/timeseries/DE-BY/cases | jq
{
  "data": [
    {
      "2020-03-10T12:00:00+01:00": "314"
    },
[...]
```

The points in time are encoded using localized ISO 8601 time string notation.
Any decent datetime library can parse that into timezone-aware native timestamp
representations.

**How to get the current snapshot for all of Germany (no time series):**

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

Shout-out to ZEIT ONLINE for continuously collecting and publishing the state-level data with little delay.

Edit: Notably, by now the [Berliner Morgenpost](https://interaktiv.morgenpost.de/corona-virus-karte-infektionen-deutschland-weltweit/)
seems to do an equally well job of _quickly_ aggregating the state-level data.
We are using that in here, too. Thanks!

Edit March 26: [Risklayer](https://twitter.com/risklayer) is coordinating a crowd-sourcing effort to process verified Landkreis data as quickly as possible. [Tagesspiegel](https://twitter.com/Tagesspiegel) is verifying this effort and using it in [their overview page](https://interaktiv.tagesspiegel.de/lab/karte-sars-cov-2-in-deutschland-landkreise/).
As far as I can tell this is so far the most transparent data flow, and also the fastest, getting us the freshest case count numbers. Great work!

Fast aggregation & communication is important during the phase of exponential growth.

## Random notes

- The MDC Berlin has published [this visualization](https://covid19germany.mdc-berlin.de/)
  and [this article](https://www.mdc-berlin.de/news/press/state-state-breakdown-covid-19-germany), but
  they seemingly decided to not publish the time series data. I got my hopes
  up here at first!
