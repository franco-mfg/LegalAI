FROM debian:stable-slim

WORKDIR /legalai


# requirements.txt requirements.txt
# build-base cmake
RUN SYS_MODULES="sqlite3 python3 python3-pip python3-venv" \
&& apt-get update -y \
&& apt-get -y upgrade \
&& DEBIAN_FRONTEND=noninteractive apt-get -y install $SYS_MODULES \
&& rm -rf /var/lib/apt/lists/*
# && apk add --no-cache $SYS_MODULES \
# && mkdir legalai \
# && cd legalai \
RUN python3 -m venv --prompt LegaAI .venv \
&& . .venv/bin/activate \
&& pip install streamlit

COPY client/ ./
RUN ls -la
# RUN mv streamlit .streamlit

ENV PATH="/legalai/.venv/bin:$PATH"

EXPOSE 8501

# ENTRYPOINT [ "sh" ]

CMD [ "streamlit","run","streamlit_client.py" ]

# ENTRYPOINT [ source .venv/bin/activate python hello.py ]