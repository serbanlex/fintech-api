from fastapi import FastAPI, requests
import random
import string
import time
import logging
from routers import portfolio, ticker_info, graphs

app = FastAPI(title="Syneto Labs Project - Fintech Time Machine", version="0.1")


# setting the routers for portfolio operations, various ticker info and graphs
app.include_router(portfolio.router)
app.include_router(ticker_info.router)
app.include_router(graphs.router)


# setup logger
logging.basicConfig(filename='../resources/logger.txt', level=logging.INFO,
                    format='%(asctime)s | %(levelname)s: %(message)s ',
                    datefmt='%d/%m/%Y %I:%M:%S %p')


# middleware that runs for every request (command) that comes
@app.middleware("http")
async def log_requests(request: requests.Request, call_next):
    # generating a random unique ID, so we can trace which logs come from the same requests
    request_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    logging.info(f"Request ID = {request_id} came, start path: {request.url.path}, method: {request.method}, "
                 f"parameters: {request.query_params}")

    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000

    # fomat the process time so it has 2 decimals
    formatted_process_time = '{0:.2f}'.format(process_time)

    logging.info(f"Request ID = {request_id} got its response. Completed in {formatted_process_time}ms, "
                 f"status_code = {response.status_code}\n")

    return response
