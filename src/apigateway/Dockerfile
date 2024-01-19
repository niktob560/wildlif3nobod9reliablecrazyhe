FROM python:alpine3.16

# Creating Application Source Code Directory
RUN mkdir -p /app/src

# Setting Home Directory for containers
WORKDIR /app/src

RUN apk update && apk add --no-cache libpq-dev
RUN apk add build-base

RUN apk add --no-cache git openssh

# Installing python dependencies
COPY requirements.txt /app/src
RUN pip install --no-cache-dir -r requirements.txt

# Copying src code to Container
COPY . /app/src

# Application Environment variables
ENV APP_ENV development

# Exposing Ports
EXPOSE 8080

# Setting Persistent data
VOLUME ["/app-data"]

# Running Python Application
CMD ["python", "/app/src/main.py"]
