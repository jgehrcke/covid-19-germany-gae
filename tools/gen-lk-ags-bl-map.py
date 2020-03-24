# MIT License

# Copyright (c) 2020 Dr. Jan-Philip Gehrcke

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
This program is part of https://github.com/jgehrcke/covid-19-germany-gae

Purpose of this tool is to create a JSON file a mapping between "Amtlicher
Gemeindeschlüssel" (AGS) to Bundesland.

https://de.wikipedia.org/wiki/Amtlicher_Gemeindeschl%C3%BCssel

This association is constant, this tool is here for transparency.
"""

import json

import pandas as pd
import numpy as np

# original data source for this association is documented in
# https://github.com/jgehrcke/covid-19-germany-gae/issues/46
df = pd.read_csv("landkreise.csv")

# NaNs for kreisefreie Stadt Berlin need to be replaced with 0 before casting.
df["AGS"] = df["AGS"].fillna(0.0).astype("int")
all_agss = list(df["AGS"])
ags_bl_map = {}
for ags in all_agss:
    if ags == 0:
        # These are rows for Berlin, kreisfreie Stadt. Manually set this to
        # 11000 (which seems to be what some use).
        ags_bl_map["11000"] = "Berlin"
        continue
    matches = df[df["AGS"] == ags]["BL"].tolist()
    # double-check that data set is clean, one row per non-zero AGS
    assert len(matches) == 1
    ags_bl_map[ags] = matches[0]

# Note that JSON only allows text keys, not numbers.
with open("lk-ags-to-bl.json", "wb") as f:
    f.write(json.dumps(ags_bl_map, indent=2, ensure_ascii=False).encode("utf-8"))
