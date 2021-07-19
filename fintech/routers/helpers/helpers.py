import logging
import re
from datetime import date
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi import HTTPException
import yfinance
from matplotlib import pyplot
import yagmail
from dotenv import dotenv_values


# class that holds functions related to the input file: reading, adding, checking if a ticker is saved,
# creating an yfinance object with prior check as it is very used in endpoints
class Input:
    def __init__(self, file_source):
        self.source = file_source
        self.lines = []

    # read the portfolio file, storing the lines
    def read(self):
        try:
            with open(self.source, "r") as tickers_file:
                # get all of the file's lines
                self.lines = tickers_file.readlines()

                # give info to lhe logger
                logging.info(f"Did read from file: {self.source}")

        except FileNotFoundError:
            logging.error(f"Input file {self.source} does not exist.")
            raise HTTPException(status_code=404, detail="No portfolio input found.")

    # adding a new ticker, with existence check
    def add(self, ticker: str) -> JSONResponse:
        with open(self.source, "a+", encoding='utf-8') as tickers_file:
            # set the file pointer to the beginning, so we can check existing elements
            tickers_file.seek(0)

            self.lines = tickers_file.readlines()

            # see if the ticker already exists
            if self.check_ticker(ticker):
                logging.warning(f"Add of ticker {ticker} denied, already exists in {self.source}")
                return JSONResponse(status_code=400, content="Ticker already exists.")

            tickers_file.write(f"{ticker}\n")

        logging.info(f"Added {ticker} ticker to {self.source}")

        return JSONResponse(content="Ticker added successfully!")

    # delete an existent portfolio ticker
    def delete(self, ticker):
        deleted_something = False

        # read the and make sure everything is okay
        self.read()

        # iter through the lines list and write the ones that aren't the one we want to delete
        with open(self.source, "w") as tickers_file:
            for line in self.lines:
                if line.rstrip() != ticker:
                    tickers_file.write(line)
                else:
                    # mark that we deleted it
                    deleted_something = True

        if deleted_something:
            logging.info(f"Deleted ticker {ticker} successfully.")
            return JSONResponse(status_code=200, content="Ticker deleted")
        else:
            logging.info(f"Deletion of ticker {ticker} unsuccessful. Ticker not found. Nothing changed.")
            return JSONResponse(status_code=404, content="Ticker not found in file. ")

    # method for checking if a ticker exists, returns true/false
    def check_ticker(self, ticker: str):
        self.read()

        for line in self.lines:
            if line.rstrip() == ticker:
                logging.info(f"Checked ticker {ticker}. It is part of the portfolio.")
                return True

        logging.info(f"Checked ticker {ticker}. Not part of the portfolio.")
        return False

    # returns a YFinance Ticker Object, checks if it is saved too
    def ticker_object(self, ticker: str) -> yfinance.ticker.Ticker:
        ticker = ticker.upper()

        if self.check_ticker(ticker) is False:
            logging.error(f"Ticker {ticker} not found in {self.source}. Could not check attributes.")
            raise HTTPException(status_code=404, detail="Ticker not found. Please save it into the portfolio before "
                                                        "querying it.")

        ticker_object = yfinance.Ticker(ticker)

        return ticker_object


# can download historical details about one or more tickers between two dates
class TickerHistory:
    def __init__(self, ticker_list, start_date, end_date):
        self.ticker_list = ticker_list
        self.start_date = start_date
        self.end_date = end_date
        self.history_details = yfinance.download(self.ticker_list, start=start_date, end=end_date)

    # We need to validate the date types (dates strings may not be suitable/in good order).
    # Doing that with the constructor.

    @property
    def start_date(self):
        return self._start_date

    @start_date.setter
    def start_date(self, first_date):
        try:
            self._start_date = date.fromisoformat(first_date)
        except ValueError as e:
            logging.error(str(e))
            raise HTTPException(status_code=400, detail=str(e))

    @property
    def end_date(self):
        return self._end_date

    @end_date.setter
    def end_date(self, second_date):
        try:
            self._end_date = date.fromisoformat(second_date)
        except ValueError as e:
            logging.error(str(e))
            raise HTTPException(status_code=400, detail=str(e))

        if self.end_date < self.start_date:
            error = "Invalid input - start date cannot be after end date."
            logging.error(error)
            raise HTTPException(status_code=400, detail=error)

    pass

    def number_of_tickers(self):
        return len(self.ticker_list)

    def graph(self, graph_name_tickers: str):
        history = self.history_details

        close = history["Close"]

        figure, axis = pyplot.subplots(figsize=(16, 9))

        axis.plot(close.index, close, marker='.', mew='1')

        # string that concatenates the ticker list so we can show them off nicely in the title
        tickers_string = " ".join(self.ticker_list)

        pyplot.title(f"{tickers_string} history between {self.start_date} and {self.end_date}")
        pyplot.xlabel("Date")
        pyplot.ylabel("Close index")
        pyplot.grid()

        graph_name = f"../resources/graphs/{graph_name_tickers}_history_{self.start_date}_{self.end_date}.png"

        # list of tickers contains more than one ticker
        if self.number_of_tickers() > 1:
            axis.legend(close.columns.values, loc="upper right")

        # only one ticker in the list, can't query close.columns so we're using the tickers string as it's suitable
        else:
            axis.legend([tickers_string], loc="upper right")

        pyplot.savefig(graph_name)

        logging.info(f"Saved new plot for tickers: {self.ticker_list}. Path: {graph_name}")
        return FileResponse(graph_name, media_type="image/png")


class EmailSender:
    # private attributes
    __config = dotenv_values("../bin/.env") # ../bin/.env
    __sender_mail = __config["MAIL"]
    __sender_password = __config["PASS"]

    def __init__(self, to, subject, body, img):
        self.receiver = to
        self.subject = subject
        self.body = body
        self.img = img

    @property
    def receiver(self):
        return self._receiver

    @receiver.setter
    def receiver(self, email):
        regex = "(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if re.search(regex, email):
            self._receiver = email
        else:
            logging.error(f"Email of receiver, {email}, is invalid. Send failed.")
            raise HTTPException(status_code=400, detail="Invalid receiver mail given!")

    def send_mail(self):
        yag = yagmail.SMTP(self.__sender_mail, self.__sender_password)

        logging.info(f"An email with the plot has been sent to {self.receiver}.")

        yag.send(to=self.receiver, subject=self.subject, contents=[self.body, self.img])
