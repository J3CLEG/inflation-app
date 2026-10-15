# Inflation Monitor

An iPhone web app tracking U.S. inflation from the official BLS CPI and BEA PCE releases: gauges against the Fed's 2% target, sticky vs. transitory drivers, monthly momentum, six-month base-effect scenarios, and the release calendar.

**Open it:** https://j3cleg.github.io/inflation-app — in Safari, tap Share → Add to Home Screen.

Refreshed after each CPI and PCE release by a scheduled Claude task.

- `src/pipeline.py`: pulls the official series (FRED mirror of BLS/BEA) and computes 12-month, momentum and scenario tables into `data/`
- `src/build_app.py` + `src/app_template.html`: embeds `data/` and `src/briefing.json` into the app
- `src/make_site.py`: wraps it as the installable `index.html`

Rebuild: `python3 -I src/pipeline.py raw data --fetch && python3 -I src/build_app.py data src/app_template.html src/briefing.json /tmp/frag.html && python3 -I src/make_site.py /tmp/frag.html index.html`

Data: U.S. Bureau of Labor Statistics; U.S. Bureau of Economic Analysis. Projections are arithmetic scenarios, not forecasts.
