from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("PGVECTOR_CONNECTION_STRING")
engine = create_engine(DATABASE_URL) 

def ingest_pdf(pdf_path, collection_name="my_collection"):
    
    if isinstance(pdf_path, str):
        pdf_path = [pdf_path]
        
        
    all_docs = []
    text_splitter= RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    for path in pdf_path:
        loader = PyPDFLoader(path)
        documents = loader.load()
        docs = text_splitter.split_documents(documents)
        all_docs.extend(docs)
        print(f"Ingestione completata per '{path}': {len(docs)} chunks")
    
    embeddings = OpenAIEmbeddings()
    
    vector_store = PGVector.from_documents(
        embedding=embeddings,
        documents=all_docs,
        collection_name=collection_name,
        connection=engine,
        pre_delete_collection=True 
    )
    
    
    print(f"file caricati {len(all_docs)} documenti nella collezione '{collection_name}'.")
    return vector_store

if __name__ == "__main__":
    ingest_pdf([
        "data/DATA_SECURITY.pdf",
        "data/OWASP.pdf",
        "data/Security.pdf",
        "data/OWASP_Testing_Guide.pdf",
        "data/OWASP_Application_Security.pdf"
    ])
