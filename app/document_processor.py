#%%
import pandas as pd
import fitz

from langchain_text_splitters import RecursiveCharacterTextSplitter

def extract_text_from_file(uploaded_file)->str:
    """
    Extract text from a PDF file.
    """
    extracted_text  = ""
    file_extension = uploaded_file.name.lower()
    if file_extension.endswith(".pdf"):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        for page in doc:
            extracted_text += page.get_text()

    elif file_extension.endswith(".txt"):
        extracted_text = uploaded_file.read().decode("utf-8")

    elif file_extension.endswith(".xlsx"):
        df = pd.read_excel(uploaded_file)
        extracted_text = df.to_string()

    else:
        return "Unsupported file type"
        
    return extracted_text


def chunk_text(text)->list[str]:
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    return chunks.split_text(text)

if __name__ == '__main__':
    # Change this variable to test your different files (test.txt, test.pdf, test.xlsx)
    test_filename = "native.pdf" 
    
    print(f"\n========== TESTING: {test_filename} ==========")

    # 1. We create a "Mock" class to pretend to be a Streamlit file
    class MockUploadedFile:
        def __init__(self, filepath):
            self.name = filepath
            # Read the bytes into memory immediately
            with open(filepath, "rb") as f:
                self.bytes_data = f.read()
        
        def read(self):
            # When the function calls .read(), we hand it the bytes
            return self.bytes_data

    try:
        # 2. Initialize our fake Streamlit file
        fake_uploaded_file = MockUploadedFile(test_filename)
        
        # --- TEST 1: EXTRACTION ---
        print("\n--- Phase 1: Extraction ---")
        raw_text = extract_text_from_file(fake_uploaded_file)
        print(f"SUCCESS: Extracted {len(raw_text)} characters.")
        print("Preview of first 100 characters:")
        print(repr(raw_text[:100])) 
        
        # --- TEST 2: CHUNKING ---
        print("\n--- Phase 2: Chunking ---")
        chunks = chunk_text(raw_text)
        print(f"SUCCESS: Split text into {len(chunks)} chunks.")
        
        if len(chunks) > 0:
            print("\nPreview of Chunk 1:")
            print("-" * 40)
            print(chunks[0])
            print("-" * 40)
            
    except FileNotFoundError:
        print(f"ERROR: Could not find '{test_filename}' in the folder. Did you create it?")
    except Exception as e:
        print(f"ERROR: Something broke! The error is: {e}")