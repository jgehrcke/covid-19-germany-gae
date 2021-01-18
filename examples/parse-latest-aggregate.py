import json
import pandas

# Parse CSV file, ignore first line.
print(pandas.read_csv("more-data/latest-aggregate.csv", comment="#"))

# Read first line and JSON-decode meta data.
with open("more-data/latest-aggregate.csv", "rb") as f:
    firstline = f.readline().decode("utf-8")
    metadata = json.loads(firstline.strip("#"))

print(metadata)
