import streamlit as st
from mistralai import Mistral

st.set_page_config(page_title="Le Prof perso d'Edgar", page_icon="🤖")

# Vérification et initialisation sécurisée
if "MISTRAL_API_KEY" not in st.secrets:
    st.error("La clé API 'MISTRAL_API_KEY' est absente des Secrets Streamlit.")
    st.stop()

client = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])

# Configuration de la page
# st.set_page_config(page_title="Le Prof perso d'Edgar", page_icon="🎓")
# st.title("Aide scolaire")
# st.write("Pose-moi tes questions, je t’aiderai à réfléchir sans donner les réponses !")





# Instructions de l'assistant (votre prompt reste inchangé)
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


# Initialiser l'historique des messages avec des dictionnaires standards
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": INSTRUCTIONS}]

# Afficher les messages de l'historique (en ignorant le message système à l'index 0)
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Champ de saisie pour l'utilisateur
if prompt := st.chat_input("Pose-moi une question !"):
    # Ajouter le message de l'utilisateur à l'historique
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Afficher le message de l'utilisateur
    with st.chat_message("user"):
        st.markdown(prompt)

    # Obtenir la réponse de Mistral
    try:
        response = client.chat.complete(
            model="mistral-small-latest",  # Modèle moderne et adapté
            messages=st.session_state.messages,
            temperature=0.3
        )
        
        assistant_response = response.choices[0].message.content

        # Afficher la réponse de l'assistant
        with st.chat_message("assistant"):
            st.markdown(assistant_response)

        # Ajouter la réponse de l'assistant à l'historique
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

    except Exception as e:
        st.error(f"Erreur de communication avec l'API Mistral : {e}")