#!/bin/bash
# Azure App Service startup script
cd /home/site/wwwroot
pip install -r requirements.txt
gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --timeout 120
