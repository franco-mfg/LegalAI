# https://blog.stoplight.io/python-rest-api

import os
import sys, requests, signal

sys.path.append('./libs')

import tools.utils as tls
from   tools.debug import Debug

pkg_list=[
  'requests',
  'flask',
  'langchain_community',
  'langchain_chroma',
  "langchain-huggingface",
  'sentence-transformers',
  "langchain-ollama",
  "pandas",
  'streamlit'
]

if tls.pip_install(pkg_list)>0:
  tls.pip_save_requirements(pkg_list)

import flask
from flask import request, jsonify, send_file
# from rag_history import do_query

from douglas import do_query # liandi

app = flask.Flask(__name__)

DEBUG = os.environ.get('DEBUG', 'false').lower() in ['si','yes','on','1',"true"]
OLLAMA_BASE_URL=os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

dbg = Debug(DEBUG)

def docker_send_stop(sig, frame):
    dbg.print("OK docker stopped server")
    os.kill(os.getpid(), signal.SIGTERM)
    ## app.close()

# per uscire da docker senza errore 137
signal.signal(signal.SIGTERM, docker_send_stop)
dbg.print("*** Setting signal")

@app.route('/')
def home():
    dbg.print(f'getting...file')
    return send_file('index.html', mimetype='text/html')

@app.route('/api', methods=['GET','POST'])
def query():
    """
        Gestisce richieste GET e POST all'endpoint /query.
    """
    query_params = request.args.to_dict()
    if request.method == 'GET':
        # query_params = request.args.to_dict()
        query=request.args.get("query",None)
        multi=request.args.get("multi",None)
        sid  =request.args.get("sid",None)
        dbg.print(f'q={query}')

        if sid is None:
            response={'answer':'You are not logged in','time': 0}
        else:
            if(query!=None):
                # response=do_query(query, multi in ['si','yes','on','1'], sid=sid)
                # https://flask.palletsprojects.com/en/2.1.x/patterns/streaming/
                # app.response_class(generate(), mimetype='text/csv')
                return app.response_class(
                     do_query(query, multi in ['si','yes','on','1'], sid=sid),
                     mimetype='text/plain'
                )
            else:
                response={'answer':'no query. Please ask something!'}

        dbg.print(response)

        return jsonify(response)

    elif request.method == 'POST':
        data = request.get_json()
        return jsonify(data)
    else:
        return jsonify({'error': 'Metodo HTTP non supportato'}), 405


@app.route('/info', methods=['GET'])
def info():
    """Handles GET requests to the /info endpoint.

    Returns:
        JSON response containing information about the server.
    """

    dbg.print(f'OLLAMA------> {OLLAMA_BASE_URL}')

    req=requests.get(f"{OLLAMA_BASE_URL}/api/version")

    info = {
        'server_name': 'My Flask Server',
        'version': f'1.0.1, {req.content}',
        'description': 'A simple API server for querying and retrieving information.',
        # 'db': vectorstore.get(limit=1)
    }
    return jsonify(info)

if __name__ == '__main__':
    app.run(debug=DEBUG, host="0.0.0.0")