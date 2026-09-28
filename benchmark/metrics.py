import numpy as np
from typing import List, Union

def recall_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
    """
    Tính Recall@K cho 1 truy vấn.
    Nếu có ít nhất 1 ground_truth xuất hiện trong top K retrieved_ids, trả về 1.0 (Hit), ngược lại 0.0.
    Nếu ground_truth có nhiều id, tính tỷ lệ số lượng tìm thấy / tổng số ground truth.
    """
    if not ground_truth_ids:
        return 0.0
    
    top_k_retrieved = set(retrieved_ids[:k])
    ground_truth_set = set(ground_truth_ids)
    
    # Tìm giao của 2 tập hợp
    hits = top_k_retrieved.intersection(ground_truth_set)
    return len(hits) / len(ground_truth_set)


def mrr_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
    """
    Tính Mean Reciprocal Rank (MRR) tại K cho 1 truy vấn.
    Công thức: 1 / rank (với rank là vị trí ĐẦU TIÊN chứa kết quả đúng).
    """
    if not ground_truth_ids:
        return 0.0
        
    ground_truth_set = set(ground_truth_ids)
    
    for i, doc_id in enumerate(retrieved_ids[:k]):
        if doc_id in ground_truth_set:
            return 1.0 / (i + 1)  # Vị trí (rank) bắt đầu từ 1
            
    return 0.0


def map_at_k(retrieved_ids: List[str], ground_truth_ids: List[str], k: int) -> float:
    """
    Tính Mean Average Precision (MAP) tại K cho 1 truy vấn.
    MAP trung bình cộng Precision tại mỗi điểm (rank) có kết quả đúng.
    """
    if not ground_truth_ids:
        return 0.0
        
    ground_truth_set = set(ground_truth_ids)
    hits = 0
    sum_precisions = 0.0
    
    for i, doc_id in enumerate(retrieved_ids[:k]):
        if doc_id in ground_truth_set:
            hits += 1
            precision_at_i = hits / (i + 1)
            sum_precisions += precision_at_i
            
    # Lưu ý: Chia cho số lượng ground_truths hoặc k (thường chia cho len(ground_truth))
    # Trong RAG, thường dùng len(ground_truth_set) để phạt các truy vấn không tìm đủ kết quả.
    return sum_precisions / len(ground_truth_set)


# ==========================================
# HÀM TỔNG HỢP (EVALUATOR) CHO NHIỀU TRUY VẤN
# ==========================================
def evaluate_retrieval_metrics(results: List[dict]):
    """
    Hàm tính toán tổng hợp toàn bộ các metrics cho một tập dữ liệu.
    Đầu vào `results` là một list các dictionary, mỗi dict chứa:
    {
        "retrieved": ["doc_1", "doc_3", "doc_5", ...],  # Danh sách ID các chunk máy tìm được
        "ground_truths": ["doc_3", "doc_9"]           # Danh sách ID các chunk chuẩn (đáp án)
    }
    """
    all_r10 = []
    all_r100 = []
    all_mrr10 = []
    all_map10 = []
    
    for item in results:
        retrieved = item.get("retrieved", [])
        truths = item.get("ground_truths", [])
        
        # Nếu câu hỏi này là bẫy (không có đáp án chuẩn), ta bỏ qua việc tính Retrieval
        if not truths:
            continue
            
        all_r10.append(recall_at_k(retrieved, truths, k=10))
        all_r100.append(recall_at_k(retrieved, truths, k=100))
        all_mrr10.append(mrr_at_k(retrieved, truths, k=10))
        all_map10.append(map_at_k(retrieved, truths, k=10))
        
    return {
        "R@10 (%)": round(np.mean(all_r10) * 100, 2) if all_r10 else 0,
        "R@100 (%)": round(np.mean(all_r100) * 100, 2) if all_r100 else 0,
        "MRR@10": round(np.mean(all_mrr10), 4) if all_mrr10 else 0,
        "MAP@10": round(np.mean(all_map10), 4) if all_map10 else 0
    }

# Đoạn code mô phỏng (Test)
if __name__ == "__main__":
    # GIẢ LẬP DỮ LIỆU ĐÁNH GIÁ (2 câu hỏi)
    mock_results = [
        {
            # Câu 1: Máy tìm thấy đáp án chuẩn ở vị trí số 3 (index 2)
            "retrieved": ["chunk_A", "chunk_B", "chunk_C", "chunk_D"], 
            "ground_truths": ["chunk_C"]
        },
        {
            # Câu 2: Máy tìm thấy 2 đáp án chuẩn ở vị trí số 1 và 4
            "retrieved": ["chunk_X", "chunk_Y", "chunk_Z", "chunk_W"], 
            "ground_truths": ["chunk_X", "chunk_W"]
        }
    ]
    
    print("Kết quả đánh giá:", evaluate_retrieval_metrics(mock_results))
