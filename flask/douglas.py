# -*- coding: utf-8 -*-
"""Integrar.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1iTlQSag_9rcQrA3g4KYEef3DP0Dihwj7
"""
import os, sys, json

sys.path.append('./libs')

import tools.utils  as utils
from tools.debug  import Debug

## Envirnoment (Docker)
DEBUG          =os.environ.get('DEBUG', 'false').lower() in ['si','yes','on','1',"true"]
LLM_MODEL      =os.environ.get('LLM_MODEL', 'qwen2:1.5b')
OLLAMA_BASE_URL=os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
EMBED_MODEL    =os.environ.get('EMBED_MODEL', 'all-MiniLM-L6-v2')
##

dbg=Debug(DEBUG, __file__)

pkg_list=[
    "chromadb",
    "langchain",
    "pyngrok",
    "lark",
    "streamlit",
    "optimum",
    "transformers",
    "huggingface_hub",
    "sentence-transformers",
    "langchain-huggingface",
    "langchain-community",
    "langchain-chroma",
    "langchain-text-splitters",
    "langchain-ollama"
]

utils.pip_install(pkg_list)
print("Integrar...")

import re
# import spacy
from collections import defaultdict
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
# from langchain.embeddings import HuggingFaceEmbeddings
from langchain.retrievers.self_query.base import AttributeInfo
from langchain.retrievers import SelfQueryRetriever
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain.schema import Document
# from langchain.document_loaders import TextLoader
from langchain_community.document_loaders import TextLoader
from langchain_core.runnables import RunnablePassthrough
import lark
from langchain.retrievers.self_query.base import AttributeInfo
from langchain.retrievers import SelfQueryRetriever
from langchain.prompts import PromptTemplate
from langchain.retrievers.self_query.base import AttributeInfo
from langchain.retrievers import SelfQueryRetriever
from langchain.prompts import PromptTemplate
# from langchain_community.chat_models import ChatOllama
from langchain_ollama import OllamaLLM, OllamaEmbeddings, ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings

# Dividir os documentos em chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=20,
    separators=["\n\n", "\n", " ", ".", ",", ""]
)

llm = ChatOllama(model=LLM_MODEL, temperature=0, base_url=OLLAMA_BASE_URL)

embedding_model = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

persist_directory = './db/'+embedding_model.model_name.replace('/','-')

db_2 = Chroma(embedding_function=embedding_model, persist_directory=persist_directory,
                collection_name='legalai',
                collection_metadata={"hnsw:space": "cosine"})

# testing db_2
data=db_2.get(limit=5,include=["metadatas", "documents"])
dbg.print('test db')
# for rec in data:
#     dbg.print(rec.metadata)

# Metadados e atributos sugeridos
metadata_field_info = [
    AttributeInfo(name="source", description="Celex ID", type="string"),
    AttributeInfo(name="labels", description="Argomenti dei documenti", type="string"),
    AttributeInfo(name="number", description="Numero del Regolamento o Direttiva", type="string")

]

# Conteúdo dos documentos que será utilizado pelo SelfQueryRetriever
document_contents = "Testo del Regolamento o Diretiva"  # Nome do campo que contém o texto dos documentos

# Prompt para perguntas e contexto
prompt_template = """
<|system|>

Sei un assistente IA specializzato in Leggi, Regolamenti, Decreti e questioni legali. Utilizza SOLO il database (db_2) fornito come contesto per rispondere alle domande.
Se la risposta non è esplicitamente presente nel database, informa che non è possibile rispondere.

{context}

Indica le fonti trovate nel database vettoriale utilizzate per generare le risposte.
</s>
<|user|>{question}</s>
<|assistant|>
"""
prompt = PromptTemplate(input_variables=["context", "question"], template=prompt_template)

# Criar o SelfQueryRetriever
self_query_retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=db_2,  # Usando a base vetorial Chroma criada anteriormente
    document_contents=document_contents,
    metadata_field_info=metadata_field_info,
    retriever=db_2.as_retriever(),  # Usando a função de recuperação da base Chroma
    verbose=True
)
# Função para realizar consulta
def query_documents(question):
    retrieved_docs = self_query_retriever.get_relevant_documents(question)

    for doc in retrieved_docs:
        print(f"Pagina: {doc.metadata.get('page', 'sconosciuta')}, Contenuto: {doc.page_content[:200]}...\n")

    return retrieved_docs


# Pipeline de consulta
chain = {"context": self_query_retriever, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser()


import time

# Função para realizar consulta
def do_query(query: str, multiquery=None, sid='1-1-0'):
    tm_on = time.perf_counter()
    dbg.print("*** Query:", query)
    stream_model = True
    response = ''

    if stream_model:
        print("***** Stream")
        for item in chain.stream(query):
            response = response + item
            dbg.print(item)
            dj={"answer":item}
            js=json.dumps(dj)
            # dbg.print(dj,js)
            yield(f"{js}\n")

        counter=time.perf_counter()-tm_on
        stime='{"time": '+f'"{counter}"'+"}"
        yield f'{stime}\n'
    else:
        response = chain.invoke(query)

    counter = time.perf_counter() - tm_on

    return {'answer': response, 'time': counter}

# Função para consulta dos documentos
def query_documents(query: str):
    # Simulação de uma consulta ao banco de dados de documentos
    documents = [
        {"id": "2015/41", "title": "DECISIONE (UE) 2015/41 DEL PARLAMENTO EUROPEO",
         "content": "DECISIONE (UE) 2015/41 DEL PARLAMENTO EUROPEO E DEL CONSIGLIO del 17 dicembre 2014..."}
    ]

    # Filtrar documentos relevantes com base na query
    relevant_docs = [doc for doc in documents if query in doc['title']]

    return relevant_docs

# Função para separar metadados e conteúdo
def process_response(response):
    if 'Document' in response:
        metadata_start = response.find("Document(metadata=")
        metadata_end = response.find("page_content=")

        metadata = response[metadata_start:metadata_end].strip()
        content_start = response.find('page_content="') + len('page_content="')
        content_end = response.find('")', content_start)

        page_content = response[content_start:content_end].replace("\\n", "\n")

        return page_content, metadata
    else:
        return response, None

if __name__ == '__main__':
    user_input = input("Digite sua pergunta: ")

    # Faz a consulta nos documentos
    response_docs = query_documents(user_input)

    # Obtém a resposta completa
    for dato in do_query(user_input):
        # raw_response = do_query(user_input)
        raw_response = dato
        # print(dato)

    # Processa a resposta para separar o conteúdo do metadado
    resposta_texto, metadados = process_response(raw_response['answer'])

    # Exibe a resposta em texto e os metadados separados
    print(f"\nDomanda: {user_input}\n")
    print(f"Resposta (Testo): {resposta_texto}")

    if metadados:
        print(f"\nMetadados:\n{metadados}")
