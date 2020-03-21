SHELL=/bin/bash -o pipefail -o errexit -o nounset


.PHONY: update-csv
update-csv:
	python tools/update_csv.py
	/bin/cp data.csv.new data.csv
	git diff data.csv
	@echo "Diff looks good? Run git commit data.csv -m 'data.csv: automated update'"


.PHONY: plots
plots:
	cd plots && python ../tools/plot.py ../data.csv


.PHONY: install-python-dependencies
install-python-dependencies:
	pip install gae/requirements.txt

