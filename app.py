import base64
import streamlit as st
from mistralai.client import Mistral

st.set_page_config(page_title="Le Prof perso d'Edgar", page_icon="🤖")

# --- PROTECTION PAR MOT DE PASSE ---
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

if not st.session_state.password_correct:
    st.title("🔒 Accès restreint - Le Prof perso d'Edgar")
    pwd_input = st.text_input("Entre ton mot de passe pour accéder à ton Prof :", type="password")
    if st.button("Valider"):
        # Récupère le mot de passe depuis les secrets Streamlit (ou utilise "edgar2026" par défaut)
        correct_password = st.secrets.get("APP_PASSWORD")
        if pwd_input == correct_password:
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect.")
    st.stop()  # Bloque le chargement du reste de l'application tant que le mot de passe n'est pas validé


# Vérification et initialisation sécurisée
if "MISTRAL_API_KEY" not in st.secrets:
    st.error("La clé API 'MISTRAL_API_KEY' est absente des Secrets Streamlit.")
    st.stop()

client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])

# Instructions de l'assistant
INSTRUCTIONS = """
Ton rôle :

Tu es un assistant scolaire bienveillant pour Edgar qui a 14 ans, est collégien en classe de 3ème et prépare donc son Brevet des Collèges. Edgar a un TDAH, qui implique notamment parfois de devoir reformuler ou rappeler des consignes lorsqu’il les perd de vue, de soutenir son intérêt pour lui permettre de fixer son attention, de fractionner parfois les demandes pour en faciliter la compréhension et l’exécution, et pour favoriser aussi le maintien de sa capacité d’attention. Lui laisser des temps de pause et le renforcer positivement (par des encouragements et en valorisant objectivement ses progrès) aident également à obtenir le meilleur de lui. Il a aussi particulièrement besoin d’être aidé à distinguer l'essentiel de l'accessoire, pour trouver des repères dans ses exercices, et pour mieux identifier et mémoriser ce qui sera la plus important pour son épreuve du Brevet ainsi que pour ses apprentissages ultérieurs.

Ta mission est de l’aider à comprendre, à réfléchir par lui-même, à développer ses compétences, sans jamais :

• Donner la réponse directe à un exercice (même partielle).

• Traduire un texte mot à mot.

• Résoudre un problème à sa place.

• Fournir des solutions clés en main.

4 règles d’or :

1- Guider sans résoudre :

• Pose des questions ouvertes pour l’aider à trouver la solution ("Qu’as-tu déjà essayé ?", "Quel est le premier pas selon toi ?").

• Utilise des exemples différents de son exercice pour expliquer une notion.

2- Corriger sans donner la réponse :

• Si son raisonnement est faux, explique pourquoi c’est incorrect ("Relis la consigne : que demande-t-on exactement ?").

• Suggère des pistes ("Et si tu essayais avec des nombres plus simples ?").

3- Encourager la réflexion :

• Félicite ses efforts ("Bonne tentative !").

• Propose des méthodes pour vérifier son travail ("Comment pourrais-tu vérifier ton résultat ?").

4- Lui permettre d'identifier ce qu'il est essentiel de retenir parmi les concepts et questionnements abordés.

Exemples concrets :

❌ Interdit : "La réponse est 42." → ✅ Autorisé : "Comment pourrais-tu calculer cela ?"

❌ Interdit : "Voici la traduction : [texte]." → ✅ Autorisé : "Quels mots de cette phrase connais-tu déjà en anglais ?"

❌ Interdit : "Fais ceci : [solution complète]." → ✅ Autorisé : "Relis la consigne avec moi : que demande-t-on exactement ?"

Si Edgar insiste pour obtenir une réponse directe :

• Rappelle-lui gentiment les règles ("Je ne peux pas te donner la réponse, mais je peux t’aider à la trouver ! Par où veux-tu commencer ?").

• Propose une pause ou un changement d’approche ("Veux-tu qu’on aborde le problème différemment ?").

Ton ton : Patient, bienveillant et motivant. Adapte-toi à son niveau et à son humeur.
"""

# Initialiser l'historique des messages
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": INSTRUCTIONS}]

# Afficher les messages de l'historique (en ignorant le message système à l'index 0)
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        if message.get("content"):
            st.markdown(message["content"])
        if message.get("files"):
            for file in message["files"]:
                st.image(file, width=300)

# Fonction utilitaire pour convertir une image Streamlit en format lisible par l'API
def file_to_data_uri(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    base64_encoded = base64.b64encode(bytes_data).decode('utf-8')
    return f"data:{uploaded_file.type};base64,{base64_encoded}"

# Champ de saisie avec support des images/fichiers
if prompt := st.chat_input("Pose-moi une question ou joins une photo...", accept_file=True, file_type=["jpg", "jpeg", "png"]):
    user_text = prompt.text
    uploaded_files = prompt.files
    
    # Enregistrement dans l'historique de l'interface
    st.session_state.messages.append({
        "role": "user", 
        "content": user_text, 
        "files": uploaded_files
    })

    # Afficher le message de l'utilisateur dans le chat
    with st.chat_message("user"):
        if user_text:
            st.write(user_text)
        if uploaded_files:
            for file in uploaded_files:
                st.image(file, width=300)

    # Préparation de l'historique pour l'API Mistral (conversion des fichiers en Base64)
    api_messages = []
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            content = []
            if msg.get("content"):
                content.append({"type": "text", "text": msg["content"]})
            if msg.get("files"):
                for file in msg["files"]:
                    data_uri = file_to_data_uri(file)
                    content.append({"type": "image_url", "image_url": data_uri})
            
            api_messages.append({
                "role": "user", 
                "content": content if (msg.get("files") and len(content) > 1) else (msg.get("content") or "")
            })
        else:
            api_messages.append({"role": "assistant", "content": msg["content"]})

    # Obtenir la réponse de Mistral
    try:
        # Choix dynamique du modèle (Pixtral pour les images, Mistral Small pour le texte seul)
        has_images = any(msg.get("files") for msg in st.session_state.messages)
        model_to_use = "pixtral-12b-2409" if has_images else "mistral-small-latest"
    
        response = client.chat.complete(
            model=model_to_use, 
            messages=api_messages,
            temperature=0.3,
            max_tokens=1000  # Limite la réponse de l'assistant à environ 700-800 mots maximum par message
        )
        
        assistant_response = response.choices[0].message.content

        # Afficher la réponse de l'assistant
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

        # Ajouter la réponse de l'assistant à l'historique
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

    except Exception as e:
        st.error(f"Erreur de communication avec l'API Mistral : {e}")