from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import create_engine
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
import re, json, logging, os
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = Flask(__name__)
SVG_TEMPLATE_PATH = "static/template.svg"
SVG_OUTPUT_PATH = "static/output.svg"

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


def popola_svg(template_path, output_path, node_data_array):
    tree = ET.parse(template_path)
    root = tree.getroot()
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    ET.register_namespace('', ns['svg'])

    contenuti = {node['key']: (node.get('text', ''), node.get('description', '')) for node in node_data_array}

    for key, (text_value, desc_value) in contenuti.items():
        text_elem = root.find(f".//svg:text[@id='{key}']", ns)
        if text_elem is not None:
            text_elem.text = text_value
        desc_elem = root.find(f".//svg:text[@id='{key}_desc']", ns)
        if desc_elem is not None:
            desc_elem.text = desc_value

    tree.write(output_path, encoding='utf-8', xml_declaration=True)
    logging.info(f"SVG scritto su {output_path}")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    query = data.get("query", "").strip()
    print(f"Query ricevuta: {query}")

    diagram_keywords = [
        "mappa concettuale", "diagramma", "diagramma a blocchi",
        "schema architetturale", "diagramma architettura"
    ]

    if any(keyword in query.lower() for keyword in diagram_keywords):
        relevant_docs = retriever.invoke(query)
        context = "\n".join(
            f"[fonte: {doc.metadata.get('source', 'sconosciuta')}] {doc.page_content}"
            for doc in relevant_docs
        )

        diagram_prompt = f"""Crea una rappresentazione dettagliata e ordinata sotto forma di mappa concettuale per una moderna Web Application progettata con il principio di Security by Design, seguendo le best practice aggiornate al 2025.

Documenti pertinenti trovati:
{context}

Il diagramma deve avere come nodo principale:
\"Architettura Software Secure-by-Design\"

Mostrare i seguenti cinque macro-layers principali, ciascuno con 3-5 sotto-nodi:

- Frontend Security (Azzurro): Validazione input, HTTPS+HSTS, Cookie sicuri, CSP, Clickjacking
- API Security (Viola): Autenticazione API, CORS restrittivo, API rate limiting
- Backend Security (Grigio): MFA, RBAC/ABAC, Sanitizzazione, Sessioni sicure, Audit log
- Database Security (Verde): Query sicure, Dati criptati, Mascheramento, Logging DB, Backup
- DevSecOps (Arancione): Patch mgmt, Hardening, SAST/DAST, Secret mgmt, SIEM

Per ogni nodo:
- `key`, `text`, `description` (massimo una frase)
- Blocchi principali con `color`
- Sotto-nodi senza `color`

Restituisci lo skeleton JSON:
- `nodes`: key, text, color (se presente), description
- `links`: from, to

Descrizione specifica fornita dall’utente:
{query}
"""
        response = llm.invoke(diagram_prompt)
        raw_content = response.content.strip()
        match = re.search(r"\{[\s\S]*\}", raw_content)

        diagram_json = "{}"
        output_svg_url = None

        if match:
            try:
                obj = json.loads(match.group(0))
                if "nodes" in obj and "links" in obj:
                    nodes = obj["nodes"]
                    links = obj["links"]
                    nodeDataArray = []
                    key_to_node = {node["key"]: node for node in nodes}

                    for node in nodes:
                        if "color" in node:
                            node["isGroup"] = True
                        nodeDataArray.append(node)

                    for link in links:
                        parent = link["from"]
                        child = link["to"]
                        if not key_to_node.get(child, {}).get("color"):
                            for n in nodeDataArray:
                                if n["key"] == child:
                                    n["group"] = parent

                    obj = {"nodeDataArray": nodeDataArray, "linkDataArray": links}
                    diagram_json = json.dumps(obj)
                    popola_svg(SVG_TEMPLATE_PATH, SVG_OUTPUT_PATH, nodeDataArray)
                    output_svg_url = "/static/output.svg"
            except json.JSONDecodeError as e:
                logging.error(f"JSONDecodeError: {e}")

        return jsonify({"diagram": diagram_json, "svg_url": output_svg_url})

    else:
        relevant_docs = retriever.invoke(query)
        context = "\n".join(doc.page_content for doc in relevant_docs)
        response = llm.invoke(
            f"Domanda utente: {query}\n Rispondi in modo cortese, breve e professionale in italiano."
        ) if not context.strip() else llm.invoke(
            ChatPromptTemplate.from_messages([
                ("system", """Sei un assistente educativo progettato per supportare professori e studenti delle scuole italiane.
Rispondi sempre in lingua italiana. Evita consigli medici, legali o personali.
{context}"""),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{query}"),
            ]).format_prompt(query=query, context=context, history=chat_history)
        )
        answer = response.content

        if any(phrase in answer.lower() for phrase in ["non lo so", "non sono sicuro", "non ho informazioni"]):
            answer = wikipedia_search.run(query)

        chat_history.append(HumanMessage(content=query))
        chat_history.append(AIMessage(content=answer))
        return jsonify({"answer": answer})

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    app.run(debug=True)

