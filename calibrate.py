"""Merge published-rate logs (Actions + local backup), dedupe to one value per funding hour,
join to the proxy, fit published = a + b*proxy. Usage:
  python calibrate.py <proxy_hourly.csv> <published.csv> [<published_local.csv> ...]"""
import sys, pandas as pd, numpy as np
proxy = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)
logs = pd.concat([pd.read_csv(p) for p in sys.argv[2:]])
logs["funding_time"] = pd.to_datetime(logs.funding_time, utc=True)
logs["polled_at"] = pd.to_datetime(logs.polled_at, utc=True)
pub = logs.sort_values("polled_at").groupby("funding_time").funding_rate.last()   # last poll per hour
exp = pd.date_range(pub.index.min(), pub.index.max(), freq="h", tz="UTC")
print(f"published hours: {len(pub)} of {len(exp)} expected ({len(exp)-len(pub)} missed)")
j = pd.DataFrame({"pub": pub, "proxy": proxy.funding_rate_est, "q": proxy.quality}).dropna()
j = j[j.q != "stale"]
if len(j) < 24: sys.exit(f"only {len(j)} matched hours -- keep logging")
b, a = np.polyfit(j.proxy, j.pub, 1); r = np.corrcoef(j.proxy, j.pub)[0, 1]
res = j.pub - (a + b * j.proxy)
print(f"n={len(j)}  intercept a={a:.3e}  slope b={b:.3f}  r={r:.3f}  resid MAE={res.abs().mean():.2e}")
print(f"mean pub {j.pub.mean():.3e} vs proxy {j.proxy.mean():.3e}  sign agreement {(np.sign(j.pub)==np.sign(j.proxy)).mean():.1%}")
print("stage:", "first check only (<168)" if len(j) < 168 else "linear calibration usable (>=336)" if len(j) >= 336 else "bias/scale check (168-335)")
