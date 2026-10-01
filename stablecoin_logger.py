"""Daily stablecoin supply from DefiLlama's free stablecoins API (no key). Tier 1 of the stablecoin collector
(xrp-bot docs/data.md §6a). Appends ONE row per run day to data/stablecoin_supply.csv, holding the PRIOR CLOSED UTC day:
  observed_at            UTC fetch time (the bot's leakage guard: only rows with observed_at <= decision time)
  source_date            DefiLlama's date for the values = yesterday (UTC) relative to observed_at
  total_circulating_usd  all stablecoins, all peg types, in USD (DefiLlama's headline total)
  usd_pegged_usd         USD-pegged stablecoins only (no FX moves from EUR / JPY / ... coins)
  usdt_usd, usdc_usd, rlusd_usd   per coin, USD value
Endpoints (checked against the live API 2026-10-01): /stablecoincharts/all for the totals and
/stablecoincharts/all?stablecoin=<id> per coin (USDT 1, USDC 2, RLUSD 250); each returns a list of daily points
{"date": "<unix s, 00:00 UTC>", "totalCirculatingUSD": {"peggedUSD": ..., "peggedEUR": ..., ...}, ...}.
The last point is the current day's live value; yesterday's point counts as closed only once a point for today
exists in every series. Not closed yet, bad response, or a missing coin / day: no row, exit 1 (the run fails on
GitHub). Skips (exit 0) if a row with today's UTC observed date already exists. Never a partial row."""
import csv, datetime as dt, math, os, sys, time
import requests

BASE = "https://stablecoins.llama.fi/stablecoincharts/all"
SERIES = {"total": None, "usdt": 1, "usdc": 2, "rlusd": 250}  # DefiLlama stablecoin ids
OUT = os.environ.get("STABLECOIN_OUT", "data/stablecoin_supply.csv")
HDR = ["observed_at", "source_date", "total_circulating_usd", "usd_pegged_usd", "usdt_usd", "usdc_usd", "rlusd_usd"]


def fetch(sid):
    params = {} if sid is None else {"stablecoin": sid}
    for k in range(4):
        try:
            r = requests.get(BASE, params=params, timeout=30); r.raise_for_status()
            return r.json()
        except Exception as e:
            print("fetch", sid, "attempt", k, e, file=sys.stderr); time.sleep(5 * (k + 1))
    raise RuntimeError(f"fetch failed: stablecoin={sid}")


def _day(p):
    return dt.datetime.fromtimestamp(int(p["date"]), dt.timezone.utc).date()


def _usd(x):
    v = float(x)
    if not math.isfinite(v) or v <= 0:
        raise ValueError(f"bad value {x!r}")
    return v


def closed_point(points, today, name):
    """The point for today - 1, required to be closed: the series must already hold a point dated today."""
    if not isinstance(points, list) or not points:
        raise ValueError(f"{name}: empty or non-list response")
    if _day(points[-1]) != today:
        raise ValueError(f"{name}: yesterday not closed yet (last point {_day(points[-1])}, today {today})")
    want = today - dt.timedelta(days=1)
    hit = [p for p in points if _day(p) == want]
    if len(hit) != 1:
        raise ValueError(f"{name}: {len(hit)} points for {want}")
    return hit[0]["totalCirculatingUSD"]


def parse(responses, today):
    """responses: {"total"|"usdt"|"usdc"|"rlusd": parsed JSON}; today: UTC date of the fetch.
    Returns (source_date ISO, [total, usd_pegged, usdt, usdc, rlusd]) or raises."""
    usd = {k: closed_point(responses[k], today, k) for k in SERIES}
    total = sum(_usd(v) for v in usd["total"].values())
    vals = [total, _usd(usd["total"]["peggedUSD"])] + [_usd(usd[k]["peggedUSD"]) for k in ("usdt", "usdc", "rlusd")]
    return (today - dt.timedelta(days=1)).isoformat(), vals


def already_logged(path, day):
    if not os.path.exists(path):
        return False
    with open(path, newline="") as fh:
        return any(r["observed_at"][:10] == day for r in csv.DictReader(fh))


def main():
    now = dt.datetime.now(dt.timezone.utc)
    observed_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    if already_logged(OUT, observed_at[:10]):
        print("row for", observed_at[:10], "already present; skip"); return 0
    try:
        source_date, vals = parse({k: fetch(sid) for k, sid in SERIES.items()}, now.date())
    except Exception as e:
        print("no row written:", repr(e), file=sys.stderr); return 1
    row = [observed_at, source_date] + [f"{v:.2f}" for v in vals]
    if os.path.dirname(OUT):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="") as fh:
        w = csv.writer(fh)
        if new: w.writerow(HDR)
        w.writerow(row)
    print(row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
