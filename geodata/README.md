# DE-counties.geojson

For the sake of information flow transparency, the file `DE-counties.geojson` can be reproduced by using the script `gen-geojson.sh` in this directory.

Original data source: [Bundesamt für Kartographie und Geodäsie, Open Data](https://gdz.bkg.bund.de/index.php/default/open-data.html).

Data set detail:
* The data set [Verwaltungsgebiete 1:250 000 (Ebenen), Stand 01.01. (VG250 01.01.)](https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-250-000-ebenen-stand-01-01-vg250-ebenen-01-01.html) was selected.
* Specifically, the file [g250_01-01.gk3.shape.ebenen.zip](https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_0101/aktuell/vg250_01-01.gk3.shape.ebenen.zip) was used.
* The file is annotated with `Stand: 01.01., Georeferenzierung: GK3, Format: shape Inhalt: Ebenen (ZIP, 72 MB)`.
* State of data: January 1, 2020

I used `ogr2ogr` from the [GDAL](https://gdal.org/) distribution version `3.0.4` for the GK3-GeoJSON conversion.

During the conversion, `ogr2ogr`'s `-simplify` option was used with a tolerance value of 200. See [this](https://gdal.org/programs/ogr2ogr.html#cmdoption-ogr2ogr-simplify) and [that](https://gis.stackexchange.com/questions/144015/how-does-ogr2ogr-simplify-work) to learn more about what that means.

## Coordinate system

The coordinates listed in `DE-counties.geojson` are given in the spatial reference system [EPSG:4326 (WGS84)](https://spatialreference.org/ref/epsg/wgs-84/).

The CRS URN specified in `DE-counties.geojson` is `urn:ogc:def:crs:OGC:1.3:CRS84`.

## Further references (for the curious ones)

* https://gis.stackexchange.com/a/203442
* https://macwright.com/2015/03/23/geojson-second-bite.html
* https://geojson.org/geojson-spec.html#coordinate-reference-system-objects
