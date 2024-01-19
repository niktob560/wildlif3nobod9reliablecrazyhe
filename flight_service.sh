#!/bin/bash
cd src/flight_service
poetry update
uvicorn main:app --port 8060