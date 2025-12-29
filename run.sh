#!/bin/bash
# Activate virtual environment and run the monitor

source venv/bin/activate
python -m src.main "$@"
