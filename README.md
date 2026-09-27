# XRP perp funding logger

Captures Coinbase's published hourly funding for XPP-20DEC30-CDE. The endpoint only exposes the last settled
hour, so any hour not polled is gone.

## Primary: GitHub Actions
1. Create a **public** repo with these files at the root. Public matters: private repos get 2,000 free Actions
   min/month, and 96 runs/day at the 1-minute billing floor is ~2,900 min/month. Funding data is not sensitive.
2. Push. Actions tab -> enable workflows if prompted -> run `xrp-perp-funding-logger` once via "Run workflow".
3. Confirm a commit lands with `xrp_perp_funding_published.csv`.

## Backup: deployment laptop
Same script, different output file, so the two never conflict in git:
- Windows Task Scheduler, every 15 min:
  `cmd /c "set FUNDING_OUT=C:\path\published_local.csv&& set FUNDING_SOURCE=local&& python C:\path\log_funding.py"`
- macOS/Linux cron: `*/15 * * * * FUNDING_OUT=$HOME/funding/published_local.csv FUNDING_SOURCE=local python3 /path/log_funding.py`
Once the bot is live it polls Coinbase anyway -- have it log funding itself and retire this task.

## Calibrate
`python calibrate.py ../phase1/data/xrp_perp_funding_est_hourly.csv xrp_perp_funding_published.csv published_local.csv`
~1 week: bias/scale check. ~2 weeks: linear fit usable. ~4 weeks: tail confidence.
