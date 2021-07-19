import json
import unittest
from unittest.mock import patch
import yfinance
from fastapi.testclient import TestClient
from app import app
import logging
import yfinance as yf

# A far better approach for testing would have been setting up a clone of the server, in a different folder,
# making an identical test server, but with different resource files.
# As for the purpose of this project, I thought there's no sense in just copying and pasting code all around,
# while testing the same things / functionalities, basically.

client = TestClient(app)


def log_start(test_name):
    logging.info(f"\n------STARTED TESTING {test_name}------\n")


def log_end(test_name):
    logging.info(f"\n------FINISHED TESTING {test_name}------\n")


@unittest.skip("Passed by")
class TestPortfolio(unittest.TestCase):
    route = "/fintech/portfolio"

    def test_get_all_tickers(self):
        log_start("GETTING ALL TICKERS")

        # mock the yfinance ticker info api as we don't really want to depend on it
        # (big loading times, server being up etc.), and we care about an ok response with a dictionary from it
        with patch('yfinance.Ticker.info') as mock_yfinance_info:
            mock_yfinance_info.return_value.ok = True
            mock_yfinance_info.return_value.json.return_value = {
             'country': 'United States',
             'sector': 'Technology',
             'marketCap': 201411241,
             'exchange': '',
            }

            # test if the file exists and everything is retrieved okay
            response = client.get(self.route + "/tickers")
            self.assertEqual(response.status_code, 200)

            # see if we get a list of tickers as response
            response_content = json.loads(response.content)
            self.assertTrue(type(response_content) == list)

        log_end("GETTING ALL TICKERS")

    def test_add_ticker(self):
        log_start("ADD TICKER")

        # add ticker when it doesn't exist (make sure it doesn't exist)
        client.delete(self.route + "/tickers/TSLA")
        response = client.post(self.route + "/tickers/TSLA")
        self.assertEqual(response.status_code, 200)

        # add ticker when it already exists
        response = client.post(self.route + "/tickers/TSLA")
        self.assertEqual(response.status_code, 400)

        log_end("ADD TICKER")

    def test_delete_ticker(self):
        log_start("DELETE TICKER")

        # delete ticker when it exists
        client.post(self.route + "/tickers/TSLA")
        response = client.delete(self.route + "/tickers/TSLA")
        self.assertEqual(response.status_code, 200)

        # delete ticker when it doesn't exist
        client.delete(self.route + "/tickers/TSLA")
        response = client.delete(self.route + "/tickers/TSLA")
        self.assertEqual(response.status_code, 404)

        log_end("DELETE TICKER")


@unittest.skip("Passed by")
class TestTickerInfo(unittest.TestCase):
    route = "/fintech/ticker/"
    portfolio_route = "/fintech/portfolio/tickers/"

    # yfinance_object.info["forwardPE"] works the same way for market cap and last dividend value
    # the test for this one is concludent for those too
    def test_forward_pe(self):
        log_start("FORWARD_PE")

        # request forward PE for an added ticker
        client.post(self.portfolio_route + "TSLA")

        response = client.get(self.route + "TSLA/price-to-earnings")
        response_content = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(response_content), float)

        # request it when it's not there
        client.delete(self.portfolio_route + "TSLA")
        response = client.get(self.route + "TSLA/price-to-earnings")
        self.assertEqual(response.status_code, 404)

        log_end("FORWARD_PE")

    def test_dividends(self):
        log_start("DIVIDENDS EVOLUTION")

        # test for an added ticker
        client.post(self.portfolio_route + "TSLA")
        response = client.get(self.route + "TSLA/dividends")
        response_content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(response_content), dict)

        # test for a deleted ticker
        client.delete(self.portfolio_route + "TSLA")
        response = client.get(self.route + "TSLA/dividends")

        self.assertEqual(response.status_code, 404)

        log_end("DIVIDENDS EVOLUTION")

    def test_high_low(self):
        log_start("HIGH-LOW")

        # test on an added ticker
        client.post(self.portfolio_route + "TSLA")
        response = client.get(self.route + "TSLA/high-low?period=1mo")
        response_content = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        # see if it returns a dictionary with keys that are strings
        self.assertEqual(type(response_content), dict)
        response_content_keys = list(response_content.keys())
        self.assertEqual(type(response_content_keys[0]), str)

        # test on a non-existent ticker
        client.delete(self.portfolio_route + "TSLA")
        response = client.get(self.route + "TSLA/high-low?period=1mo")
        self.assertEqual(response.status_code, 404)

        log_end("HIGH-LOW")


