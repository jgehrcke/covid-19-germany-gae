SHELL=/bin/bash -o pipefail -o errexit -o nounset

JHU_REPO_DIR?=jhu-csse-covid-19-data

.PHONY: update-csv
update-csv:
	python tools/update_csv.py
	/bin/cp data.csv.new data.csv
	git diff data.csv
	@echo "Diff looks good? Run git commit data.csv -m 'data.csv: update MM-DD'"


.PHONY: plots
plots:
	cd gae/static/plots && python ../../../tools/plot.py ../../../cases-rki-by-state.csv


.PHONY: deploy-staging
deploy-staging:
	cd gae && gcloud app deploy --no-promote


.PHONY: deploy-prod
deploy-prod:
	cd gae && gcloud app deploy --promote
	echo "do you need to 'make deploy-cron'?"


.PHONY: deploy-cron
deploy-cron:
	cd gae && gcloud app deploy cron.yaml


.PHONY: update-jhu-data
update-jhu-data:
	@if [ -d "${JHU_REPO_DIR}" ]; then \
	    echo "updating ..." && \
		cd ${JHU_REPO_DIR} && git pull; \
	else \
		git clone https://github.com/CSSEGISandData/COVID-19 ${JHU_REPO_DIR}; \
	fi


.PHONY: install-python-dependencies
install-python-dependencies:
	pip install gae/requirements.txt
