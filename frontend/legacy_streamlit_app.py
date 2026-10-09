import streamlit as st
import requests

st.set_page_config(
    page_title="RAG Pháp luật Giao thông 🇻🇳",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ Trợ lý ảo Luật Giao thông VN")
st.caption("🚀 Hệ thống RAG sử dụng FastAPI + Qdrant + LLM")

API_URL = "http://localhost:8000/api/chat/stream"

# Khởi tạo lịch sử trò chuyện trong bộ nhớ
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "Xin chào! Tôi là trợ lý ảo am hiểu Luật Giao thông đường bộ Việt Nam. Tôi có thể giúp gì cho bạn hôm nay?"
    })

# Hiển thị lại lịch sử
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Xử lý khi user gửi câu hỏi
if prompt := st.chat_input("Nhập câu hỏi pháp lý của bạn vào đây..."):
    
    # 1. In câu hỏi của user
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. In câu trả lời của Bot (Hiệu ứng gõ chữ Streaming)
    with st.chat_message("assistant"):
        try:
            with st.spinner("⏳ Đang xử lý..."):
                # Bật stream=True để hứng từng chữ
                response = requests.post(API_URL, json={"question": prompt}, stream=True)
                
                if response.status_code == 200:
                    # Lấy luồng dữ liệu
                    iterator = response.iter_content(chunk_size=1024, decode_unicode=True)
                    try:
                        # Chờ lấy chữ cái đầu tiên (Đây là lúc LLM suy nghĩ lâu nhất)
                        first_chunk = next(iterator)
                    except StopIteration:
                        first_chunk = ""
            
            if response.status_code == 200:
                # Hàm sinh từng mảnh chữ
                def generate_chunks():
                    if first_chunk:
                        yield first_chunk
                    for chunk in iterator:
                        if chunk:
                            yield chunk
                
                # Streamlit sẽ tự động in từng chữ ra màn hình
                answer = st.write_stream(generate_chunks())
            else:
                answer = f"Lỗi Server: {response.text}"
                st.markdown(answer)
                
        except requests.exceptions.ConnectionError:
            answer = "Lỗi: Không thể kết nối. Hãy đảm bảo bạn đã mở 1 terminal khác và chạy `python main.py`."
            st.markdown(answer)
            
    # 3. Lưu lại câu trả lời vào lịch sử
    st.session_state.messages.append({"role": "assistant", "content": answer})
