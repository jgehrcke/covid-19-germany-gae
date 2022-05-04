#!/usr/bin/env bash
set -o errexit
set -o errtrace

# GITHUB_ACTIONS may be unbound
#set -o nounset
#set -o pipefail

# Change this in local dev branch to not create a branch, and to not make any
# commits.
GIT_COMMIT_CHANGES="yes"

echo "running auto-update.sh in dir: $(pwd)"

RNDSTR=$(python -c 'import uuid; print(uuid.uuid4().hex.upper()[0:4])')
UPDATE_ID="$(date +"%m-%d-%H%M" --utc)-${RNDSTR}"
BRANCH_NAME="data-update/${UPDATE_ID}"

echo "generated branch name: ${RNDSTR}"

if [[ $GIT_COMMIT_CHANGES == "yes" ]]; then
    git branch "${BRANCH_NAME}" || true
    git checkout "${BRANCH_NAME}"
fi


if [[ $GITHUB_ACTIONS == "true" ]]; then
    # https://github.community/t/github-actions-bot-email-address/17204
    # https://github.com/actions/checkout/issues/13#issuecomment-724415212
    git config --local user.email "action@github.com"
    git config --local user.name "GitHub Action"
fi

# make update-csv
# git status --untracked=no --porcelain
# if [[ $GIT_COMMIT_CHANGES == "yes" ]]; then
#     git commit data.csv -m "data.csv: update ${UPDATE_ID}" || true
# fi

#make update-jhu-data

# RKI data: set previous data set aside. Use as "base" for tolerant merge, below.
set -x
for CPATH in *-rki-*.csv; do
    # Copy, so that the current data files are left intact when something
    # goes wrong below.
    /bin/cp -f "${CPATH}" "${CPATH}.previous"
done

# Get current data set. Use as "extension" for tolerant merge, below.
set +e
python tools/build-rki-csvs.py
FETCH_RKI_ECODE=$?
set -e

# Skip RKI data processing if fetching an update failed.
# This happens every now and then as of ArcGIS system downtime.
if [ $FETCH_RKI_ECODE -ne 0 ]; then
    echo "error: build-rki-csvs.py returned with code ${FETCH_RKI_ECODE} -- skip"

    # revert the renames
    # Note(JP): not needed when  using cp instead of mv above!
    # for CPATHP in *-rki-*.csv.previous; do
    #     # use ${var/Pattern/Replacement} (replace first occurrence)
    #     /bin/mv -f "${CPATHP}" "${CPATHP/.previous/}"
    # done
else

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

    git status --untracked=no --porcelain
    if [[ $GIT_COMMIT_CHANGES == "yes" ]]; then
        git add \
            cases-rki-by-ags.csv \
            cases-rki-by-state.csv \
            deaths-rki-by-ags.csv \
            deaths-rki-by-state.csv || true
        git commit -m "RKI data: update: ${UPDATE_ID}" || true
    fi

fi

# Risklayer Covid data: "This service has been discontinued since March 13th, 2022"
# python tools/build-rl-csvs.py
# git status --untracked=no --porcelain
# if [[ $GIT_COMMIT_CHANGES == "yes" ]]; then
#     git add \
#         cases-rl-crowdsource-by-ags.csv \
#         cases-rl-crowdsource-by-state.csv \
#         deaths-rl-crowdsource-by-ags.csv \
#         deaths-rl-crowdsource-by-state.csv || true
#     git commit -m "RL data: update: ${UPDATE_ID}" || true
# fi


#python tools/7di.py cases-rl-crowdsource-by-ags.csv more-data/7di-rl-by-ags.csv
#python tools/7di.py cases-rl-crowdsource-by-state.csv more-data/7di-rl-by-state.csv
python tools/7di.py cases-rki-by-ags.csv more-data/7di-rki-by-ags.csv
#python tools/7di.py cases-rki-by-state.csv more-data/7di-rki-by-state.csv

if [[ $GIT_COMMIT_CHANGES == "yes" ]]; then
    git add more-data/7di-*.csv || true
    git commit -m "data: 7di update ${UPDATE_ID}" || true
fi

python tools/generate-latest-aggregate.py
if [[ $GIT_COMMIT_CHANGES == "yes" ]]; then
    git add more-data/latest-aggregate.csv || true
    git commit -m "data: latest-aggregate update ${UPDATE_ID}" || true
fi

python tools/plot-compare-sources.py

if [[ $GIT_COMMIT_CHANGES == "yes" ]]; then
    git add plots/daily-change-plot* || true
    git commit -m "plots: dcp update ${UPDATE_ID}" || true
fi


python tools/heatmap.py \
    more-data/7di-rki-by-ags.csv \
    --label-data-source="RKI data" \
    --figure-out-pprefix=plots/germany-heatmap-7ti-rki

# python tools/heatmap.py \
#     more-data/7di-rl-by-ags.csv \
#     --label-data-source="Risklayer data" \
#     --figure-out-pprefix=plots/germany-heatmap-7ti-rl

if [[ $GIT_COMMIT_CHANGES == "yes" ]]; then
    git add plots/germany-heatmap-7ti-* || true
    git commit -m "plots: gh7tirki update ${UPDATE_ID}" || true
fi

if [[ $GITHUB_ACTIONS == "true" ]]; then
    git push --set-upstream origin "${BRANCH_NAME}"
else
    # git push
    # When run locally skip the rest
    exit
fi


if [[ $GITHUB_ACTIONS == "true" ]]; then
    # `hub` CLI is available through actions/checkout@v2 -- nice!
    # https://github.com/github/hub#github-actions
    # https://hub.github.com/hub-pull-request.1.html
    PR_URL="$(hub pull-request \
        --base master \
        --head "${BRANCH_NAME}" \
        --message "Automatic data update ${UPDATE_ID}" \
        --reviewer jgehrcke)"

    # Split string on slashes and get last item, for extracting PR ID
    # credits: https://stackoverflow.com/a/3162500/145400
    PR_ID=${PR_URL##*/}
    echo "::set-output name=pr_url::${PR_URL}"
    echo "::set-output name=pr_id::${PR_ID}"
fi
