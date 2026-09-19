import os
from langchain_community.document_loaders import DirectoryLoader, Docx2txtLoader
from src.chunking.legal_chunker import LegalDocumentChunker

def load_and_chunk_data(base_data_dir: str):
    """
    Quét qua các thư mục con trong base_data_dir (luat, nghidinh, thongtu),
    load file .docx và cắt thành các chunk sử dụng chunker tương ứng.
    """
    all_chunks = []
    
    doc_types = ["luat", "nghidinh", "thongtu"]
    
    for doc_type in doc_types:
        folder_path = os.path.join(base_data_dir, doc_type)
        if not os.path.exists(folder_path):
            continue
            
        loader = DirectoryLoader(
            folder_path, 
            glob="**/*.docx", 
            exclude=["**/~$*.docx"],
            loader_cls=Docx2txtLoader
        )
        documents = loader.load()
        
        for doc in documents:
            doc.metadata["doc_type"] = doc_type
            
        
        chunker = LegalDocumentChunker(doc_type=doc_type)
        chunks = chunker.split_documents(documents)
        
        all_chunks.extend(chunks)
        print(f"create {len(chunks)} chunks for {doc_type}.\n")
        
    return all_chunks
