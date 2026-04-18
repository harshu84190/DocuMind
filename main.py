import streamlit as st
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Notice the "app." prefix! This tells Python to look inside your app/ folder
from app import document_processor as dp
from app import vector_store as vs

# Load environment variables (Pinecone and Gemini API keys)
load_dotenv()

# Initialize the Gemini LLM (The Brain)

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

st.set_page_config(page_title="RAG Assistant", layout="wide")
st.title("My AI Document Assistant 🤖")

# ==========================================
# SIDEBAR: DATA INGESTION
# ==========================================
with st.sidebar:
    st.header("1. Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF, TXT, or Excel file", type=["pdf", "txt", "xlsx"])
    
    # We need to know which Pinecone index to use
    index_name = "my-rag-project" 
    
    if st.button("Process Document"):
        if uploaded_file is not None:
            with st.spinner("Processing and uploading to Pinecone..."):
                try:
                    # 1. Extract the text
                    raw_text = dp.extract_text_from_file(uploaded_file)
                    
                    # 2. Chunk the text
                    chunks = dp.chunk_text(raw_text)
                    
                    # 3. Upload to Pinecone
                    vs.upload_chunks_to_pinecone(chunks, index_name=index_name)
                    
                    st.success(f"Success! {len(chunks)} chunks uploaded to the database.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
        else:
            st.warning("Please upload a file first.")

# ==========================================
# MAIN INTERFACE: THE CHAT
# ==========================================
st.header("2. Ask Questions")
user_query = st.text_input("Ask a question about your uploaded document:")

if st.button("Ask AI"):
    if user_query:
        with st.spinner("Searching database and thinking..."):
            try:
                # 1. Search the database for the top 3 chunks
                search_results = vs.search_database(user_query, index_name="my-rag-project")
                
                # 2. Stitch the chunks together into one massive string of context
                context = "\n\n".join([doc.page_content for doc in search_results])
                
                # 3. Build the prompt for Gemini
                prompt = f"""
                You are a highly intelligent assistant. Use the following pieces of retrieved context to answer the user's question. 
                If the answer is not in the context, just say "I don't know based on the document." Do not make things up.
                
                Context: {context}
                
                Question: {user_query}
                """
                
                # 4. Get the answer and display it!
                response = llm.invoke(prompt)
                
                st.markdown("### Answer:")
                st.info(response.content)
                
                # Optional: Show the user the actual chunks we retrieved for transparency
                with st.expander("See retrieved database chunks"):
                    for i, doc in enumerate(search_results):
                        st.markdown(f"**Chunk {i+1}:**")
                        st.write(doc.page_content)
                        st.divider()
                        
            except Exception as e:
                st.error(f"An error occurred while searching: {e}")