import os
import sys
import json
import re
import time
import random
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_community.document_loaders import DirectoryLoader, Docx2txtLoader
from src.chunking.legal_chunker import LegalDocumentChunker
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    print("Vui lòng thêm GROQ_API_KEY vào file .env!")
    sys.exit(1)

# Sử dụng model gpt-oss-120b
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.7,
    groq_api_key=api_key,
    max_retries=3
) 

SYSTEM_PROMPT = """You are an advanced legal query generator with specialized skills in analyzing legal documents. When provided with an excerpt from a legal document, your task is to identify 1-5 critical aspects or implications that might interest or impact the readers. These aspects should address various dimensions of the content, focusing on rights, obligations, potential legal issues, or general legal awareness, exclusively within provided grounded content. Do not consider information in document's source for this analysis. 

For each identified critical aspect, generate a single question. These questions should reflect plausible inquiries that an average citizen might have, relating directly to the document but formulated in a manner accessible to someone unfamiliar with the presence of the legal text or information being asked about. Phrase the questions as if coming from a layperson who has not read or seen the legal text ever.

- The queries should be ones that could reasonably be answered by the information exclusively within provided grounded content only. Do not ask information in document's source.
- Each query should be one sentence only and its length is no more than 120 words.
- Try to phrase each of the question as detailed as possible, as if you haven't never seen the legal text and are trying to looking for it using keywords in the question. You should not quote the exact legal text code (like Nghị định 100/2019/NĐ-CP). The better way is to include information on the content of document like the executive body (e.g. "Cảnh sát giao thông phạt thế nào về...", "Luật Giao thông đường bộ quy định sao..."). In the case you have to refer to the legal text, use words like: "Quy định pháp luật", "Pháp luật", "Luật". Don't use the word "này".
- Present your analysis and questions in Vietnamese.

Structure your output in the JSON format below:
{{
  "aspects": [
    "[Brief description of the aspect 1]",
    "[Brief description of the aspect 2]"
  ],
  "questions": [
    "[Your question related to aspect 1 of the legal text]",
    "[Your question related to aspect 2 of the legal text]"
  ]
}}

Ensure to replace the placeholders with actual analysis and questions based on the legal text provided, and in Vietnamese. Answer with the JSON and nothing else."""

USER_PROMPT = """The following is the mentioned excerpt:
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", USER_PROMPT)
])
chain = prompt | llm

def extract_json(text):
    try:
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        data = json.loads(text.strip())
        
        qa_pairs = []
        if "aspects" in data and "questions" in data:
            aspects = data["aspects"]
            questions = data["questions"]
            for a, q in zip(aspects, questions):
                qa_pairs.append({
                    "aspect": a,
                    "question": q
                })
        return qa_pairs
    except Exception as e:
        print(f"Lỗi parse JSON: {e}")
        return []

def main():
    external_dir = os.path.join("benchmark", "data_ngoai")
    if not os.path.exists(external_dir):
        os.makedirs(external_dir)
        print(f"Đã tạo thư mục {external_dir}. Hãy copy các file .docx vào đây và chạy lại!")
        return

    # Load file docx
    loader = DirectoryLoader(
        external_dir, 
        glob="**/*.docx", 
        exclude=["**/~$*.docx"],
        loader_cls=Docx2txtLoader
    )
    documents = loader.load()
    if not documents:
        print(f"Không tìm thấy file .docx nào trong thư mục {external_dir}")
        return

    chunks = []
    for doc in documents:
        filename = doc.metadata.get("source", "").lower()
        if "nd-cp" in filename or "nd" in filename or "nghidinh" in filename or "nghị định" in filename:
            doc_type = "nghidinh"
        elif "tt" in filename or "thongtu" in filename or "thông tư" in filename:
            doc_type = "thongtu"
        else:
            doc_type = "luat"
            
        doc.metadata["doc_type"] = doc_type
        chunker = LegalDocumentChunker(doc_type=doc_type)
        chunks.extend(chunker.split_documents([doc]))
    
    
    # Chỉ lấy ngẫu nhiên một lượng nhỏ (VD: 30 chunks) làm bẫy
    NUM_TRAPS = 30
    sampled_chunks = random.sample(chunks, min(NUM_TRAPS, len(chunks)))
    print(f"Đã chọn ngẫu nhiên {len(sampled_chunks)} chunks làm bẫy để không làm loãng Benchmark.")
    
    output_file = os.path.join("benchmark", "eval_dataset.jsonl")
    
    with open(output_file, "a", encoding="utf-8") as f_out:
        for i, chunk in enumerate(sampled_chunks):
            print(f"Đang sinh dữ liệu từ luật ngoài: Chunk {i+1}/{len(sampled_chunks)}...")
            try:
                doc_source = chunk.metadata.get("source", "Nguồn ngoài")
                enriched_context = f"[Nguồn văn bản: {doc_source}]\n{chunk.page_content}"
                
                response = chain.invoke({"context": enriched_context})
                result_text = response.content if hasattr(response, 'content') else str(response)
                
                qa_list = extract_json(result_text)
                for qa in qa_list:
                    record = {
                        "chunk_source": chunk.metadata.get("source", ""),
                        "chunk_dieu": chunk.metadata.get("dieu", ""),
                        "context": chunk.page_content,
                        "aspect": qa.get("aspect", ""),
                        "question": qa.get("question", ""),
                        "is_trap": True
                    }
                    f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                
                time.sleep(4) 
                
            except Exception as e:
                print(f"[Lỗi] Chunk {i+1} thất bại: {str(e)}")
                if "429" in str(e) or "quota" in str(e).lower():
                    print("Bị Rate Limit, tạm nghỉ 15 giây...")
                    time.sleep(15)
                continue
                
    print(f"\n[Thành công] Đã nối thêm dữ liệu từ Luật Ngoài vào file: {output_file}")

if __name__ == "__main__":
    main()
