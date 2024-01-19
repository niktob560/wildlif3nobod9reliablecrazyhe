#!/bin/bash
nohup ./apigateway.sh &
nohup ./bonus_service.sh &
nohup ./flight_service.sh &
nohup ./ticket_service.sh &
