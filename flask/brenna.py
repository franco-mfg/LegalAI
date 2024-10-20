import streamlit as st
import os
import requests, json
# Titre de l'application

LEGALAI_SERVER_URL=os.environ.get('LEGALAI_SERVER_URL', 'http://localhost:5000')

st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>LEGAL_AI Chatbot 🏛️</h1>", unsafe_allow_html=True)

# Affichage de l'image à droite
image_path = os.path.join("/home/brenna/liandi/image", "lagal.jpg")
if os.path.exists(image_path):
    st.sidebar.image(image_path, caption=" ", use_column_width=True)

st.sidebar.write("Benvenuta da LEGAL_AI! Poni le tue domande legali tramite PDF e il database.")

# Sélection du modèle Ollama
model_options = ["llama3", "llama3.1"]
chosen_model = st.sidebar.selectbox("Seleziona un modello Ollama", model_options)

# Sélection d'emoji utilisateur
suggestions = ["🫡", "👤", "🙂", "🧑‍⚖️"]
emoji_utilisateur = st.sidebar.radio("scegli la tua emoji :", suggestions, index=1)
bot_emoji = "🤖"

# Initialisation de l'état de session
if 'historique' not in st.session_state:
    st.session_state['historique'] = []  # Historique des questions et réponses
if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""
if 'pdf_segments' not in st.session_state:
    st.session_state['pdf_segments'] = []  # Pour stocker les segments du PDF
if 'index_faiss' not in st.session_state:
    st.session_state['index_faiss'] = None  # Pour stocker l'index FAISS

# Gestion des PDF
def extract_text_from_pdf(uploaded_file):
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        return ''.join([page.extract_text() for page in reader.pages])
    except:
        return ""

# Chargement du modèle d'embedding
@st.cache_resource
def charger_modeles():
    #embedding_model = SentenceTransformer('all-mpnet-base-v2')
    return "*"

embedding_model = charger_modeles()

# Chargement des fichiers PDF dans la barre latérale
st.sidebar.header("📄 caricamento del file")
uploaded_file = st.sidebar.file_uploader("Scarica un pdf", type="pdf")

pdf_text = None
if uploaded_file:
    pdf_text = extract_text_from_pdf(uploaded_file)
    st.sidebar.success("PDF caricato con successo!")

    # Découper le texte en segments
    segments = [pdf_text[i:i+1000] for i in range(0, len(pdf_text), 800)]  # Découpage en segments avec chevauchement
    st.session_state['pdf_segments'] = segments

    # Créer l'index FAISS
    embeddings = embedding_model.encode(segments)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings))
    st.session_state['index_faiss'] = index

    st.sidebar.write(f"PDF indexé avec {len(segments)} segments.")

# Fonction de recherche dans l'index FAISS
def recherche_faiss(question, index, segments, top_k=3):
    #question_embedding = embedding_model.encode([question])
    d#istances, indices = index.search(np.array(question_embedding), top_k)
    return "*"

# Nouvelle fonction de génération de réponse avec Ollama
def generate_response_ollama(model_name, context, question):
    try:
        # Combiner le contexte du PDF avec la question utilisateur
        full_prompt = f"Contexte:\n{context}\n\nQuestion: {question}"
        
        # Utiliser Ollama pour générer une réponse
        response = ollama.chat(model=model_name, messages=[{"role": "user", "content": full_prompt}])
        return response['message']['content']
    except Exception as e:
        return f"Erreur lors de la génération de la réponse : {e}"

# Fonction de génération de réponse complète en utilisant FAISS pour le PDF et Ollama pour la génération de texte
def generate_response_with_faiss_and_ollama(model_name, question, index_faiss, pdf_segments):
    if index_faiss is not None and pdf_segments:
        # Rechercher les segments pertinents dans l'index FAISS
        relevant_segments = recherche_faiss(question, index_faiss, pdf_segments)
        context = " ".join(relevant_segments)

        # Générer la réponse en combinant le contexte et la question
        return generate_response_ollama(model_name, context, question)
    else:
        # Si aucun PDF n'est chargé, générer une réponse simple avec Ollama
        return generate_response_ollama(model_name, "", question)
    
def stream_server_data(prompt, sid):
  req=requests.get(f"{LEGALAI_SERVER_URL}/api?query={prompt}&sid={sid}", stream=True)
  if req.status_code==200:
    for line in req.iter_lines():
        if line:
          jsData=json.loads(line)
          dataLine=''
          for key in jsData:
            match key:
              case 'answer':
                dataLine+=dataLine+jsData[key]
              case 'time':
                tm=jsData[key]
                #dbg.print(type(tm),tm)
                # dbg.print('time '+f"\n\n*query in: {float(tm):.02f}sec*")
                dataLine+=dataLine+f"\n\n*query in: {float(tm):.02f}sec*"
                # dbg.print("dataline:",dataLine)
          yield dataLine # str(dataLine,'utf-8')
          
# Fonction de callback pour envoyer un message
def envoyer_message():
    if st.session_state['user_input']:
        # Générer la réponse en combinant les données du PDF et Ollama
        # response = generate_response_with_faiss_and_ollama(
        #     chosen_model,
        #     st.session_state['user_input'],
        #     st.session_state['index_faiss'],
        #     st.session_state['pdf_segments']
        # )
        response = st.write_stream(stream_server_data(st.session_state['user_input'], 'brenna'))
        
        # Ajouter la question et la réponse à l'historique
        st.session_state['historique'].append({
            "question": st.session_state['user_input'],
            "reponse": response
        })

        # Vider le champ de saisie
        st.session_state['user_input'] = ""
        #st.experimental_rerun()

# Affichage de l'historique des échanges à gauche
st.sidebar.subheader("📝 Storia delle domande")
if st.session_state['historique']:
    for entry in st.session_state['historique']:
        st.sidebar.markdown(f"**{emoji_utilisateur} Vous :** {entry['question']}")

# Affichage des échanges complets
st.subheader("💬 I tuoi scambi")
if st.session_state['historique']:
    for entry in st.session_state['historique']:
        st.markdown(f"""
        <div style='background-color: #e0f7fa; padding: 10px; border-radius: 10px; margin-bottom: 10px;'>
            <strong>{emoji_utilisateur} </strong> {entry['question']}
        </div>
        <div style='background-color: #ffffff; padding: 10px; border-radius: 10px; margin-bottom: 10px;'>
            <strong>{bot_emoji} </strong> {entry['reponse']}
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("Al momento non ci sono cambi. Fai la tua prima domanda!")

# Champ de saisie avec bouton pour envoyer le message
col1, col2 = st.columns([5, 1])
with col1:
    st.text_input("Scrivi qui il tuo messaggio...", key='user_input', on_change=envoyer_message)
with col2:
    if st.button("🎤"):
        st.info("Il microfono è attivato per catturare la voce.")

# Bouton pour supprimer l'historique
if st.sidebar.button("Elimina la cronologia"):
    st.session_state['historique'] = []
    st.experimental_rerun()

# Image de fin
image_fin_path = os.path.join("/home/brenna/liandi/image", "fin.jpg")
if os.path.exists(image_fin_path):
    st.sidebar.image(image_fin_path, caption=" ", use_column_width=True)

