import os, sys, time, json

os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1" # per evitare warning in codedebug
os.environ['USER_AGENT'] = 'LegalAI Agent/0.1'

sys.path.append('./libs')

from langchain import hub
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# from langchain_community.llms import Ollama
# from langchain_community.embeddings import OllamaEmbeddings
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings


from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_chroma import Chroma

from langchain_core.messages import HumanMessage

from tools.sqlitedb import SqliteChatHistory
from tools.debug import Debug
import torch

## Envirnoment (Docker)
DEBUG          =os.environ.get('DEBUG', 'false').lower() in ['si','yes','on','1',"true"]
LLM_MODEL      =os.environ.get('LLM_MODEL', 'qwen2:1.5b')
OLLAMA_BASE_URL=os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
EMBED_MODEL    =os.environ.get('EMBED_MODEL', 'all-MiniLM-L6-v2')
##

collection_name="legalai"

dbg=Debug(DEBUG)

if dbg.on():
  print(f"""
  DEBUG_FLAG      = {DEBUG}
  LLM_MODEL       = {LLM_MODEL}
  OLLAMA_BASE_URL = {OLLAMA_BASE_URL}
  EMBED_MODEL     = {EMBED_MODEL}
  """)

llmModel=LLM_MODEL

llm = OllamaLLM(
  base_url=OLLAMA_BASE_URL,
  temperature=0,
  model=llmModel
)

# embeddings = OllamaEmbeddings(model=f"nomic-embed-text",base_url=OLLAMA_BASE_URL)
device  = 'cuda' if torch.cuda.is_available() else 'cpu'
print('Device:', device)

model_kwargs = {'device': device ,'trust_remote_code':True}
encode_kwargs = {'normalize_embeddings': True, 'clean_up_tokenization_spaces': True, 'weights_only': True}

