#!bin/sh

# Load environments
export $(cat .env | xargs);

# Start 2D Server
poetry run start;