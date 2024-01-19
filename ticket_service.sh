#!/bin/bash
cd src/ticket_service
poetry update
uvicorn main:app --port 8070