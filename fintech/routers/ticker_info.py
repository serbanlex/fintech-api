from .helpers.input import input_file
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse

# setup fastAPI router and tickers portfolio input file
router = APIRouter(prefix="/fintech/ticker")


# GET endpoint for checking price to earnings
@router.get("/{ticker}/price-to-earnings", tags=["Ticker info"])
async def get_forward_pe(ticker: str):
    ticker_object = input_file.ticker_object(ticker)
    ticker_info = ticker_object.info
    forward_pe = ticker_info["forwardPE"]

    return JSONResponse(content=forward_pe)


# GET endpoint for market cap
@router.get("/{ticker}/market-cap", tags=["Ticker info"])
async def get_market_cap(ticker: str):
    ticker_object = input_file.ticker_object(ticker)
    ticker_info = ticker_object.info
    market_cap = ticker_info["marketCap"]

    return JSONResponse(content=market_cap)


# GET endpoint for last dividend value
@router.get("/{ticker}/last-dividend-value", tags=["Ticker info"])
async def get_last_dividend_value(ticker: str):
    ticker_object = input_file.ticker_object(ticker)
    ticker_info = ticker_object.info
    dividends_value = ticker_info["lastDividendValue"]

    return JSONResponse(content=dividends_value)


# GET endpoint for dividends evolution of a ticker
@router.get("/{ticker}/dividends", tags=["Ticker info"])
async def get_historical_dividends(ticker: str):
    ticker_object = input_file.ticker_object(ticker)
    ticker_dividends = ticker_object.dividends

    # from pandas.core.series.Series to dict
    ticker_dividends = ticker_dividends.to_dict()

    # dict keys in a json can't be of type Timestamp so we have to make a new one, with string keys
    dividends_map = {}
    timestamp_list = list(ticker_dividends.keys())

    for timestamp in timestamp_list:
        # timestamp object to string
        timestamp_string = timestamp.to_pydatetime()
        timestamp_string = timestamp_string.strftime("%d %b %Y")

        dividends_map[timestamp_string] = ticker_dividends[timestamp]

    return JSONResponse(content=dividends_map)


# GET endpoint for high/low for a given period, on a saved ticker
@router.get("/{ticker}/high-low", tags=["Ticker info"])
async def get_high_low(ticker: str, period: str):
    ticker_object = input_file.ticker_object(ticker)

    try:
        ticker_history = ticker_object.history(period=period)
    except ValueError as e:
        logging.error(e)
        return JSONResponse(status_code=401, content=e)

    high = ticker_history["High"]
    low = ticker_history["Low"]

    high_map = high.to_dict()
    low_map = low.to_dict()

    # merging high and low dicts into one with the same timestamp and a touple as value
    high_low_map = {}
    timestamp_list = list(low_map.keys())

    for timestamp in timestamp_list:
        # timestamp object to string
        timestamp_string = timestamp.to_pydatetime()
        timestamp_string = timestamp_string.strftime("%d %b %Y")

        high_low_map[timestamp_string] = (low_map[timestamp], high_map[timestamp])

    return JSONResponse(content=high_low_map)