@unittest.skip("Passed by")
class TestGraphs(unittest.TestCase):
    route = "/fintech/graphs/tickers/"
    portfolio_route = "/fintech/portfolio/tickers/"

    @unittest.skip("Passed by")
    def test_return_graph(self):
        log_start("CREATING A GRAPH")

        # creating a graph on some existent tickers with okay dates
        client.post(self.portfolio_route + "TSLA")
        client.post(self.portfolio_route + "AAPL")

        response = client.get(self.route + "tsla%20aapl/history/?start=2016-02-02&end=2020-02-02")
        self.assertEqual(response.status_code, 200)

        # putting dates reverse, in a wrong order (should return 400 bad request, from an exception)
        response = client.get(self.route + "tsla%20aapl/history/?start=2020-02-02&end=2016-02-02")
        self.assertEqual(response.status_code, 400)

        # calling it on unadded tickers
        client.delete(self.portfolio_route + "TSLA")
        client.delete(self.portfolio_route + "AAPL")
        response = client.get(self.route + "tsla%20aapl/history/?start=2016-02-02&end=2020-02-02")
        self.assertEqual(response.status_code, 400)

        # having them back, don't want to lose them forever
        client.post(self.portfolio_route + "TSLA")
        client.post(self.portfolio_route + "AAPL")

        log_end("CREATING A GRAPH")

    def test_email_graph(self):
        log_start("EMAILING A GRAPH")
        # the graph functionality works, we're sure about that. this method inherits the last.
        # emailing remains to test

        client.post(self.portfolio_route + "TSLA")
        client.post(self.portfolio_route + "AAPL")

        # trying to mail an invalid mail
        invalid_email = "something.com"

        response = client.post(self.route + f"tsla%20aapl/history/send_graph/?email={invalid_email}&start=2016-02-02")
        self.assertEqual(response.status_code, 400)

        # trying to mail a valid mail
        valid_email = "dev.alex.serban%40gmail.com"

        response = client.post(self.route + f"tsla%20aapl/history/send_graph/?email={valid_email}&start=2016-02-02")
        self.assertEqual(response.status_code, 200)

        log_end("EMAILING A GRAPH")