embeddings = HuggingFaceEmbeddings(
    # model_name='BAAI/bge-base-en-v1.5',
    # model_name='all-MiniLM-L6-v2',
    model_name=EMBED_MODEL,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# ########################################################
# Chroma DB
# ########################################################
persist_dir='./db/'+embeddings.model_name.replace('/','-')
vectorstore = Chroma(
  collection_name=collection_name,
  persist_directory=persist_dir,
  embedding_function=embeddings,
  collection_metadata={"hnsw:space": "cosine"},
)
# rag=OllamaRAG(db=vectorstore,llm_model=llmModel,show_progress=True)

retriever = vectorstore.as_retriever()
prompt = hub.pull("rlm/rag-prompt")

# def format_docs(docs):
#     return "\n\n".join(doc.page_content for doc in docs)

# rag_chain = (
#     {"context": retriever | format_docs, "question": RunnablePassthrough()}
#     | prompt
#     | llm
#     | StrOutputParser()
# )

contextualize_q_system_prompt = """\
  Given a chat history and the latest user question\
  which might reference context in the chat history, formulate a standalone question\
  which can be understood without the chat history. Do NOT answer the question,\
  just reformulate it if needed and otherwise return it as is.\
"""
qa_system_prompt = """\
  You are an assistant for question-answering tasks.\
  Use the following pieces of retrieved context to answer the question.\
  If you don't know the answer, just say that you don't know.\
  Use three sentences maximum and keep the answer concise.\
  {context}\
"""
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

chat_history=SqliteChatHistory("db/data_rag_history.db")

func=lambda q,a:[HumanMessage(content=q), a]

def do_query(query:str, multiquery=None, sid='1-1-0'):
  tm_on=time.perf_counter()

  if len(query)>0:
    # answer=rag.query(query)
    stream_chat=True

    nquery={
      "input": query,
      "chat_history": chat_history.get_chat_history_list(sid,func)
    }

    dbg.print("******",nquery)

    response=''

    if stream_chat:
      dbg.print("stream_chat start")
      for chunk in rag_chain.stream(nquery):
        dbg.print(chunk)
        if token := chunk.get("answer"):
          response+=token
          tmpx=''.join(token)
          dbg.print(tmpx)
          js_chunk=json.dumps(chunk)
          yield f"{js_chunk}\n"

      counter=time.perf_counter()-tm_on
      stime='{"time": '+f'"{counter}"'+"}"
      dbg.print(stime)
      yield f'{stime}\n'

      # qui response contiene il testo della risposta
      answer=response
    else:
      response=rag_chain.invoke({
        "input": query,
        "chat_history": chat_history.get_chat_history_list(sid,func)
      })
      # qui response contiente un set
      answer=response['answer']

    chat_history.save_chat_history(sid,query,answer)
  else:
    answer='fai una domanda'

  counter=time.perf_counter()-tm_on

  dbg.print(answer)

  return {'answer':answer,
          'time': counter}



#### ###########
#### ######################################################################
#### ###########
if __name__ == '__main__':
  import tools.utils as tls

  pkg_list=[
    'bs4',
    # 'langchain-huggingface',
    'pandas'
    # 'requests',
    # 'flask',
    # 'langchain_community',
    # 'langchain_chroma'
  ]

  tls.pip_install(pkg_list)

  import bs4
  from langchain_community.document_loaders import WebBaseLoader
  from langchain.text_splitter import RecursiveCharacterTextSplitter
  # from langchain_huggingface import HuggingFaceEmbeddings



  permanent_dir = "./ChromaDBG"
  collection_name="chat_db"

  if not os.path.exists(permanent_dir):

    loader = WebBaseLoader(
      web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
      bs_kwargs=dict(
          parse_only=bs4.SoupStrainer(
              class_=("post-content", "post-title", "post-header")
          )
      ),
    )

    docs = loader.load()

    # document split
    text_splitter=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    # embfunc=SentenceTransformerEmbeddings(model_name="distiluse-base-multilingual-cased-v1")
    # tm_on=time.perf_counter()
    # embfunc=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # tok=len(embfunc.embed_query("Hello world"))
    # counter=time.perf_counter()-tm_on

    # print('huggingface',tok, counter) # 384 115.5 secs


    #### ollama
    tm_on=time.perf_counter()
    embfunc=embeddings = OllamaEmbeddings(model="nomic-embed-text")

    tok=len(embfunc.embed_query("Hello world"))
    counter=time.perf_counter()-tm_on

    print("ollama:",tok, counter) # 768 1.04 sec

    docs_splits=text_splitter.split_documents(docs)

    db= Chroma.from_documents(
      docs_splits,
      embfunc,
      persist_directory=permanent_dir,
      collection_metadata={"hnsw:space": "cosine"},
      collection_name=collection_name,
    )
  else:
    print('Permanent')

    embfunc=embeddings = OllamaEmbeddings(model="nomic-embed-text")

    db = Chroma(
        embedding_function=embfunc,
        persist_directory=permanent_dir,
        collection_metadata={"hnsw:space": "cosine"},
        collection_name=collection_name
    )

  llmModel="qwen2:1.5b" # quello che hai installato in ollama

  llm = OllamaLLM(
    base_url='http://localhost:11434',
    temperature=0.1,
    model=llmModel
  )
  retriever = db.as_retriever()
  prompt = hub.pull("rlm/rag-prompt")

  print(prompt)
  def format_docs(docs):
      return "\n\n".join(doc.page_content for doc in docs)

  rag_chain = (
      {"context": retriever | format_docs, "question": RunnablePassthrough()}
      | prompt
      | llm
      | StrOutputParser()
  )

  Q1="What is Task Decomposition?"
  Q2="What are common ways of doing it?"

  A1=rag_chain.invoke(Q1)

  print(A1)

  contextualize_q_system_prompt = """\
    Given a chat history and the latest user question\
    which might reference context in the chat history, formulate a standalone question\
    which can be understood without the chat history. Do NOT answer the question,\
    just reformulate it if needed and otherwise return it as is.\
  """
  contextualize_q_prompt = ChatPromptTemplate.from_messages(
      [
          ("system", contextualize_q_system_prompt),
          MessagesPlaceholder("chat_history"),
          ("human", "{input}"),
      ]
  )

  history_aware_retriever = create_history_aware_retriever(
      llm, retriever, contextualize_q_prompt
  )

  qa_system_prompt = """\
    You are an assistant for question-answering tasks.\
    Use the following pieces of retrieved context to answer the question.\
    If you don't know the answer, just say that you don't know.\
    Use three sentences maximum and keep the answer concise.\
    {context}\
  """
  qa_prompt = ChatPromptTemplate.from_messages(
      [
          ("system", qa_system_prompt),
          MessagesPlaceholder("chat_history"),
          ("human", "{input}"),
      ]
  )

  question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

  rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

  chat_history=SqliteChatHistory("data_rag_history.db")
  sid='1-1-0'
  func=lambda q,a:[HumanMessage(content=q), a]

  ai_msg_1 = rag_chain.invoke({
    "input": Q1,
    "chat_history": chat_history.get_chat_history_list(sid,func)
  })

  chat_history.save_chat_history(sid,Q1,ai_msg_1['answer'])

  print("R1",ai_msg_1['answer'])

  ai_msg_2 = rag_chain.invoke({
    "input": Q2,
    "chat_history": chat_history.get_chat_history_list(sid,func)
  })

  chat_history.save_chat_history(sid,Q2,ai_msg_2['answer'])

  print("R2",ai_msg_2['answer'])
