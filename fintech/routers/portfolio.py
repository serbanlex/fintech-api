from .helpers.input import input_file
from fastapi import APIRouter
import yfinance
import urllib.parse
from fastapi.responses import JSONResponse
import logging

# setup fastAPI router and tickers portfolio input file
router = APIRouter(prefix="/fintech/portfolio")


# GET endpoint that returns the portfolio (all available tickers)
# The tickers can be filtered by: greater than a market cap, region (country), exchange, sector
@router.get("/tickers", tags=["Portfolio"])
async def get_all_tickers(market_cap_min: float = None, market_cap_max: float = None,
                          country: str = None,
                          exchange: str = None,
                          sector: str = None):

    input_file.read()

    file_lines = input_file.lines

    # here we will store every existent ticker that fits all filters
    tickers_list = []

    # taking each line content one by one, having each ticker
    for ticker in file_lines:
        # readlines() includes a \n in the end of each ticker, so we format to not have it anymore
        ticker = ticker.rstrip()
        ticker_info = yfinance.Ticker(ticker).info

        # check to see if actual ticker fits the filters

        # country filter (also  check if the ticker returned has the queried field in its structure, using .get)
        if country:
            country = urllib.parse.unquote(country)
            country = country.removesuffix(" ")

            if ticker_info.get("country") != country:
                continue

        # sector filter
        if sector and ticker_info.get("sector"):
            sector = urllib.parse.unquote(sector)
            sector = sector.removesuffix(" ")

            if ticker_info.get("sector") != sector:
                continue

        if ticker_info.get("marketCap"):
            market_cap = ticker_info["marketCap"]
            # market cap filter
            if market_cap_min:
                if market_cap < market_cap_min:
                    continue

                if market_cap_max:
                    # we're interested for in between values and we already know the minimum is fine
                    if market_cap > market_cap_max:
                        continue

            if market_cap_max:
                # at this point we know there is no minimum requirement so we are only interested about max
                if market_cap > market_cap_max:
                    continue

        # exchange filter
        if exchange and ticker_info.get("exchange"):
            exchange = urllib.parse.unquote(exchange)
            exchange = exchange.removesuffix(" ")

            # exchanges are all uppercase, so we may accept that the user is lazy and writes it lower
            exchange = exchange.upper()

            if ticker_info.get("exchange") != exchange:
                continue

        # finally, add the ticker if it passed all the filters
        tickers_list.append(ticker)

    return JSONResponse(content=tickers_list)


# POST api endpoint for saving a ticker into the portfolio
@router.post("/tickers/{ticker}", tags=["Portfolio"])
async def add_ticker(ticker: str):
    # make sure that every ticker we add is all in uppercase, for consequence
    ticker = ticker.upper()

    ticker_info = yfinance.Ticker(ticker).info

    # check if the ticker is valid
    try:
        ticker_info['marketCap']
    except KeyError:
        logging.error(f"Attempt of adding {ticker} failed: Invalid ticker")
        return JSONResponse(status_code=403, content="Invalid ticker")

    response = input_file.add(ticker)

    return response


# DELETE endpoint in order to delete an existent ticker
@router.delete("/tickers/{ticker}", tags=["Portfolio"])
async def delete_ticker(ticker: str):
    ticker = ticker.upper()

    response = input_file.delete(ticker)

    return response
