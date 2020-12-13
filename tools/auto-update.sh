#!/usr/bin/env bash
set -o errexit
set -o errtrace
#set -o nounset
set -o pipefail

set +e
RNDSTR=$(cat /dev/urandom | tr -dc "a-zA-Z0-9" | fold -w 5 | head -n 1)
set -e

BRANCH_NAME="data-update-$(date +"%m-%d")-${RNDSTR}"

# git checkout master
# git pull
# git branch "${BRANCH_NAME}" || true
# git checkout "${BRANCH_NAME}"

source tools/env.sh

#make update-csv
#git status --untracked=no --porcelain
#git commit data.csv -m "data.csv: update $(date +"%m-%d")" || true

#make update-jhu-data

# Set previous data set aside. Use as "base" for merge later.
set -x
for CPATH in *-rki-*.csv; do
    /bin/mv -f "${CPATH}" "${CPATH}.previous"
done

# Get current data set. Use as "extension" for merge later.
python tools/build-rki-csvs.py

# Set the newly generated files (by build-rki-csvs.py) aside as "extension".
# Then do a tolerant merge of base and extension, using data points (rows)
# of the previous data set when the new (current) data set deviates from the
# previous one only by a tiny amount.
for FPATH in *-rki-*.csv; do
    /bin/mv -f "${FPATH}" "${FPATH}.current"

    # See if this is about cases or deaths, and choose the merge threshold
    # correspondingly.
    if [[ $FPATH =~ "cases" ]]; then
        THRESHOLD="10"
    elif [[ $FPATH =~ "deaths" ]]; then
        THRESHOLD="4"
    else
        echo "FPATH $FPATH did not match either pattern: check manually"
        exit 1
    fi

    python tools/csv-epsilon-merge.py \
    --threshold=${THRESHOLD} --column-allowlist-pattern 'sum_*' \
    "${FPATH}.previous" "${FPATH}.current" > \
        "${FPATH}"
done
set +x

git status --untracked=no --porcelain
#git commit -a -m "RKI data: update: $(date +"%m-%d")" || true

python tools/build-rl-csvs.py
git status --untracked=no --porcelain
#git commit -a -m "cases-rl-*: update: $(date +"%m-%d")" || true

#python tools/plot-compare-sources.py
#git add gae/static/data-sources-comparison-2020-* gae/static/case-rate-rw-*
#git commit -a -m 'landing page update'

git push

