import re
from typing import List
from langchain_core.documents import Document

# Các Regex định dạng pháp luật

# Điều / Phụ lục / Phần / Chương (Tầng 1)
RE_DIEU   = re.compile(r"^(?:##\s*)?(Điều\s+\d+|Phụ\s*lục\s*[A-Z0-9]*|Phần\s+[A-ZIVXLCDM]+|Chương\s+[A-ZIVXLCDM\d]+)[.:]?\s*(.*)", re.IGNORECASE)

# Khoản: dòng bắt đầu bằng số + dấu chấm + chữ hoa
RE_KHOAN  = re.compile(r"^(\d+)\.(?=\s+[A-ZĐÀÁẠẢÃẮẰẲẴẶẤẦẨẪẬÉÈẺẼẸẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌỐỒỔỖỘỚỜỞỠỢÚÙỦŨỤỨỪỬỮỰÝỲỶỸỴ])", re.MULTILINE)

# Điểm: "a) ..." / "đ) ..."
RE_DIEM   = re.compile(r"(?:^|;\s+)([a-zđ])\)(?=\s+)", re.MULTILINE)

from src.utils.config import THRESH_DIEU, THRESH_KHOAN_DEFAULT, MIN_CHUNK, MIN_CHUNK_DIEM

def count_tokens(text: str) -> int:
    # 1 tu tieng viet = 1.3 token
    words = len(text.split())
    return int(words * 1.3)

def apply_legal_styling(text: str) -> str:
    # Bold mức phạt tiền
    text = re.sub(
        r'(phạt tiền từ\s+[\d.,]+\s+đồng\s+đến\s+[\d.,]+\s+đồng)',
        r'**\1**', text, flags=re.IGNORECASE
    )
    # Bold tước quyền sử dụng GPLX
    text = re.sub(
        r'(tước quyền sử dụng[^.;]{5,80}tháng)',
        r'**\1**', text, flags=re.IGNORECASE
    )
    # Tránh lồng **
    text = re.sub(r'\*{4,}', '**', text)
    return text

class LegalDocumentChunker:
    # Hierarchical Semantic Chunking
    def __init__(self, doc_type: str):
        self.doc_type = doc_type

    def split_documents(self, documents: List[Document]) -> List[Document]:
        chunks = []
        for doc in documents:
            text = doc.page_content
            metadata = doc.metadata.copy()
            chunks.extend(self._chunk_document(text, metadata))
        return chunks

    def _split_into_articles(self, full_text: str):
        articles = []
        lines = full_text.splitlines()

        current_num = "0"
        current_title = "Phần giới thiệu"
        current_lines = []

        for line in lines:
            m = RE_DIEU.match(line.strip())
            if m:
                if current_lines:
                    articles.append((current_num, current_title, "\n".join(current_lines)))
                current_num = m.group(1)
                current_title = m.group(2).strip()
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            articles.append((current_num, current_title, "\n".join(current_lines)))

        return articles

    def _split_article_into_khoans(self, text: str):
        parts = RE_KHOAN.split(text)
        khoans = []

        if len(parts) <= 1:
            return [("0", text)]

        if parts[0].strip():
            khoans.append(("0", parts[0].strip()))

        i = 1
        while i + 1 < len(parts):
            khoan_num = parts[i]
            content = parts[i + 1]
            khoans.append((khoan_num, f"{khoan_num}.{content}"))
            i += 2

        return khoans if khoans else [("0", text)]

    def _split_khoan_into_diems(self, text: str):
        parts = RE_DIEM.split(text)
        diems = []

        if len(parts) <= 1:
            return [("", text)]

        # Câu dẫn của Khoản (ví dụ: "Phạt tiền 1 triệu đối với...")
        preamble = parts[0].strip() if parts[0].strip() else ""
        if preamble:
            diems.append(("", preamble))

        i = 1
        while i + 1 < len(parts):
            label = parts[i]
            content = parts[i + 1]
            diem_body = f"{label}){content}".strip()
            
            # Context Enrichment: Nối phần câu dẫn của Khoản vào đầu Điểm
            # Giúp cho 1 chunk nhỏ gọn vẫn có đủ ngữ cảnh "phạt bao nhiêu"
            if preamble:
                enriched = f"{preamble}\n{diem_body}"
            else:
                enriched = diem_body
                
            diems.append((label, enriched))
            i += 2

        return diems if diems else [("", text)]

    def _chunk_document(self, full_text: str, doc_meta: dict) -> List[Document]:
        articles = self._split_into_articles(full_text)
        chunks = []

        ten_van_ban = doc_meta.get("source", "Không rõ nguồn").split("/")[-1]

        for dieu_num, dieu_title, dieu_content in articles:
            if count_tokens(dieu_content) < MIN_CHUNK:
                continue

            if count_tokens(dieu_content) <= THRESH_DIEU:
                # Level 1: Cả Điều là 1 chunk
                chunk = self._make_document(dieu_content, doc_meta, dieu_num, dieu_title, None, None, ten_van_ban)
                chunks.append(chunk)
            else:
                # Level 2: Cắt xuống Khoản
                khoans = self._split_article_into_khoans(dieu_content)
                for khoan_num, khoan_content in khoans:
                    if count_tokens(khoan_content) < MIN_CHUNK:
                        continue
                    
                    # Cắt xuống Điểm (Level 3) CHỈ KHI Khoản đó quá dài (vượt ngưỡng THRESH_KHOAN_DEFAULT)
                    # Loại bỏ logic bắt buộc cắt nát Nghị định để bảo toàn ngữ cảnh
                    should_split_l3 = count_tokens(khoan_content) > THRESH_KHOAN_DEFAULT

                    if not should_split_l3:
                        chunk = self._make_document(khoan_content, doc_meta, dieu_num, dieu_title, khoan_num, None, ten_van_ban)
                        chunks.append(chunk)
                    else:
                        # Level 3: Cắt xuống Điểm
                        diems = self._split_khoan_into_diems(khoan_content)
                        for diem_label, diem_content in diems:
                            if count_tokens(diem_content) < MIN_CHUNK_DIEM:
                                continue
                            chunk = self._make_document(diem_content, doc_meta, dieu_num, dieu_title, khoan_num, diem_label, ten_van_ban)
                            chunks.append(chunk)
        return chunks

    def _make_document(self, text, doc_meta, dieu_num, dieu_title, khoan_num, diem_label, ten_van_ban):
        content = apply_legal_styling(text)
        
        # Context Enrichment (Thêm thông tin Nguồn + Điều vào đầu văn bản)
        if dieu_num and dieu_num != "0":
            context_line = f"Văn bản: {ten_van_ban} | {dieu_num}: {dieu_title}"
            if not content.startswith(context_line):
                content = f"{context_line}\n{content}"
        
        meta = doc_meta.copy()
        meta["dieu"] = dieu_num
        if khoan_num and khoan_num != "0":
            meta["khoan"] = khoan_num
        if diem_label:
            meta["diem"] = diem_label

        return Document(page_content=content, metadata=meta)
