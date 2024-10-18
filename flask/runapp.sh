#!/bin/bash

echo activating environment...
if [ ! -d ".venv/bin" ]; then
  echo "Python virtual env does not exist. creating ..."
  python3 -m venv --prompt LegaAI .venv
fi

export PATH=".venv/bin:$PATH"

## extra modules
pip install requests

echo running app
export FLASK_APP=flask_server
export FLASK_ENV=development
# export FLASK_RUN_PORT=8000
# export FLASK_RUN_HOST="0.0.0.0"

python $FLASK_APP.py &
streamlit run streamlit_client.py

# python hello.py

if [ ! -z "${SLEEP}" ]; then
  echo 'sleeping time time...'
  sleep $SLEEP
fi

