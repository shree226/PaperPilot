import os
import re
import shutil
from langchain_community.document_loaders import DirectoryLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

VECTOR_DB_ROOT = "database"


def get_collection_path(collection_id="default"):
    """Return a safe Chroma directory for one paper collection."""
    collection_id = re.sub(r"[^a-zA-Z0-9_-]", "_", collection_id or "default")
    return os.path.join(VECTOR_DB_ROOT, collection_id)


def get_or_create_vector_db(collection_id="default"):
    """Get or create the vector database for one chat/paper collection."""
    vector_db_path = get_collection_path(collection_id)
    os.makedirs("./files", exist_ok=True)
    embeddings = HuggingFaceEmbeddings()

    if os.path.exists(vector_db_path) and os.listdir(vector_db_path):
        return Chroma(persist_directory=vector_db_path, embedding_function=embeddings)

    loader = DirectoryLoader("./files")
    docs = loader.load()
    if not docs:
        return None

    semantic_text_splitter = SemanticChunker(embeddings)
    documents = semantic_text_splitter.split_documents(docs)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)
    split_documents = text_splitter.split_documents(documents)
    return Chroma.from_documents(split_documents, embeddings, persist_directory=vector_db_path)


def add_documents(documents, collection_id="default"):
    """Add documents to a specific chat/paper collection."""
    vector_db_path = get_collection_path(collection_id)
    os.makedirs(vector_db_path, exist_ok=True)
    embeddings = HuggingFaceEmbeddings()

    semantic_text_splitter = SemanticChunker(embeddings)
    documents = semantic_text_splitter.split_documents(documents)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=400)
    split_documents = text_splitter.split_documents(documents)

    if os.listdir(vector_db_path):
        vectorstore = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)
        vectorstore.add_documents(split_documents)
    else:
        vectorstore = Chroma.from_documents(split_documents, embeddings, persist_directory=vector_db_path)

    return vectorstore


def delete_collection(collection_id="default"):
    """Delete all persisted vectors for one chat/paper collection."""
    vector_db_path = get_collection_path(collection_id)
    if os.path.exists(vector_db_path):
        shutil.rmtree(vector_db_path)


def delete_document(collection_id, document_name):
    """Delete all vector chunks whose source metadata matches a document name."""
    vector_db_path = get_collection_path(collection_id)
    if not os.path.exists(vector_db_path) or not os.listdir(vector_db_path):
        return
    embeddings = HuggingFaceEmbeddings()
    vectorstore = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)
    vectorstore.delete(where={"source": document_name})


def get_collection_document_count(collection_id="default"):
    """Return the number of persisted vector records in a collection."""
    vector_db_path = get_collection_path(collection_id)
    if not os.path.exists(vector_db_path) or not os.listdir(vector_db_path):
        return 0
    embeddings = HuggingFaceEmbeddings()
    vectorstore = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)
    return len(vectorstore.get()["ids"])
