from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import create_engine
from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
import os

# http://127.0.0.1:5000

load_dotenv()

app = Flask(__name__)

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)

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

# Wikipedia API wrapper ottimizzato
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

    # Normale retrieval augmented generation (RAG)
    relevant_docs = retriever.invoke(query)
    context = "\n".join(doc.page_content for doc in relevant_docs)
    print(f"Context trovato: {bool(context.strip())}")

    if not context.strip():
        # Fallback chatbot generico se nessun documento trovato
        response = llm.invoke(f"Domanda utente: {query}\nRispondi in modo cortese, breve e professionale in italiano.")
        answer = response.content
    else:
        # Prompt con RAG
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             """Sei un assistente altamente capace, riflessivo e preciso. 
             Il tuo obiettivo è comprendere a fondo le intenzioni dell'utente, 
             porre domande di chiarimento se necessario, 
             pensare passo dopo passo a problemi complessi, 
             fornire risposte chiare e accurate e anticipare proattivamente informazioni utili di follow-up. 
             Dai sempre la priorità all'essere veritiero, sfumato, perspicace ed efficiente, 
             adattando le tue risposte specificamente alle esigenze e alle preferenze dell'utente.   
{context}
"""),  MessagesPlaceholder(variable_name="history"),
            ("human", "{query}")
        ])

        response = llm.invoke(
            prompt.format_prompt(query=query, context=context, history=chat_history)
        )
        answer = response.content
        
    
    print(f"Risposta AI prima fallback: {answer}")    

    # Fallback automatico: Wikipedia se AI mostra incertezza
    if any(phrase in answer.lower() for phrase in ["non lo so", "non sono sicuro", "non ho informazioni", "non ho trovato"]):
        wikipedia_result = wikipedia_search.run(query)
        print(f"Wikipedia fallback result: {wikipedia_result}")
        answer = f"{wikipedia_result}"

    # Aggiorna chat history
    chat_history.append(HumanMessage(content=query))
    chat_history.append(AIMessage(content=answer))
    print(f"Risposta finale inviata: {answer}")

    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=True)
