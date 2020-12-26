#!/usr/bin/env bash
set -o errexit
set -o errtrace
#set -o nounset
#set -o pipefail

echo "running auto-update.sh in dir: $(pwd)"
echo

set +e
RNDSTR=$(python -c 'import uuid; print(uuid.uuid4().hex.upper()[0:6])')
set -e

BRANCH_NAME="data-update-$(date +"%m-%d")-${RNDSTR}"

git branch "${BRANCH_NAME}" || true
git checkout "${BRANCH_NAME}"

if [[ $GITHUB_ACTIONS == "true" ]]; then
    git config --global user.email "jgehrcke@googlemail.com"
    git config --global user.name "automation"
fi

make update-csv
git status --untracked=no --porcelain
git commit data.csv -m "data.csv: update $(date +"%m-%d")" || true

#make update-jhu-data

# RKI data: set previous data set aside. Use as "base" for tolerant merge, below.
set -x
for CPATH in *-rki-*.csv; do
    /bin/mv -f "${CPATH}" "${CPATH}.previous"
done

# Get current data set. Use as "extension" for tolerant merge, below.
python tools/build-rki-csvs.py

# Set the (newly) build-rki-csvs.py-generated files aside, as "extension". Then
# do a tolerant merge of base and extension, using data points (rows) of the
# previous data set when the new (current) data set deviates from the previous
# one by less than a threshold. This is to mitigate the effects of an ArcGIS
# query instability, to produce better (more useful) diffs -- see
# https://github.com/jgehrcke/covid-19-germany-gae/pull/274.
for FPATH in *-rki-*.csv; do

    # Set aside as "new"/"current"/"extension" (compared to
    # "old"/"previous"/"base").
    /bin/mv -f "${FPATH}" "${FPATH}.current"

    # See if this is about cases or deaths, and choose the merge threshold
    # correspondingly.
    if [[ $FPATH =~ "cases" ]]; then
        THRESHOLD="15"
    elif [[ $FPATH =~ "deaths" ]]; then
        THRESHOLD="5"
    else
        echo "FPATH $FPATH did not match either pattern: check manually"
        exit 1
    fi

    cat "${FPATH}.previous" | wc -l
    stat "${FPATH}.previous"
    cat "${FPATH}.previous" | head -n3
    cat "${FPATH}.previous" | tail -n2

    cat "${FPATH}.current" | wc -l
    stat "${FPATH}.current"
    cat "${FPATH}.current" | head -n3
    cat "${FPATH}.current" | tail -n2

    # Select rows by the sum_ column only, to make this selection consistent
    # across data sets resolved by state/AGS.
    python tools/csv-epsilon-merge.py \
    --threshold=${THRESHOLD} --column-allowlist-pattern 'sum_*' \
    "${FPATH}.previous" "${FPATH}.current" > \
        "${FPATH}"
done
set +x

git status --untracked=no --porcelain
git commit -a -m "RKI data: update: $(date +"%m-%d")" || true

python tools/build-rl-csvs.py
git status --untracked=no --porcelain
git commit -a -m "cases-rl-*: update: $(date +"%m-%d")" || true

python tools/plot-compare-sources.py
#git add gae/static/data-sources-comparison-2020-* gae/static/case-rate-rw-*
git commit -a -m "daily-change-plot-latest: update $(date +"%m-%d")"

git push

