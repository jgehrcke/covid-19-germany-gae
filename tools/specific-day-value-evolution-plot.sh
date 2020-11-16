#!/usr/bin/env bash
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

INFILE="deaths-rki-by-state.csv"
DAY_OF_INTEREST="2020-03-30"
OUTFILENAME="rki-deaths-on-${DAY_OF_INTEREST}-evolution.csv"

echo "commit_time_iso8601,deaths_sum" > ${OUTFILENAME}

# Iterate through commit hashes. Order: past -> future.
for commit in $(git rev-list --reverse master)
do
    COMMIT_TIME_ISO8601=$(git show -s --format=%ci "${commit}")

    # Get last column (known to be sum_deaths) for the row on day of interest.
    set +e
    DEATHS_SUM=$(git show "${commit}:${INFILE}" | grep "${DAY_OF_INTEREST}" | awk -F, '{print $NF}')
    set -e

    # https://unix.stackexchange.com/a/146945/13256
    if [[ ! -z "${DEATHS_SUM// }" ]]; then
        echo "sum(deaths) in ${INFILE} at ${COMMIT_TIME_ISO8601}: ${DEATHS_SUM}"
    else
        echo "no data point extracted for commit $commit: emtpy val"
        continue
    fi

    echo "${COMMIT_TIME_ISO8601},${DEATHS_SUM}" >> ${OUTFILENAME}
done
