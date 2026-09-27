"""One-shot poll of Coinbase's published XRP PERP (XPP-20DEC30-CDE) funding rate. No API key.
Endpoint shows the LAST SETTLED hour (already 75/25-smoothed by Coinbase). Appends every poll;
dedupe by funding_time at analysis time. Output path: $FUNDING_OUT, default xrp_perp_funding_published.csv.
Used by both GitHub Actions (primary) and the laptop scheduled task (backup) -- identical schema."""
import requests, csv, os, sys, time
URL = "https://api.coinbase.com/api/v3/brokerage/market/products/XPP-20DEC30-CDE"
OUT = os.environ.get("FUNDING_OUT", "xrp_perp_funding_published.csv")
SOURCE = os.environ.get("FUNDING_SOURCE", "actions")
HDR = ["polled_at", "source", "funding_time", "funding_rate", "open_interest", "index_price", "last_price"]
for k in range(4):
    try:
        p = requests.get(URL, timeout=20); p.raise_for_status(); p = p.json()
        f = p["future_product_details"]; break
    except Exception as e:
        print("attempt", k, e, file=sys.stderr); time.sleep(5 * (k + 1))
else:
    sys.exit(1)
row = [time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), SOURCE, f["funding_time"], f["funding_rate"],
       f.get("open_interest", ""), f.get("index_price", ""), p.get("price", "")]
new = not os.path.exists(OUT)
with open(OUT, "a", newline="") as fh:
    w = csv.writer(fh)
    if new: w.writerow(HDR)
    w.writerow(row)
print(row)
