#%%
import os
import tempfile
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter



def extract_text_from_file(uploaded_file) -> list[Document]:
    """
    Extracts markdown using Docling safely in a multi-user cloud environment.
    """
    # Dynamically grab the original extension (e.g., '.docx', '.pdf')
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

    print(file_extension)
    
    # Pass that dynamic extension to the temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        temp_file_path = tmp_file.name 

    print(temp_file_path)

    try:
        converter = DocumentConverter()
        result = converter.convert(temp_file_path)
        markdown_text = result.document.export_to_markdown()
        
        final_doc = Document(
            page_content=markdown_text,
            metadata={"source": uploaded_file.name}
        )
        return [final_doc]
        
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def chunk_text(documents: list[Document]) -> list[Document]:
    from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
    
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    
    # 🚨 THE FIX: Increase the size to 2500 and overlap to 300 for academic papers
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=2500, chunk_overlap=300)
    
    final_chunks = []
    for doc in documents:
        header_splits = markdown_splitter.split_text(doc.page_content)
        sized_splits = text_splitter.split_documents(header_splits)
        
        for split in sized_splits:
            split.metadata["source"] = doc.metadata.get("source", "Unknown")
            final_chunks.append(split)
            
    return final_chunks
