from .helpers.input import input_file
from .helpers.helpers import TickerHistory, EmailSender
import yagmail
from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import JSONResponse
from datetime import date
import urllib.parse


# setup fastAPI router and tickers portfolio input file
router = APIRouter(prefix="/fintech/graphs")


# GET endpoint for a history graph of the price (close index) between two dates for maximum 5 existent tickers
@router.get("/tickers/{ticker_list}/history/", tags=["History graphs"])
async def get_tickers_shared_history_graph(ticker_list: str, start: str, end: str = None):
    # format the list obtained with %20 and other url specific characters
    ticker_list = ticker_list.upper()
    ticker_list = ticker_list.removesuffix(" ")
    ticker_list = urllib.parse.unquote(ticker_list)

    # retrieve the list of tickers that we have
    ticker_list = ticker_list.split(" ")

    # check if we have more than 5 tickers and at least one
    given_tickers_number = len(ticker_list)
    if (1 <= given_tickers_number <= 5) is False:
        return JSONResponse(status_code=400, content="There has to be at least 1 ticker, and maximum 5.")

    # if end date doesn't exist, set it to today
    if end is None:
        end = date.today().strftime('%Y-%m-%d')

    # tickers already added to portfolio will go here
    final_ticker_list = []

    # i'll use these for naming the resulted graph specifically
    graph_name_tickers = ""
    underscore = ""

    for ticker in ticker_list:
        # see if the ticker is added to the portfolio
        ticker_exists = input_file.check_ticker(ticker)
        if ticker_exists:
            final_ticker_list.append(ticker)
            graph_name_tickers = graph_name_tickers + underscore + ticker
            underscore = "_"

    valid_tickers_number = len(final_ticker_list)

    if valid_tickers_number:
        history_object = TickerHistory(final_ticker_list, start, end)
        graph = history_object.graph(graph_name_tickers)

        return graph

    else:
        return JSONResponse(status_code=400, content="None of tickers given is added to the portfolio")


@router.post("/tickers/{ticker_list}/history/send_graph/", tags=["History graphs"])
async def email_graph(email: str, graph=Depends(get_tickers_shared_history_graph)):
    if graph.status_code != 200:
        return graph

    sender = EmailSender(email, "Your graph bro", "Here's the graph for a couple of tickers. Enjoy!",
                         yagmail.inline(graph.path))
    sender.send_mail()

    return JSONResponse(status_code=200, content="Email sent successfully.")
