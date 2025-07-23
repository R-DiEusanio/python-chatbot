from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import create_engine
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
import re, json
import logging
import os
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO) # in console solo messaggi Error o Warning
load_dotenv() #caricamento variabili ambiente dal file .env

app = Flask(__name__)

SVG_TEMPLATE_PATH = "static/mappa2.svg" # File SVG vuoto/modello con id univoci
SVG_OUTPUT_PATH = "static/output.svg" # File SVG popolato che verrà scritto e servito

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)

DATABASE_URL = os.getenv("PGVECTOR_CONNECTION_STRING")
engine = create_engine(DATABASE_URL)

embeddings = OpenAIEmbeddings()
vector_store = PGVector(
    collection_name="my_collection", connection=engine, embeddings=embeddings
)

retriever = vector_store.as_retriever()

chat_history = []
api_wrapper = WikipediaAPIWrapper(top_k_results=1, doc_content_chars_max=300)
wikipedia_search = WikipediaQueryRun(api_wrapper=api_wrapper)

#funzione popola SVG
def popola_svg(template_path,output_path,nodeDataArray,linkDataArray):
    tree = ET.parse(template_path)
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    ET.register_namespace('', ns['svg'])
    
    contenuti =  {node['key']: (node.get('text', ''), node.get('description', '')) for node in nodeDataArray} 
    
    for key, (text_value, desc_value) in contenuti.items():
        text_elem = root.find(f".//svg:tspan[@id='{key}']", ns)
        if text_elem is not None:
            text_elem.text = text_value
            
        desc_elem = root.find(f".//svg:tspan[@id='{key}_desc']", ns)
        if desc_elem is not None:
            desc_elem.text = desc_value
            
    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    logging.info(f"SVG popolato salvato in {output_path}")
    
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    query = data.get("query", "").strip()
    print(f"Query ricevuta: {query}")

    diagram_keywords = [
        "mappa concettuale",
        "diagramma",
        "diagramma a blocchi",
        "schema architetturale",
        "diagramma architettura",
    ]

    if (
        "schema base diagramma" in query.lower()
        or "diagramma ordine layers" in query.lower()
    ):
        diagram_skeleton = {
            "nodeDataArray": [ #le key devono corrispondere agli id nel file SVG
                {"key": "root", "text": "", "description": ""},
                {
                    "key": "frontend_security",
                    "text": "",
                    "description": "",
                    "color": "#ADD8E6",
                },
                {"key": "fs1", "text": "", "description": ""},
                {"key": "fs2", "text": "", "description": ""},
                {"key": "fs3", "text": "", "description": ""},
                {"key": "fs4", "text": "", "description": ""},
                {"key": "fs5", "text": "", "description": ""},
                {
                    "key": "api_security",
                    "text": "",
                    "description": "",
                    "color": "#9370DB",
                },
                {"key": "as1", "text": "", "description": ""},
                {"key": "as2", "text": "", "description": ""},
                {"key": "as3", "text": "", "description": ""},
                {
                    "key": "backend_security",
                    "text": "",
                    "description": "",
                    "color": "#A9A9A9",
                },
                {"key": "bs1", "text": "", "description": ""},
                {"key": "bs2", "text": "", "description": ""},
                {"key": "bs3", "text": "", "description": ""},
                {"key": "bs4", "text": "", "description": ""},
                {"key": "bs5", "text": "", "description": ""},
                {
                    "key": "database_security",
                    "text": "",
                    "description": "",
                    "color": "#3CB371",
                },
                {"key": "ds1", "text": "", "description": ""},
                {"key": "ds2", "text": "", "description": ""},
                {"key": "ds3", "text": "", "description": ""},
                {"key": "ds4", "text": "", "description": ""},
                {"key": "ds5", "text": "", "description": ""},
                
                {"key": "devsecops", 
                 "text": "", "description": "", 
                 "color": "#FFA500"},
                {"key": "dv1", "text": "", "description": ""},
                {"key": "dv2", "text": "", "description": ""},
                {"key": "dv3", "text": "", "description": ""},
                {"key": "dv4", "text": "", "description": ""},
                {"key": "dv5", "text": "", "description": ""},
            ],
            "linkDataArray": [
                {"from": "root", "to": "frontend_security"},
                {"from": "root", "to": "api_security"},
                {"from": "root", "to": "backend_security"},
                {"from": "root", "to": "database_security"},
                {"from": "root", "to": "devsecops"},
                
                {"from": "frontend_security", "to": "fs1"},
                {"from": "frontend_security", "to": "fs2"},
                {"from": "frontend_security", "to": "fs3"},
                {"from": "frontend_security", "to": "fs4"},
                {"from": "frontend_security", "to": "fs5"},
                
                {"from": "api_security", "to": "as1"},
                {"from": "api_security", "to": "as2"},
                {"from": "api_security", "to": "as3"},
                
                {"from": "backend_security", "to": "bs1"},
                {"from": "backend_security", "to": "bs2"},
                {"from": "backend_security", "to": "bs3"},
                {"from": "backend_security", "to": "bs4"},
                {"from": "backend_security", "to": "bs5"},
                
                {"from": "database_security", "to": "ds1"},
                {"from": "database_security", "to": "ds2"},
                {"from": "database_security", "to": "ds3"},
                {"from": "database_security", "to": "ds4"},
                {"from": "database_security", "to": "ds5"},
                
                {"from": "devsecops", "to": "dv1"},
                {"from": "devsecops", "to": "dv2"},
                {"from": "devsecops", "to": "dv3"}, 
                {"from": "devsecops", "to": "dv4"},
                {"from": "devsecops", "to": "dv5"},
                
            ],
        }

        logging.info(f"Diagramma schema base inviato:\n{diagram_skeleton}")
        popola_svg(SVG_TEMPLATE_PATH, SVG_OUTPUT_PATH, diagram_skeleton["nodeDataArray"], diagram_skeleton["linkDataArray"])
        return jsonify({"diagram": diagram_skeleton, "svg_url": "static/output.svg"})

    elif any(keyword in query.lower() for keyword in diagram_keywords):
        relevant_docs = retriever.invoke(query)
        context = "\n".join(
            f"[fonte: {doc.metadata.get('source', 'sconosciuta')}] {doc.page_content}"
            for doc in relevant_docs
        )
        print(f"Context diagramma trovato: {bool(context.strip())}")

        diagram_prompt = f"""Crea una rappresentazione dettagliata e ordinata sotto forma di mappa concettuale per una moderna Web Application progettata con il principio di Security by Design, seguendo le best practice aggiornate al 2025.

Documenti pertinenti trovati:
{context}

Il diagramma deve avere come nodo principale:
"Architettura software per CyberSecurity"

Mostrare i seguenti tre macro-layers principali, ciascuno con tre dettagli operativi come sotto-nodi:

- Frontend:
  - Validazione input lato client
  - Content Security Policy (CSP)
  - HTTPS

- Backend:
  - Autenticazione e Autorizzazione robuste
  - Sanitizzazione input lato server
  - Logging sicuro

- Database:
  - Crittografia dati
  - Minimo privilegio DB
  - Backup sicuri

Il diagramma deve:
- Mostrare i layer principali in sequenza ordinata verticale (top-down).
- Mostrare chiaramente le relazioni padre-figlio tra layer principali e dettagli operativi.
- Per ogni nodo, includere una proprietà `description` sintetica (massimo una frase) che spiega il ruolo del nodo.
- Applicare i seguenti colori ai blocchi principali:
  - Frontend: #ADD8E6
  - Backend: #A9A9A9
  - Database: #3CB371

Per i dettagli operativi (sotto-nodi), lascia `color` assente e fornisci la `description`.

Restituisci solo lo skeleton JSON con queste proprietà:
- `nodes`: key, text, color (solo se blocco principale), description
- `links`: from, to

Descrizione specifica fornita dall’utente:
{query}
"""
        response = llm.invoke(diagram_prompt)
        raw_content = response.content.strip()

        match = re.search(r"\{[\s\S]*\}", raw_content)
        if match:
            try:
                obj = json.loads(match.group(0))
                if "nodes" in obj and "links" in obj:
                    nodes = obj["nodes"]
                    links = obj["links"]
                    nodeDataArray = []
                    key_to_node = {node["key"]: node for node in nodes}

                    for node in nodes:
                        if "color" in node and node["color"]:
                            node["isGroup"] = True
                        nodeDataArray.append(node)

                    for link in links:
                        parent = link["from"]
                        child = link["to"]
                        child_node = key_to_node.get(child)
                        if child_node and not child_node.get("color"):
                            for n in nodeDataArray:
                                if n["key"] == child:
                                    n["group"] = parent
                                    break

                    obj = {"nodeDataArray": nodeDataArray, "linkDataArray": links}
                    diagram_json = json.dumps(obj)
                    popola_svg(SVG_TEMPLATE_PATH, SVG_OUTPUT_PATH, nodeDataArray, links)                    
                    return jsonify({"diagram": diagram_json, "svg_url": "static/output.svg"})
                    

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
            response = llm.invoke(
                f"Domanda utente: {query}\n Rispondi in modo cortese, breve e professionale in italiano."
            )
            answer = response.content
        else:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """Sei un assistente educativo progettato per supportare professori e studenti delle scuole italiane.
Rispondi sempre in lingua italiana. Evita consigli medici, legali o personali.
{context}""",
                    ),
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{query}"),
                ]
            )
            response = llm.invoke(
                prompt.format_prompt(query=query, context=context, history=chat_history)
            )
            answer = response.content

        print(f"Risposta AI prima fallback: {answer}")

        if any(
            phrase in answer.lower()
            for phrase in [
                "non lo so",
                "non sono sicuro",
                "non ho informazioni",
                "non ho trovato",
            ]
        ):
            wikipedia_result = wikipedia_search.run(query)
            print(f"Wikipedia fallback result: {wikipedia_result}")
            answer = wikipedia_result

        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=answer))
        print(f"Risposta finale inviata: {answer}")

        return jsonify({"answer": answer})
    
    


if __name__ == "__main__":
    app.run(debug=True)
