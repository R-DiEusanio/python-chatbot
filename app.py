from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import create_engine
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
import re,json
import logging
import os

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = Flask(__name__)

llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

DATABASE_URL = os.getenv("PGVECTOR_CONNECTION_STRING")
engine = create_engine(DATABASE_URL)

embeddings = OpenAIEmbeddings()
vector_store = PGVector(
    collection_name="my_collection",
    connection=engine,
    embeddings=embeddings
)

retriever = vector_store.as_retriever()

chat_history = []
api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=300)
wikipedia_search = WikipediaQueryRun(api_wrapper=api_wrapper)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    query = data.get("query", "").strip()
    print(f"Query ricevuta: {query}")

    diagram_keywords = ["mappa concettuale", "diagramma", "diagramma a blocchi", "schema architetturale", "diagramma architettura"]

    # NUOVA CONDIZIONE per il diagramma "schema base"
    if "schema base diagramma" in query.lower() or "diagramma ordine layers" in query.lower():
        diagram_skeleton = {
            "nodes": [
                { "key": "Frontend", "text": "Frontend / Presentation", "color": "#ADD8E6", "description": "" },
                { "key": "APIGateway", "text": "API Gateway / BFF", "color": "#1E90FF", "description": "" },
                { "key": "IAM", "text": "Identità e accessi (IAM)", "color": "#FFA500", "description": "" },
                { "key": "Backend", "text": "Backend / Microservices", "color": "#A9A9A9", "description": "" },
                { "key": "Networking", "text": "Networking / Rete", "color": "#9370DB", "description": "" },
                { "key": "Storage", "text": "Storage & Database", "color": "#3CB371", "description": "" },
                { "key": "Telemetria", "text": "Telemetria e sicurezza operativa", "color": "#FF77FF", "description": "" },
                { "key": "DevSecOps", "text": "DevSecOps", "color": "#D3D3D3", "description": "" },
                { "key": "Governance", "text": "Governance & Compliance", "color": "#F5F5DC", "description": "" }
            ],
            "links": [
                { "from": "Frontend", "to": "APIGateway" },
                { "from": "APIGateway", "to": "IAM" },
                { "from": "IAM", "to": "Backend" },
                { "from": "Backend", "to": "Networking" },
                { "from": "Networking", "to": "Storage" },
                { "from": "Storage", "to": "Telemetria" },
                { "from": "Telemetria", "to": "DevSecOps" },
                { "from": "DevSecOps", "to": "Governance" }
            ]
        }
        logging.info(f"Diagramma schema base inviato:\n{diagram_skeleton}")
        return jsonify({"diagram": json.dumps(diagram_skeleton)})

    elif any(keyword in query.lower() for keyword in diagram_keywords):
        relevant_docs = retriever.invoke(query)
        context = "\n".join(
            f"[fonte: {doc.metadata.get('source', 'sconosciuta')}] {doc.page_content}"
            for doc in relevant_docs
        )
        
        print(f"Context diagramma trovato: {bool(context.strip())}")
        
        diagram_prompt = f"""Crea una rappresentazione dettagliata e completa sotto forma di mappa concettuale per una moderna Web Application con cybersecurity integrata, seguendo le best practice aggiornate al 2025.

Analizza i documenti pertinenti recuperati e usa i concetti chiave identificati per strutturare il diagramma.

Documenti pertinenti trovati:
{context}

Il diagramma deve avere come nodo principale:
"Applicazione Web"

E svilupparsi con i seguenti rami principali (aggiungi sottorami pertinenti):
- Frontend / Presentation
- API Gateway
- Backend / Microservices
- Storage & Database
- Identità e accessi (IAM)
- Rete / Networking
- Telemetria & Monitoring
- DevSecOps
- Governance & Compliance

Per ciascun ramo descrivi i principali controlli di sicurezza integrati: autenticazione, autorizzazione, encryption, networking sicuro (VNet, private endpoints), mTLS, rate limiting, monitoring, threat detection, ecc.

Il diagramma deve:
- Mostrare chiaramente le relazioni tra i blocchi
- Differenziare visivamente i blocchi principali con i seguenti colori:
  • Frontend / Presentation: Azzurro chiaro (#ADD8E6)
  • API Gateway: Blu scuro (#1E90FF)
  • Backend / Microservices: Grigio (#A9A9A9)
  • Storage & Database: Verde (#3CB371)
  • Identità e accessi (IAM): Arancione (#FFA500)
  • Rete / Networking: Viola (#9370DB)
  • Telemetria & Monitoring: Magenta chiaro (#FF77FF)
  • DevSecOps: Grigio chiaro (#D3D3D3)
  • Governance & Compliance: Beige (#F5F5DC)

- Usare una struttura modulare e ordinata, simile a una vera **mind map**.
- Includere per ciascun nodo e sottoramo una breve descrizione chiara e professionale (1-2 frasi) adatta a un architetto IT che deve implementare questa soluzione come modello di riferimento ufficiale.
- Se i documenti recuperati non sono sufficienti o mancano, basati sulle best practice note fino al 2025 e completa comunque il diagramma completo e descrittivo.

Formato risultato:
- JSON con due array:
  - nodes: key, text, color, description
  - links: from, to

Descrizione specifica fornita dall'utente:
{query}
"""
        response = llm.invoke(diagram_prompt)
        raw_content = response.content.strip()

        match = re.search(r"\{[\s\S]*\}", raw_content)
        if match:
            try:
                obj = json.loads(match.group(0))
                diagram_json = json.dumps(obj)
            except json.JSONDecodeError as e:
                logging.error(f"JSONDecodeError: {e}")
                diagram_json = "{}"

        logging.info(f"Diagramma JSON finale inviato:\n{diagram_json}")
        return jsonify({"diagram": diagram_json})

    else:
        relevant_docs = retriever.invoke(query)
        context = "\n".join(doc.page_content for doc in relevant_docs)
        print(f"Context trovato: {bool(context.strip())}")

        if not context.strip():
            response = llm.invoke(f"Domanda utente: {query}\n Rispondi in modo cortese, breve e professionale in italiano.")
            answer = response.content
        else:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Sei un assistente educativo progettato per supportare professori e studenti delle scuole italiane. 
Rispondi sempre in lingua italiana. Evita consigli medici, legali o personali.
{context}"""),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{query}")
            ])
            response = llm.invoke(
                prompt.format_prompt(query=query, context=context, history=chat_history)
            )
            answer = response.content

        print(f"Risposta AI prima fallback: {answer}")

        if any(phrase in answer.lower() for phrase in ["non lo so", "non sono sicuro", "non ho informazioni", "non ho trovato"]):
            wikipedia_result = wikipedia_search.run(query)
            print(f"Wikipedia fallback result: {wikipedia_result}")
            answer = f"{wikipedia_result}"

        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=answer))
        print(f"Risposta finale inviata: {answer}")

        return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=True)
