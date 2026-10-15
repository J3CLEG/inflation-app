"""Build the Inflation Monitor iPhone web app.

Usage: python3 -I build_app.py <data_dir> <template.html> <briefing.json> <out.html>
<data_dir> holds observations.csv, momentum.csv, projections.csv, releases.csv,
contributions.csv, series.csv, events.csv (from pipeline.py plus the release
calendar and BLS Table 7 contributions).
"""
import csv, json, sys, datetime

data_dir, template, briefing, out = sys.argv[1:5]

def rows(name):
    with open(f"{data_dir}/{name}") as f:
        return list(csv.DictReader(f))

def num(v):
    return None if v in ("", None) else float(v)

series = rows("series.csv")
obs = {}
for r in rows("observations.csv"):
    obs.setdefault(r["series"], []).append([r["month"], num(r["yoy"])])
mom = {}
for r in rows("momentum.csv"):
    mom.setdefault(r["series"], []).append([r["month"], num(r["mom_sa"]), num(r["ann3"]), num(r["ann6"])])
proj = {}
for r in rows("projections.csv"):
    proj.setdefault(r["series"], {}).setdefault(r["scenario"], {"pace": num(r["assumed_mom"]), "pts": []})["pts"].append([r["month"], num(r["yoy"])])
today = datetime.date.today().isoformat()
releases = [r for r in rows("releases.csv") if r["release_date"] >= today]
contrib = rows("contributions.csv")
for c in contrib:
    c["effect_pts"] = float(c["effect_pts"]); c["yoy_pct"] = float(c["yoy_pct"])
events = rows("events.csv")

data = {
    "built": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
    "series": [{k: s[k] for k in ("key", "label", "group", "class", "latest_month", "url")} for s in series],
    "obs": obs, "mom": mom, "proj": proj, "releases": releases,
    "contrib": contrib, "events": events,
    "briefing": json.load(open(briefing)),
}
html = open(template).read()
marker = "/*__DATA__*/null"
assert marker in html, "template is missing the data marker"
html = html.replace(marker, json.dumps(data, separators=(",", ":")).replace("</", "<\\/"))
open(out, "w").write(html)
print(f"wrote {out} ({len(html):,} bytes)")
