# COVID-19 case numbers for Germany 😷

## 🇩🇪 Übersicht

(see below for an English version)

* COVID-19 Fallzahlen für **Bundesländer** und **Landkreise**.
* Mehrfach täglich automatisiert aktualisiert.
* Mit **Zeitreihen** (inkl. 7-Tage-Inzidenz-Zeitreihen).
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

## Contact, questions, contributions

You probably have a number of questions.
Just as I had (and still have).
Your feedback, your contributions, and your questions are highly appreciated!
Please use the [GitHub issue tracker](https://github.com/jgehrcke/covid-19-germany-gae/issues) (preferred) or contact me via [mail](mailto:jgehrcke@googlemail.com).
For updates, you can also follow me on Twitter: [@gehrcke](https://twitter.com/gehrcke).

## Plots

Note that these plots are updated multiple times per day.
Feel free to hotlink them.

* [germany-heatmap-7ti-rl.png](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/germany-heatmap-7ti-rl.png) (also available as [PDF](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/germany-heatmap-7ti-rl.pdf)):

<img src="https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/germany-heatmap-7ti-rl.png" width="450"/>

* [daily-change-plot-latest.png](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/daily-change-plot-latest.png) (also available as [PDF](https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/daily-change-plot-latest.pdf)):

<img src="https://raw.githubusercontent.com/jgehrcke/covid-19-germany-gae/master/plots/daily-change-plot-latest.png" width="1000"/>

**Note:** there is a systematic difference between the RKI data-based death rate curve and the Risklayer-based death rate curve.
Both curves are wrong, and yet both curves are legit.
The incidents of death that we learn about today may have happened days or weeks in the past.
Neither curve attempts to show the exact time of death (sadly! :-))
The RKI curve, in fact, is based on the point in time when each corresponding COVID-19 case that led to death was registered in the first place ("Meldedatum" of the corresponding case).
The Risklayer data set to my knowledge pretends as if the incidents of death we learn about _today_ happened _yesterday_.
While this is not true, the resulting curve is a little more intuitive.
Despite its limitations, the Risklayer data set is the best view on the "current" evolution of deaths that we have.

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
- JSON endpoint [/now](https://covid19-germany.appspot.com/now): Germany's total case count (updated in **real time**, always fresh, for the sensationalists) -- Update Feb 2021: the HTTP API was disabled.
- [data.csv](https://github.com/jgehrcke/covid-19-germany-gae/blob/master/ags.json): history, mixed data source based on RKI/ZEIT ONLINE. This did power the per-Bundesland time series exposed by the HTTP JSON API up until Jan 2021.

## How is this data set different from others?

- It includes **historical data for individual Bundesländer and Landkreise** (states and counties).
- Its time series data is being re-written as data gets better over time. This is based on official [RKI](https://www.rki.de/DE/Content/InfAZ/N/Neuartiges_Coronavirus/nCoV.html)-provided time series data which receives daily updates even for days weeks in the past (accounting for delay in reporting).


## CSV file details

Focus: predictable/robust machine readability. Backwards-compatibility (columns get added; but have never been removed so far).

- The column names use the [ISO 3166](https://en.wikipedia.org/wiki/ISO_3166-2:DE) code for individual states.
- The points in time are encoded using localized ISO 8601 time string notation.

Note that the numbers for "today" as presented in media often actually refer to the last known state of data on the evening before. To address this ambiguity, the sample timestamps in the CSV files presented in this repository contain the time of the day (and not just the _day_).
With that, consumers can have a vague impression about whether the sample represents the state in the morning or evening -- a common confusion / ambiguity with other data sets.

The `recovered` metric is not presented because it is rather blurry.
Feel free to consume it from other sources!


## Quality data sources published by Bundesländer

I tried to discover these step-by-step, they are possibly underrated (April 2020, minor updates towards the end of 2020):

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
- Thüringen: [case numbers, LK table, intensive care numbers](https://www.tmasgff.de/covid-19/fallzahlen)


## Further resources

- In [this blog post](https://gehrcke.de/2020/03/deutschlands-covid-19-fallzahlen-des-rki-und-der-who-haben-inzwischen-2-3-tage-verzogerung/) (German) I try to shed light on why — as of the time of writing (March 18) — the numbers reported in the RKI and WHO situation reports lag behind by 1-3 days.
- Blog post [Covid-19 HTTP API: German case numbers](https://gehrcke.de/2020/03/covid-19-http-api-for-german-case-numbers/)
- Blog post [Covid-19 HTTP API: case numbers as time series, for individual German states](https://gehrcke.de/2020/03/covid-19-http-api-german-states-timeseries)


## HTTP API details

Update Feb 2021: I disabled the HTTP API. It's best to directly use the data files from this respository.


## What you should know before reading these numbers

Please question the conclusiveness of these numbers.
Some directions along which you may want to think:

- Germany seems to perform a large number of tests. But think about how much insight you actually have into how the testing rate (and its spatial distribution) evolves over time. In my opinion, one absolutely should know a whole _lot_ about the testing effort itself before drawing conclusions from the time evolution of case count numbers.
- Each confirmed case is implicitly associated with a reporting date. We do not know for sure how that reporting date relates to the date of taking the sample.
- We believe that each "confirmed case" actually corresponds to a polymerase chain reaction (PCR) test for the SARS-CoV2 virus with a positive outcome. Well, I think that's true, we can have that much trust into the system.
- We seem to believe that the change of the number of confirmed COVID-19 cases over time is somewhat expressive: but what does it shed light on, exactly? The amount of testing performed, and its spatial coverage? The efficiency with which the virus spreads through the population ("basic reproduction number")? The actual, absolute number of people infected? The virus' potential to exhibit COVID-19 in an infected human body?

If you keep these (and more) ambiguities and questions in mind then I think you are ready to look at these numbers and their time evolution :-) 😷.

## Thoughts about reporting delays

In Germany, every step along the chain of reporting (Meldekette) introduces a noticeable delay.
This is not necessary, but sadly the current state of affairs.
The Robert Koch-Institut (RKI) [seems to be working on](https://github.com/jgehrcke/covid-19-germany-gae/issues/47) a more modern reporting system that might mitigate some of these delays along the Meldekette in the future.
Until then, it is fair to assume that case numbers published by RKI have 1-2 days delay over the case numbers published by Landkreise, which themselves have an unknown lag relative to the physical tests.
In some cases, the Meldekette might even be entirely disrupted, as discussed in this [SPIEGEL article](https://www.spiegel.de/wissenschaft/coronavirus-wie-belastbar-sind-die-rki-daten-a-13bd06d7-22a1-4b3d-af23-ff43e5e8abd6) (German).
Also see [this discussion](https://github.com/CSSEGISandData/COVID-19/issues/1008).

**Wishlist:** every case should be tracked with its own time line, and transparently change state over time.
The individual cases (and their time lines) should be aggregated on a country-wide level, anonymously, and get published in almost real time, through an official, structured data source, free to consume for everyone.


## Attributions

Beginning of March 2020: shout-out to ZEIT ONLINE for continuously collecting and publishing the state-level data with little delay.

Edit March 21, 2020: Notably, by now the [Berliner Morgenpost](https://interaktiv.morgenpost.de/corona-virus-karte-infektionen-deutschland-weltweit/)
seems to do an equally well job of _quickly_ aggregating the state-level data.
We are using that in here, too. Thanks!

Edit March 26, 2020: [Risklayer](https://twitter.com/risklayer) is coordinating a crowd-sourcing effort to process verified Landkreis data as quickly as possible. [Tagesspiegel](https://twitter.com/Tagesspiegel) is verifying this effort and using it in [their overview page](https://interaktiv.tagesspiegel.de/lab/karte-sars-cov-2-in-deutschland-landkreise/).
As far as I can tell this is so far the most transparent data flow, and also the fastest, getting us the freshest case count numbers. Great work!

Edit December 13, 2020: for the `*-rl-crowdsource*.csv` files proper legal attribution goes to

> Risklayer GmbH (www.risklayer.com) and Center for Disaster Management and Risk Reduction Technology (CEDIM) at Karlsruhe Institute of Technology (KIT) and the Risklayer-CEDIM-Tagesspiegel SARS-CoV-2 Crowdsourcing Contributors
