SHELL=/bin/bash -o pipefail -o errexit -o nounset


.PHONY: update-csv
update-csv:
	python tools/update_csv.py
	/bin/cp data.csv.new data.csv
	git diff data.csv
	@echo "Diff looks good? Run git commit data.csv -m 'data.csv: update MM-DD'"


.PHONY: plots
plots:
	cd gae/static/plots && python ../../../tools/plot.py ../../../data.csv


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


.PHONY: install-python-dependencies
install-python-dependencies:
	pip install gae/requirements.txt
