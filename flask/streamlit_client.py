import streamlit as st
# import ptvsd
import requests, os, platform, zlib, json, sys
# import simplejson as json
from streamlit.runtime.scriptrunner import get_script_run_ctx

sys.path.append('./libs')

import tools.utils  as utils
from tools.debug import Debug

## Envirnoment (Docker)
DEBUG          =os.environ.get('DEBUG', 'false').lower() in ['si','yes','on','1',"true"]
LEGALAI_URL=os.environ.get('LEGALAI_URL', 'http://legalai:5000')
##

dbg=Debug(DEBUG)

# proviamo ad installare streamlit
utils.pip_install('streamlit')

def stream_server_data(prompt, sid):
  req=requests.get(f"http://{LEGALAI_URL}/api?query={prompt}&sid={sid}", stream=True)
  if req.status_code==200:
    for line in req.iter_lines():
        if line:
          dbg.print(type(line), line)
          dbg.print('qui')
          jsData=json.loads(line)
          dbg.print('qua')
          dataLine=''
          for key in jsData:
            dbg.print('Key',key)
            match key:
              case 'answer':
                dataLine+=dataLine+jsData[key]
              case 'time':
                tm=jsData[key]
                dbg.print(type(tm),tm)
                dbg.print('time '+f"\n\n*query in: {float(tm):.02f}sec*")
                dataLine+=dataLine+f"\n\n*query in: {float(tm):.02f}sec*"
                dbg.print("dataline:",dataLine)
          yield dataLine # str(dataLine,'utf-8')

def main():
  ctx = get_script_run_ctx()

  st.title('Ollama test')

  dbg.print('ISID',ctx.session_id)

  if 'SID' not in st.session_state:
    st.session_state['SID']=ctx.session_id
  else:
    dbg.print(' SID',st.session_state.SID)

  s_id=st.session_state.SID

  st.subheader("Ollama Chat", divider="green", anchor=False)

  message_container = st.container(height=500, border=True)

  if "messages" not in st.session_state:
    st.session_state.messages = []

  for message in st.session_state.messages:
    print('',end='.')
    avatar = "🤖" if message["role"] == "assistant" else "😎"
    with message_container.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

  print('')

  if prompt := st.chat_input("Enter a prompt here..."):
    try:
      st.session_state.messages.append(
        {"role": "user", "content": prompt}
      )

      message_container.chat_message("user", avatar="😎").markdown(prompt)

      response=''
      with message_container.chat_message("assistant", avatar="🤖"):
         response = st.write_stream(stream_server_data(prompt, s_id))
         dbg.print(f"...{response}")
      print(response)

      st.session_state.messages.append(
        {"role": "assistant", "content": response}
      )
    except Exception as e:
      st.error(e, icon="⛔️")



st.set_page_config(
    page_title="Chat LLM",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

if __name__ == "__main__":
    # ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
    # ptvsd.wait_for_attach()
    # __DEBUG__=False
    main()
