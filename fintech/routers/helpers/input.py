# instantiating a class object for the so-called database, so we don't repeat it in every router
from .helpers import Input

portfolio_file = "../resources/tickers.txt"
input_file = Input(portfolio_file)