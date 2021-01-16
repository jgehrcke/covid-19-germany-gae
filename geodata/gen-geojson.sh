#!/usr/bin/env bash
set -o errexit
set -o errtrace
set -o nounset

# https://gdz.bkg.bund.de/index.php/default/verwaltungsgebiete-1-250-000-ebenen-stand-01-01-vg250-ebenen-01-01.html
if [ ! -f vg250data.zip ]; then
    echo "downloading vg250_01-01.gk3.shape.ebenen.zip"
    curl --progress-bar \
        https://daten.gdz.bkg.bund.de/produkte/vg/vg250_ebenen_0101/aktuell/vg250_01-01.gk3.shape.ebenen.zip \
        -o vg250data.zip
fi

unzip -o vg250data.zip

ogr2ogr -f GeoJSON -simplify 200 \
    DE-counties.geojson vg250_*/vg250_ebenen_*/VG250_KRS.shp
