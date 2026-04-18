#%%
import os

from dotenv import load_dotenv

from langchain_pinecone import PineconeVectorStore

from langchain_huggingface import HuggingFaceEmbeddings


# YOUR CODE HERE: Import GoogleGenerativeAIEmbeddings from langchain_google_genai
# YOUR CODE HERE: Import PineconeVectorStore from langchain_pinecone

# This loads your Gemini and Pinecone API keys from your .env file into memory

load_dotenv()


# ==========================================
# THE EMBEDDER (The Translator)
# ==========================================
# Initialize the Google Embedder. Remember to set the model to "models/text-embedding-004"
embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')


# ==========================================
# TASK A: THE UPLOAD FUNCTION
# ==========================================
def upload_chunks_to_pinecone(chunks, index_name):
    """
    Takes a list of text chunks, translates them into math using Google Embeddings,
    and uploads them to your Pinecone index.
    """
    PineconeVectorStore.from_texts(
        texts=chunks,
        embedding=embeddings,
        index_name=index_name
    )

    print(f"Translating and uploading {len(chunks)} chunks to Pinecone...")
    
    # YOUR CODE HERE: Use PineconeVectorStore.from_texts()
    # You need to pass it your chunks, your embeddings variable, and the index_name
    
    
    print("Upload complete!")

'''
==========================================
TASK B: THE SEARCH FUNCTION
==========================================
'''
def search_database(query, index_name):
    """Searches Pinecone for the top 3 most relevant chunks."""
    print(f"\nSearching database for: '{query}'...")
    
    # 1. Connect to the existing index
    vectorstore = PineconeVectorStore(index_name=index_name, embedding=embeddings)
    
    # 2. Perform the semantic search
    results = vectorstore.similarity_search(query, k=3)
    
    return results

if __name__ == '__main__':
    # --- TEST ENVIRONMENT ---
    index_name = "my-rag-project" 
    
    fake_chunks = [
        "The sky is blue because of Rayleigh scattering.",
        "The capital of France is Paris.",
        "A python is a large heavy-bodied nonvenomous snake."
    ]
    
    try:
        # Test 1: Uploading
        print("--- Testing Phase 1: Upload ---")
        upload_chunks_to_pinecone(fake_chunks, index_name=index_name)
        
        # Test 2: Retrieval
        print("\n--- Testing Phase 2: Search ---")
        user_question = "What city is the capital of France?"
        search_results = search_database(user_question, index_name=index_name)
        
        print("\nSUCCESS! Top Match Found:")
        print("-" * 40)
        # We print the raw text (.page_content) of the #1 result
        print(search_results[0].page_content) 
        print("-" * 40)
        
    except Exception as e:
        print(f"ERROR: {e}")