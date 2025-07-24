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

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = Flask(__name__)

SVG_TEMPLATE_PATH = "static/mappa2.svg"
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


def popola_svg(template_path, output_path, nodeDataArray, linkDataArray):
    tree = ET.parse(template_path)
    root = tree.getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}
    ET.register_namespace("", ns["svg"])

    contenuti = {
        node["key"]: (node.get("text", ""), node.get("description", ""))
        for node in nodeDataArray
    }

    for key, (text_value, desc_value) in contenuti.items():
        text_elem = root.find(f".//svg:tspan[@id='{key}']", ns)
        if text_elem is not None:
            text_elem.text = text_value

        desc_elem = root.find(f".//svg:tspan[@id='{key}_desc']", ns)
        if desc_elem is not None:
            desc_elem.text = desc_value

    tree.write(output_path, encoding="utf-8", xml_declaration=True)
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
            "nodeDataArray": [
                {"key": "root", "text": ""},
                {"key": "frontend_security", "text": ""},
                {"key": "fs1", "text": ""},
                {"key": "fs2", "text": ""},
                {"key": "fs3", "text": ""},
                {"key": "fs4", "text": ""},
                {"key": "fs5", "text": ""},
                {"key": "api_security", "text": ""},
                {"key": "as1", "text": ""},
                {"key": "as2", "text": ""},
                {"key": "as3", "text": ""},
                {"key": "backend_security", "text": ""},
                {"key": "bs1", "text": ""},
                {"key": "bs2", "text": ""},
                {"key": "bs3", "text": ""},
                {"key": "bs4", "text": ""},
                {"key": "bs5", "text": ""},
                {"key": "database_security", "text": ""},
                {"key": "ds1", "text": ""},
                {"key": "ds2", "text": ""},
                {"key": "ds3", "text": ""},
                {"key": "ds4", "text": ""},
                {"key": "ds5", "text": ""},
                {"key": "devsecops", "text": ""},
                {"key": "dv1", "text": ""},
                {"key": "dv2", "text": ""},
                {"key": "dv3", "text": ""},
                {"key": "dv4", "text": ""},
                {"key": "dv5", "text": ""},
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
        popola_svg(
            SVG_TEMPLATE_PATH,
            SVG_OUTPUT_PATH,
            diagram_skeleton["nodeDataArray"],
            diagram_skeleton["linkDataArray"],
        )
        return jsonify({"diagram": diagram_skeleton, "svg_url": "static/output.svg"})

    elif any(keyword in query.lower() for keyword in diagram_keywords):
        relevant_docs = retriever.invoke(query)
        context = "\n".join(
            f"[fonte: {doc.metadata.get('source', 'sconosciuta')}] {doc.page_content}"
            for doc in relevant_docs
        )
        print(f"Context diagramma trovato: {bool(context.strip())}")

        diagram_prompt = f"""Popola i nodi di un diagramma concettuale Secure-by-Design per una Web Application moderna, in base al seguente contesto tecnico:

Documenti pertinenti trovati:
{context}

Obiettivo:
Generare un JSON `nodeDataArray` dove ogni nodo ha:
- `key`: identificatore univoco (corrisponde all'id SVG già esistente)
- `text`: etichetta da mostrare nel nodo SVG

Struttura del diagramma:
- Nodo principale: `"root"` → testo: `"Architettura software per CyberSecurity"`
- Macro-aree di sicurezza:
  - `frontend_security`
  - `api_security`
  - `backend_security`
  - `database_security`
  - `devsecops`
- Ogni area ha sotto-nodi secondo lo schema:
  - `fs1`–`fs5` per `frontend_security`
  - `as1`–`as3` per `api_security`
  - `bs1`–`bs5` per `backend_security`
  - `ds1`–`ds5` per `database_security`
  - `dv1`–`dv5` per `devsecops`

Lista completa delle `key` da restituire:
["root", "frontend_security", "fs1", "fs2", "fs3", "fs4", "fs5", "api_security", "as1", "as2", "as3", "backend_security", "bs1", "bs2", "bs3", "bs4", "bs5", "database_security", "ds1", "ds2", "ds3", "ds4", "ds5", "devsecops", "dv1", "dv2", "dv3", "dv4", "dv5"]

Istruzioni importanti:
- Per i macro-nodi (quelli con `_security` o `devsecops`), fornisci solo il campo `text`.
- Usa termini tecnici coerenti con standard OWASP, NIST, Zero Trust e DevSecOps aggiornati al 2025.
- NON generare collegamenti tra i nodi (`links`): sono già predefiniti.

Output atteso:
Restituisci solo un JSON valido con la struttura seguente:
```json
{{"nodeDataArray": [...]}}"""

        response = llm.invoke(diagram_prompt)
        raw_content = response.content.strip()

        match = re.search(r"\{[\s\S]*\}", raw_content)
        if match:
            try:
                obj = json.loads(match.group(0))

                if "nodeDataArray" in obj:
                    nodeDataArray = obj["nodeDataArray"]
                    popola_svg(SVG_TEMPLATE_PATH, SVG_OUTPUT_PATH, nodeDataArray, [])
                    return jsonify({
                        "diagram": json.dumps(obj),
                        "svg_url": "static/output.svg"
                    })

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
