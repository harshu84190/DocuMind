import streamlit as st
import os

# 1. PAGE CONFIG MUST BE FIRST
st.set_page_config(page_title="DocuMind Assistant", layout="wide")

# 2. THE ENVIRONMENT BRIDGE
# If we are in Streamlit Cloud, push st.secrets into the OS environment
# so LangChain and Supabase can find them.
if hasattr(st, "secrets"):
    for k, v in st.secrets.items():
        os.environ[k] = str(v)

# Load local .env if it exists (this handles your local laptop testing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 3. IMPORTS AFTER CONFIG
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from app import document_processor as dp
from app import vector_store as vs
from app import auth_db

# Primary model wrapper
primary_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

# Secondary model if the primary throws a 429 (Too Many Requests) or another error
fallback_llm = ChatGroq(model="llama-3.3-70b-versatile")

# Attach the fallback gracefully! 
llm = primary_llm.with_fallbacks([fallback_llm])

# ==========================================
# APP CONFIG & ADMIN SETTINGS
# ==========================================
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL') # Change this to your actual email if you want admin rights
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME')

# Initialize session memory
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "namespace" not in st.session_state:
    st.session_state.namespace = ""
if "query_count" not in st.session_state:
    st.session_state.query_count = 0
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "auth_email" not in st.session_state:
    st.session_state.auth_email = ""
if "auth_username" not in st.session_state:
    st.session_state.auth_username = ""

# ==========================================
# SECURE OTP LOGIN GATE
# ==========================================
if not st.session_state.logged_in:
    st.title("🔒 DocuMind Secure Workspace")
    
    # STEP 1: Ask for Email
    if not st.session_state.otp_sent:
        st.markdown("Enter your email to receive a secure login code.")
        with st.form("email_form"):
            email = st.text_input("Email Address")
            username = st.text_input("Username (First time only)")
            
            if st.form_submit_button("Send Login Code"):
                if email:
                    with st.spinner("Sending secure code..."):
                        success = auth_db.send_magic_code(email)
                        if success:
                            st.session_state.auth_email = email.lower().strip()
                            st.session_state.auth_username = username.strip() if username else "User"
                            st.session_state.otp_sent = True
                            st.rerun()
                        else:
                            st.error("Failed to send code. Please check your Supabase settings.")
                else:
                    st.error("Please enter an email address.")

    # STEP 2: Verify the Code
    else:
        st.info(f"📧 We sent a 6-digit code to **{st.session_state.auth_email}**")
        with st.form("code_form"):
            code = st.text_input("Enter 6-digit code")
            
            if st.form_submit_button("Verify & Login"):
                with st.spinner("Verifying..."):
                    valid_user = auth_db.verify_magic_code(st.session_state.auth_email, code)
                    
                    if valid_user:
                        # 1. Sync with PostgreSQL
                        db_user = auth_db.get_user(st.session_state.auth_email)
                        if not db_user:
                            auth_db.create_user(st.session_state.auth_username, st.session_state.auth_email)
                            st.session_state.query_count = 0
                        else:
                            st.session_state.query_count = db_user['query_count']
                            
                        # 2. Unlock the app
                        clean_email = st.session_state.auth_email.split('@')[0]
                        st.session_state.namespace = f"user_{clean_email}"
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Invalid or expired code. Please try again.")
        
        if st.button("Start Over"):
            st.session_state.otp_sent = False
            st.rerun()

# ==========================================
# THE MAIN APPLICATION (PROTECTED)
# ==========================================
else:
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state.namespace}**")
        if st.button("Logout"):
            st.session_state.clear() # Wipes all memory
            st.rerun()
            
        st.divider()

        # --- DATA INGESTION ---
        st.header("1. Upload Document")
        uploaded_file = st.file_uploader("Choose a file", type=["pdf", "txt", "xlsx", "docx"])
        
        if st.button("Process Document"):
            if uploaded_file:
                with st.spinner("Processing..."):
                    try:
                        document = dp.extract_text_from_file(uploaded_file)
                        chunks = dp.chunk_text(document)
                        vs.upload_chunks_to_pinecone(chunks, index_name=PINECONE_INDEX_NAME, user_namespace=st.session_state.namespace)
                        st.success(f"Uploaded {len(chunks)} chunks.")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("Please upload a file.")

        st.divider()
        if st.button("🗑️ Clear Workspace"):
            with st.spinner("Deleting records..."):
                vs.clear_namespace(index_name=PINECONE_INDEX_NAME, user_namespace=st.session_state.namespace)
                st.success("Workspace cleared!")

    # --- CHAT INTERFACE ---
    st.title("My AI Document Assistant 🤖")
    
    is_admin = (st.session_state.auth_email == ADMIN_EMAIL)
    if not is_admin:
        tries_left = max(0, 5 - st.session_state.query_count)
        st.caption(f"Free Tier: You have {tries_left} queries remaining.")
    else:
        st.caption("👑 Admin Mode: Unlimited Queries")

    user_query = st.text_input("Ask a question:")

    if st.button("Ask AI"):
        if user_query:
            if not is_admin and st.session_state.query_count >= 5:
                st.error("🔒 Limit Reached! You have used your 5 free queries.")
                st.stop()

            with st.spinner("Thinking..."):
                try:
                    search_results = vs.search_database(user_query, index_name=PINECONE_INDEX_NAME, user_namespace=st.session_state.namespace)
                    
                    # ==========================================
                    # 🔍 BACKEND OBSERVABILITY LOGS
                    # ==========================================
                    print("\n" + "="*60)
                    print(f"🤖 USER QUERY: {user_query}")
                    print(f"📚 RETRIEVED {len(search_results)} CHUNKS FROM PINECONE:")
                    
                    for i, doc in enumerate(search_results):
                        print("-" * 60)
                        print(f"--- CHUNK {i+1} ---")
                        print(f"METADATA: {doc.metadata}") 
                        print(f"CONTENT: {doc.page_content}")
                    
                    print("="*60 + "\n")
                    # ==========================================
                    
                    with st.expander("🔍 View Retrieved Context Chunks"):
                        for i, doc in enumerate(search_results):
                            st.markdown(f"**Chunk {i+1} from `{doc.metadata.get('source', 'Unknown')}`**")
                            st.info(doc.page_content)
                    
                    context = "\n\n".join([doc.page_content for doc in search_results])
                    
                    prompt = f"Context: {context}\n\nQuestion: {user_query}"
                    
                    try:
                        # Attempt the primary model
                        response = primary_llm.invoke(prompt)
                    except Exception as primary_e:
                        print(f"⚠️ Primary model {primary_llm.model} failed! Catching error: {primary_e}")
                        print(f"🔄 Switching to fallback model: {fallback_llm.model_name}...")
                        # Fallback to the secondary model if a 429 or other API error occurs
                        response = fallback_llm.invoke(prompt)
                    
                    st.markdown("### Answer:")
                    st.info(response.content)

                    # PERMANENTLY SAVE USAGE TO CLOUD DB
                    st.session_state.query_count = auth_db.increment_query_count(st.session_state.auth_email, st.session_state.query_count)
                            
                except Exception as e:
                    st.error(f"Error: {e}")