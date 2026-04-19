import os
import hashlib
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

def clear_namespace(index_name, user_namespace):
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(index_name)
    # This specifically deletes only the vectors in this exact namespace
    index.delete(delete_all=True, namespace=user_namespace)

load_dotenv()
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Notice we added 'user_namespace' to isolate user data!
def upload_chunks_to_pinecone(documents, index_name, user_namespace="default_user"):
    """Hashes text to prevent duplicates and uploads chunks + metadata."""
    print(f"Uploading {len(documents)} chunks to namespace: {user_namespace}...")
    
    # 1. DEDUPLICATION: Generate a unique ID based on the chunk's actual text
    # We use doc.page_content because it is a Document object, not a string!
    unique_ids = [hashlib.md5(doc.page_content.encode('utf-8')).hexdigest() for doc in documents]
    
    # 2. MULTI-TENANCY: Connect to the specific user's namespace
    vectorstore = PineconeVectorStore(
        index_name=index_name, 
        embedding=embeddings, 
        namespace=user_namespace
    )
    
    # 3. CRITICAL FIX: Use add_documents instead of add_texts
    vectorstore.add_documents(documents=documents, ids=unique_ids)
    print("Upload complete!")

def search_database(query, index_name, user_namespace="default_user"):
    """Searches only within the specific user's namespace."""
    vectorstore = PineconeVectorStore(
        index_name=index_name, 
        embedding=embeddings, 
        namespace=user_namespace
    )
    return vectorstore.similarity_search(query, k=3)
