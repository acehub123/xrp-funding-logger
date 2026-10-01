"""Parser test against a saved DefiLlama response (last 3 daily points of each series, fetched 2026-10-01 17:40Z)."""
import copy, datetime as dt, json, os, sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import stablecoin_logger as sl

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "defillama_stablecoincharts_2026-10-01.json")
TODAY = dt.date(2026, 10, 1)


def test_parse_saved_response():
    resp = json.load(open(FIXTURE))
    source_date, vals = sl.parse(resp, TODAY)
    assert source_date == "2026-09-30"  # prior closed day, not the live 10-01 point
    total, usd_pegged, usdt, usdc, rlusd = vals
    closed = resp["total"][-2]["totalCirculatingUSD"]
    assert total == pytest.approx(sum(closed.values()))
    assert usd_pegged == 311200297805
    assert (usdt, usdc, rlusd) == (183758497423, 74568657800, 2520986370)
    assert total > usd_pegged > usdt + usdc + rlusd
    # missing coin -> raises (no row)
    bad = copy.deepcopy(resp); del bad["rlusd"][-2]["totalCirculatingUSD"]["peggedUSD"]
    with pytest.raises(KeyError):
        sl.parse(bad, TODAY)
    # a series without today's point -> yesterday not closed -> raises (no row)
    bad = copy.deepcopy(resp); bad["usdc"].pop()
    with pytest.raises(ValueError, match="not closed"):
        sl.parse(bad, TODAY)