class TestIntegrationContract(unittest.TestCase):
    def test_yfinance_contract(self):
        log_start("INTEGRATION CONTRACT WITH THE YAHOO API")

        # calling the real api
        actual = yf.Ticker("PEP").info
        actual_keys = actual.keys()
        logging.info("Called YFinance real API, got a response")

        # calling a mocked api with the structure that we know and that we used all around the project
        with patch('yfinance.Ticker.info') as mock_yfinance_info:
            mock_yfinance_info.return_value.ok = True
            mock_yfinance_info.json.return_value = {
                "zip": "",
                "sector": "",
                "fullTimeEmployees": 0,
                "longBusinessSummary": "sth",
                "city": "Purchase",
                "phone": "914 253 2000",
                "state": "NY",
                "country": "United States",
                "companyOfficers": [],
                "website": "http://www.pepsico.com",
                "maxAge": 1,
                "address1": "700 Anderson Hill Road",
                "industry": "Beverages—Non-Alcoholic",
                "previousClose": 148.2,
                "regularMarketOpen": 148.9,
                "twoHundredDayAverage": 141.99066,
                "trailingAnnualDividendYield": 0.027597843,
                "payoutRatio": 0.7574,
                "volume24Hr": 1321,
                "regularMarketDayHigh": 149.78,
                "navPrice": 123123,
                "averageDailyVolume10Day": 4351971,
                "totalAssets": 312231,
                "regularMarketPreviousClose": 148.2,
                "fiftyDayAverage": 147.20383,
                "trailingAnnualDividendRate": 4.09,
                "open": 148.9,
                "toCurrency": 12312,
                "averageVolume10days": 4351971,
                "expireDate": 1231231,
                "yield": 1231231,
                "algorithm": 1231321,
                "dividendRate": 4.3,
                "exDividendDate": 1622678400,
                "beta": 0.610326,
                "circulatingSupply": 12213,
                "startDate": 1231,
                "regularMarketDayLow": 148.66,
                "priceHint": 2,
                "currency": "USD",
                "trailingPE": 27.565718,
                "regularMarketVolume": 3835526,
                "lastMarket": 1231,
                "maxSupply": 1231,
                "openInterest": 1231,
                "marketCap": 205738524672,
                "volumeAllCurrencies": 213,
                "strikePrice": 231,
                "averageVolume": 5019448,
                "priceToSalesTrailing12Months": 2.8850882,
                "dayLow": 148.66,
                "ask": 149.2,
                "ytdReturn": 213,
                "askSize": 1000,
                "volume": 3835526,
                "fiftyTwoWeekHigh": 149.78,
                "forwardPE": 22.6307,
                "fromCurrency": 213,
                "fiveYearAvgDividendYield": 2.86,
                "fiftyTwoWeekLow": 128.32,
                "bid": 148.81,
                "tradeable": False,
                "dividendYield": 0.028900001,
                "bidSize": 1300,
                "dayHigh": 149.78,
                "exchange": "NMS",
                "shortName": "Pepsico, Inc.",
                "longName": "PepsiCo, Inc.",
                "exchangeTimezoneName": "America/New_York",
                "exchangeTimezoneShortName": "EDT",
                "isEsgPopulated": False,
                "gmtOffSetMilliseconds": "-14400000",
                "quoteType": "EQUITY",
                "symbol": "PEP",
                "messageBoardId": "finmb_32854",
                "market": "us_market",
                "annualHoldingsTurnover": "full",
                "enterpriseToRevenue": 3.406,
                "beta3Year": None,
                "profitMargins": 0.10512,
                "enterpriseToEbitda": 18.852,
                "52WeekChange": 0.11710429,
                "morningStarRiskRating": None,
                "forwardEps": 6.58,
                "revenueQuarterlyGrowth": None,
                "sharesOutstanding": 1381629952,
                "fundInceptionDate": None,
                "annualReportExpenseRatio": None,
                "bookValue": 10.092,
                "sharesShort": 9873615,
                "sharesPercentSharesOut": 0.0070999996,
                "fundFamily": None,
                "lastFiscalYearEnd": 1608940800,
                "heldPercentInstitutions": 0.73147005,
                "netIncomeToCommon": 7496000000,
                "trailingEps": 5.402,
                "lastDividendValue": 1.075,
                "SandP52WeekChange": 0.36878085,
                "priceToBook": 14.755252,
                "heldPercentInsiders": 0.0014399999,
                "nextFiscalYearEnd": 1672012800,
                "mostRecentQuarter": 1616198400,
                "shortRatio": 2.08,
                "sharesShortPreviousMonthDate": 1620950400,
                "floatShares": 1379171960,
                "enterpriseValue": 242884706304,
                "threeYearAverageReturn": None,
                "lastSplitDate": 833328000,
                "lastSplitFactor": "2:1",
                "legalType": None,
                "lastDividendDate": 1622678400,
                "morningStarOverallRating": None,
                "earningsQuarterlyGrowth": 0.281,
                "dateShortInterest": 1623715200,
                "pegRatio": 2.64,
                "lastCapGain": None,
                "shortPercentOfFloat": 0.0072000003,
                "sharesShortPriorMonth": 10545263,
                "impliedSharesOutstanding": None,
                "category": None,
                "fiveYearAverageReturn": None,
                "regularMarketPrice": 148.91,
                "logo_url": "https://logo.clearbit.com/pepsico.com"
            }

            mocked = yfinance.Ticker("PEP").info
            mocked_keys = mocked.json().keys()
            logging.info("Called a mocked YFinance API, got a response")

        self.assertListEqual(list(actual_keys), list(mocked_keys))

        log_end("INTEGRATION CONTRACT WITH THE YAHOO API")