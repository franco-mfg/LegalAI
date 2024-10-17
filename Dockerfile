# FROM python:alpine
FROM ollama/ollama

WORKDIR /legalai


# requirements.txt requirements.txt

RUN SYS_MODULES="sqlite3 python3 virtualenv python3-venv" \
&& apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y $BUILDBase $SYS_MODULES
# && mkdir legalai \
# && cd legalai \
# RUN python3 -m venv --prompt LegaAI venv

# RUN bash source venv/bin/activate \
# && pip install flask
# -r requirements.txt

COPY flask/* ./

ENTRYPOINT [ "/usr/bin/bash" ]
CMD [ "runapp.sh" ]

# ENTRYPOINT [ source .venv/bin/activate python hello.py ]