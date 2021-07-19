FROM ubuntu:20.04

RUN apt-get update -y
RUN apt-get install curl python3.9 python3-distutils bash -y
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -

RUN mkdir -p /home/time_machine

WORKDIR /home/time_machine

COPY ./pyproject.toml ./pyproject.toml

RUN /root/.poetry/bin/poetry install

EXPOSE 8000