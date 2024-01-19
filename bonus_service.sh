#!/bin/bash
cd src/bonus_service
poetry update
uvicorn main:app --port 8080