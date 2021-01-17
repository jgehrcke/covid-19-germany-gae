# COVID-19 case numbers for Germany 😷

## 🇩🇪 Übersicht

(see below for an English version)

* COVID-19 Fallzahlen für **Bundesländer** und **Landkreise**.
* Mehrfach täglich automatisiert aktualisiert.
* Mit **Zeitreihen**.
* Auch mit 7-Tage-Inzidenz-Zeitreihen.
* Aktuelle Einwohnerzahlen und GeoJSON-Daten, mit transparenten Quellen.
* Präzise maschinenlesbare **CSV**-Dateien. Zeitstempel in [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601)-Notation, Spaltennamen nutzen u.a. [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166-2:DE) country codes.
* Zwei verschiedene Perspektiven:
  * Die offiziellen Zeitreihen des [**RKI**](https://www.rki.de), auf Basis einer [ArcGIS HTTP Schnittstelle](https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/Covid19_RKI_Sums/FeatureServer/query) ([docs](https://developers.arcgis.com/rest/)) des [Esri COVID-19 GeoHub Deutschland](https://covid-19-geohub-deutschland-esridech.hub.arcgis.com/datasets/9644cad183f042e79fb6ad00eadc4ecf_0). Diese Zeitreihen werden täglich _in die Vergangenheit hinein_ aktualisiert und bieten einen *kuratierten* Blick auf die vergangenen Monate und Wochen.
  * Die Zeitreihen der [Risklayer GmbH](http://www.risklayer.com/)-koordinierten Crowdsourcing-Initiative (die Datenbasis für tagesaktuelle Zahlen einiger deutscher Medien, z. B. [des ZDF](https://www.zdf.de/nachrichten/heute/coronavirus-ausbreitung-infografiken-102.html) aber auch [der JHU](https://bnn.de/karlsruhe/johns-hopkins-university-nutzt-coronavirus-daten-von-risklayer-aus-karlsruhe)).

## 🇺🇸 Overview

* Historical (**time series**) data for individual Bundesländer and Landkreise (**states and counties**).
* Automatic updates, multiple times per day.
* 7-day incidence time series (so that you don't need to compute those).
* Population data and GeoJSON data, with transparent references and code for reproduction.
* Provided through machine-readable (**CSV**) files: timestamps are encoded using ISO 8601 time string notation. Column names use the ISO 3166 notation for individual states.
* Two perspectives on the historical evolution:
  * Official [**RKI**](https://www.rki.de) time series data, based on an [ArcGIS HTTP API](https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/Covid19_RKI_Sums/FeatureServer/query) ([docs](https://developers.arcgis.com/rest/)) provided by the [Esri COVID-19 GeoHub Deutschland](https://covid-19-geohub-deutschland-esridech.hub.arcgis.com/datasets/9644cad183f042e79fb6ad00eadc4ecf_0). These time series are being re-written as data gets better over time (accounting for delay in reporting etc), and provide a credible, curated view into the past weeks and months.
  * Time series data provided by the [Risklayer GmbH](http://www.risklayer.com/)-coordinated crowdsourcing effort (the foundation for what various German newspapers and TV channels show on a daily basis, such as [the ZDF](https://www.zdf.de/nachrichten/heute/coronavirus-ausbreitung-infografiken-102.html) but also the foundation for what [the JHU](https://bnn.de/karlsruhe/johns-hopkins-university-nutzt-coronavirus-daten-von-risklayer-aus-karlsruhe)) publishes about Germany.

In addition to the **CSV** files, this project offers an **HTTP (JSON) API**.

## Contact, questions, contributions

You probably have a number of questions.
Just as I had (and still have).
Your feedback, your contributions, and your questions are highly appreciated!
Please use the [GitHub issue tracker](https://github.com/jgehrcke/covid-19-germany-gae/issues) (preferred) or contact me via [mail](mailto:jgehrcke@googlemail.com).
For updates, you can also follow me on Twitter: [@gehrcke](https://twitter.com/gehrcke).

## Plots

Note that these plots are updated multiple times per day.
Feel free to hotlink them.

* [germany-heatmap-7ti-rki.png](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/germany-heatmap-7ti-rki.png) (also available as [PDF](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/germany-heatmap-7ti-rki.pdf)):

<img src="https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/germany-heatmap-7ti-rki.png" width="450"/>

* [daily-change-plot-latest.png](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/daily-change-plot-latest.png) (also available as [PDF](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/daily-change-plot-latest.pdf)):

<img src="https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/daily-change-plot-latest.png" width="1000"/>

**Note (December 2020):** you may be seeing the RKI data-based death rate curve with a clear downward trend in the recent past, whereas the Risklayer-based curve does not show that very trend.
Both curves are wrong, and yet both curves are legit.
It is essential to understand how.
The incidents of death that we learn about today probably have happened days or weeks in the past.
It's likely that the RKI tries to account for that.
The downwards trend in the RKI curve is an _artifact_ of that:
the majority of deaths the RKI learns about _today_ are inserted into the time series at a point in time in the past, _back-dated_ by days or weeks (likely to account for the actual time of death, but that's not confirmed).
That implies that the RKI data set cannot show a credible view of today's actual rate of deaths.
It will be available only days or weeks in the future.
The Risklayer data set pretends as if the incidents of death we learn about _today_ happened _yesterday_.
While this is not true, the resulting curve is free of said artifact. Despite its limitations, the Risklayer data set is the best view on the "current" evolution of deaths that we have.

## The individual data files

- **RKI data (most credible view into the past)**: time series data provided by the Robert Koch-Institut (**updated daily**):
  - [cases-rki-by-ags.csv](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/cases-rki-by-ags.csv) and [deaths-rki-by-ags.csv](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/deaths-rki-by-ags.csv): **per-Landkreis** time series
  - [cases-rki-by-state.csv](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/cases-rki-by-state.csv) and [deaths-rki-by-state.csv](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/deaths-rki-by-state.csv): **per-Bundesland** time series
  - 7-day incidence time series resolved by county based on RKI data can be found in `more-data/`.
  - This is the only data source that rigorously accounts for Meldeverzug (reporting delay). The historical evolution of data points in these files is updated daily based on a (less accessible) RKI ArcGIS system. These time series see amendments weeks and months into the past as data gets better over time. This data source has its strength in _the past_, but it often does not yet reflect the latest from today and yesterday.
- **Crowdsourcing data (fresh view into the last 1-2 days)**: Risklayer GmbH crowdsource effort (see "Attribution" below):
  - [cases-rl-crowdsource-by-ags.csv](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/cases-rl-crowdsource-by-ags.csv) and [deaths-rl-crowdsource-by-ags.csv](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/deaths-rl-crowdsource-by-ags.csv): **per-Landkreis** time series
  - [cases-rl-crowdsource-by-state.csv](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/cases-rl-crowdsource-by-state.csv) and [deaths-rl-crowdsource-by-state.csv](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/deaths-rl-crowdsource-by-state.csv): **per-Bundesland** time series
  - For the last ~48 hours these case count numbers (crowdsourced from Gesundheitsämter) may be a little more credible than what the RKI data set shows. For assessing the differences between the RKI data set(s) and the Risklayer data set(s) please also have a look at the [plot above](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/daily-change-plot-latest.png), and always try to do your own research.
  - 7-day incidence time series resolved by county based on Risklayer data can be found in `more-data/`.
- [ags.json](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/ags.json):
  - for translating "amtlicher Gemeindeschlüssel" (AGS) to Landreis/Bundesland details, including latitude and longitude.
  - containing per-county population data (see [pull/383](https://github.com/jgehrcke/covid-19-germany-gae/pull/383) for details).
- JSON endpoint [/now](https://covid19-germany.appspot.com/now): Germany's total case count (updated in **real time**, always fresh, for the sensationalists)
- [data.csv](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/ags.json): history, mixed data source based on RKI/ZEIT ONLINE. This powers the per-Bundesland time series exposed by the HTTP JSON API.
- JSON endpoints for per-Bundesland time series, example for Bayern: [/timeseries/DE-BY/cases](https://covid19-germany.appspot.com/timeseries/DE-BY/cases), based on `data.csv`, endpoints for other states linked from this landing page: https://covid19-germany.appspot.com

## How is this data set different from others?

- It includes **historical data for individual Bundesländer and Landkreise** (states and counties).
- Its time series data is being re-written as data gets better over time. This is based on official [RKI](https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/nCoV.html)-provided time series data which receives daily updates even for days weeks in the past (accounting for delay in reporting).
- The HTTP endpoint [/now](https://covid19-germany.appspot.com/now) consults multiple sources (and has changed its sources over time) to be as fresh and credible as possible while maintaining a stable interface.

## CSV file details

Focus: predictable/robust machine readability. Backwards-compatibility (columns get added; but have never been removed so far).

- The column names use the [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166-2:DE) code for individual states.
- The points in time are encoded using localized ISO 8601 time string notation.

Note that the numbers for "today" as presented in media often actually refer to the last known state of data on the evening before. To address this ambiguity, the sample timestamps in the CSV files presented in this repository contain the time of the day (and not just the _day_).
With that, consumers can have a vague impression about whether the sample represents the state in the morning or evening -- a common confusion / ambiguity with other data sets.

The `recovered` metric is not presented because it is rather blurry.
Feel free to consume it from other sources!


## Code example: parsing and plotting

This example assumes experience with established tools from the Python ecosystem.
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
- Saarland: [case numbers](https://corona.saarland.de/DE/service/aktuelle-lage/aktuelle-lage_node.html)
- Sachsen: [case numbers, LK table, intensive care numbers](https://www.coronavirus.sachsen.de/infektionsfaelle-in-sachsen-4151.html)
- Sachsen-Anhalt: [case numbers, LK table, intensive care numbers](https://ms.sachsen-anhalt.de/themen/gesundheit/aktuell/coronavirus/)
- Schleswig-Holstein: [case numbers, LK table](https://www.schleswig-holstein.de/DE/Landesregierung/I/Presse/_documents/Corona-Liste_Kreise.html)
- Thüringen: [case numbers, LK table, intensive car numbers](https://www.tmasgff.de/covid-19/fallzahlen)


## Further resources:

- In [this blog post](https://gehrcke.de/2020/03/deutschlands-covid-19-fallzahlen-des-rki-und-der-who-haben-inzwischen-2-3-tage-verzogerung/) (German) I try to shed light on why — as of the time of writing (March 18) — the numbers reported in the RKI and WHO situation reports lag behind by 1-3 days.
- Blog post [Covid-19 HTTP API: German case numbers](https://gehrcke.de/2020/03/covid-19-http-api-for-german-case-numbers/)
- Blog post [Covid-19 HTTP API: case numbers as time series, for individual German states](https://gehrcke.de/2020/03/covid-19-http-api-german-states-timeseries)



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

## What you should know before reading these numbers

Please question the conclusiveness of these numbers.
Some directions along which you may want to think:

- Germany seems to perform a large number of tests. But think about how much insight you actually have into how the testing rate (and its spatial distribution) evolves over time. In my opinion, one absolutely should know a whole _lot_ about the testing effort itself before drawing conclusions from the time evolution of case count numbers.
- Each confirmed case is implicitly associated with a reporting date. We do not know for sure how that reporting date relates to the date of taking the sample.
- We believe that each "confirmed case" actually corresponds to a polymerase chain reaction (PCR) test for the SARS-CoV2 virus with a positive outcome. Well, I think that's true, we can have that much trust into the system.
- We seem to believe that the change of the number of confirmed COVID-19 cases over time is somewhat expressive: but what does it shed light on, exactly? The amount of testing performed, and its spatial coverage? The efficiency with which the virus spreads through the population ("basic reproduction number")? The actual, absolute number of people infected? The virus' potential to exhibit COVID-19 in an infected human body?

If you keep these (and more) ambiguities and questions in mind then I think you are ready to look at these numbers and their time evolution :-) 😷.

## Changelog: data source

In Germany, every step along the chain of reporting (Meldekette) introduces a noticeable delay.
This is not necessary, but sadly the current state of affairs.
The Robert Koch-Institut (RKI) [seems to be working on](https://github.com/jgehrcke/covid-19-germany-gae/issues/47) a more modern reporting system that might mitigate some of these delays along the Meldekette in the future.
Until then, it is fair to assume that case numbers published by RKI have 1-2 days delay over the case numbers published by Landkreise, which themselves have an unknown lag relative to the physical tests.
In some cases, the Meldekette might even be entirely disrupted, as discussed in this [SPIEGEL article](https://www.spiegel.de/wissenschaft/coronavirus-wie-belastbar-sind-die-rki-daten-a-13bd06d7-22a1-4b3d-af23-ff43e5e8abd6) (German).
Also see [this discussion](https://github.com/CSSEGISandData/COVID-19/issues/1008).

**Wishlist:** every case should be tracked with its own time line, and transparently change state over time.
The individual cases (and their time lines) should be aggregated on a country-wide level, anonymously, and get published in almost real time, through an official, structured data source, free to consume for everyone.

As discussed, the actual data flow situation is far from this ideal.
Nevertheless, the primary concern of this dataset here is to maximize data _credibility_ while also trying to maximize data _freshness_; a challenging trade-off in this initial phase of pandemic growth in Germany.
That is, the goal is to provide you with the least shitty numbers from a set of generally pretty shitty numbers.
To that end, I took liberty to iterate on the data source behind _this_ dataset — as indicated below.

### `/now` (current state):

- **Since (incl) March 26**: Meldekette step 2: reports by the individual counties (Landkreise), curated by [Tagesspiegel](https://twitter.com/Tagesspiegel) and [Risklayer](https://twitter.com/risklayer) for the current case count, curated by ZEIT ONLINE for `deaths`.
- **Since (incl) March 24**: Meldekette step 2: reports by the individual counties (Landkreise), curated by ZEIT ONLINE.
- **Since (incl) March 19**: Meldekette step 3: reports by the individual states (Bundesländer), curated by ZEIT ONLINE, and Berliner Morgenpost.


### `/timeseries/...` (historical data):

Update (evening March 29): in the near future I consider re-writing the history exposed by these endpoints (`data.csv`) using RKI data, accounting for long reporting delays.

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

## Attributions

Shout-out to ZEIT ONLINE for continuously collecting and publishing the state-level data with little delay.

Edit March 21, 2020: Notably, by now the [Berliner Morgenpost](https://interaktiv.morgenpost.de/corona-virus-karte-infektionen-deutschland-weltweit/)
seems to do an equally well job of _quickly_ aggregating the state-level data.
We are using that in here, too. Thanks!

Edit March 26, 2020: [Risklayer](https://twitter.com/risklayer) is coordinating a crowd-sourcing effort to process verified Landkreis data as quickly as possible. [Tagesspiegel](https://twitter.com/Tagesspiegel) is verifying this effort and using it in [their overview page](https://interaktiv.tagesspiegel.de/lab/karte-sars-cov-2-in-deutschland-landkreise/).
As far as I can tell this is so far the most transparent data flow, and also the fastest, getting us the freshest case count numbers. Great work!

Edit December 13, 2020: for the `*-rl-crowdsource*.csv` files proper legal attribution goes to

> Risklayer GmbH (www.risklayer.com) and Center for Disaster Management and Risk Reduction Technology (CEDIM) at Karlsruhe Institute of Technology (KIT) and the Risklayer-CEDIM-Tagesspiegel SARS-CoV-2 Crowdsourcing Contributors
