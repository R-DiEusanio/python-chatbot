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
# import xml.etree.ElementTree as ET  

logging.basicConfig(level=logging.INFO)
load_dotenv()

app = Flask(__name__)
# SVG_TEMPLATE_PATH = "static/template.svg" 
# SVG_OUTPUT_PATH = "static/output.svg"      

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


# def popola_svg(template_path, output_path, node_data_array):
#     tree = ET.parse(template_path)
#     root = tree.getroot()
#     ns = {'svg': 'http://www.w3.org/2000/svg'}
#     ET.register_namespace('', ns['svg'])

#     contenuti = {node['key']: (node.get('text', ''), node.get('description', '')) for node in node_data_array}

#     for key, (text_value, desc_value) in contenuti.items():
#         text_elem = root.find(f".//svg:text[@id='{key}']", ns)
#         if text_elem is not None:
#             text_elem.text = text_value
#         desc_elem = root.find(f".//svg:text[@id='{key}_desc']", ns)
#         if desc_elem is not None:
#             desc_elem.text = desc_value

#     tree.write(output_path, encoding='utf-8', xml_declaration=True)
#     logging.info(f"SVG scritto su {output_path}")

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
        return jsonify({"svg_url": "/static/template.svg"})  

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
