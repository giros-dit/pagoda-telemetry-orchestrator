#!/bin/sh

set -e

# activate our virtual environment here
. /venv/bin/activate

exec uvicorn process_manager.main:app --host 0.0.0.0 \
     --port 8080 --reload \
     --log-config process_manager/config/log.yaml
