#!/bin/bash
cd src/apigateway
source venv/bin/activate
pip install -r requirements.txt
python ./main.py
