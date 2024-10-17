# qwen2:1.5B
# rag class
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from langchain.retrievers.multi_query import MultiQueryRetriever

class OllamaRAG:
  def __init__(self,
               db:Chroma,
               llm_model="phi3:mini",
               format_docs=None,
               json=False,
               multiquery=False,
               show_progress=False,
               base_url="http://localhost:11434"):

    self.db=db

    if(json):
      self.llm=ChatOllama(model=llm_model, base_url=base_url ,format="json")
    else:
      self.llm=ChatOllama(model=llm_model, base_url=base_url)

    self.db.embeddings.show_progress=show_progress

    if format_docs is None:
      self.format_docs=lambda docs: "\n\n".join(doc.page_content for doc in docs)
    else:
      self.format_docs=format_docs

    self.prompt = None
    self.multi_prompt=None
    self.history_prompt=None

    self.set_prompt()
    self.set_multiprompt()
    # self.set_history_prompt()
    self.set_multiquery(multiquery)


  def set_multiquery(self,multiquery:bool):
    if multiquery:
      self.retriever=MultiQueryRetriever.from_llm(
        retriever=self.db.as_retriever(),
        llm=self.llm,
        prompt=self.multi_prompt
      )
    else:
      self.retriever=self.db.as_retriever()

  def get_chain(self):
    chain=(
      {
        "context": self.retriever | self.format_docs,
        "question": RunnablePassthrough()
      } |
      self.prompt |
      self.llm |
      StrOutputParser()
    )
    return chain

  def query(self,query:str):
    # chain= (
    #   {"context": self.retriever | self.format_docs,
    #   "question": RunnablePassthrough()
    #   } |
    #   self.prompt |
    #   self.llm |
    #   StrOutputParser()
    # )
    chain=self.get_chain()

    return chain.invoke({"question": query})

  def set_prompt(self,prompt:str=None):
    if prompt is None:
      prompt="""
      1. Use the following pieces of context to answer the question at the end.
      2. If you don't know the answer, just say that "I don't know" but don't make up an answer on your own.\n
      3. Keep the answer crisp and limited to 3,4 sentences.
      Context: {context}
      Question: {question}
      Helpful Answer:
      """
    self.prompt=ChatPromptTemplate.from_template(prompt)

  def set_multiprompt(self,prompt:str=None):
    if prompt is None:
      prompt="""
        You're an AI language model assistant. Your task is to generate five
        different versions of the user query provided to retrieve relevant documents from
        a vector database. By generating multiple perspectives on the user's question, your
        goal is to help the user overcome some of the limitations of search for similarity.
        Provide these alternate questions separated by new lines.
        Original questions : {question}
      """
    self.multi_prompt=PromptTemplate(input_variables=["question"],template=prompt)

    def set_history_prompt(self,prompt:str=None):
      if prompt is None:
        prompt="""
          Given a chat history and the latest user question
          which might reference context in the chat history,
          formulate a standalone question which can be understood
          without the chat history. Do NOT answer the question,
          just reformulate it if needed and otherwise return it as is.
        """
      self.history_prompt=ChatPromptTemplate.from_messages(
          [
              ("system", prompt),
              MessagesPlaceholder("chat_history"),
              ("human", "{question}"),
          ]
      )

  def set_chain(self,chain):
    self.chain=chain