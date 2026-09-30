import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import uuid
from fastapi.testclient import TestClient
from main import app
from src.api.dependencies import rag_components

# Mock RAG chain if not loaded
if "chain" not in rag_components:
    class MockDoc:
        page_content = "Khoản 4 Điều 6 Nghị định 100/2019/NĐ-CP: Phạt tiền từ 800.000 đồng đến 1.000.000 đồng đối với người điều khiển xe mô tô, xe gắn máy không chấp hành hiệu lệnh của đèn tín hiệu giao thông."
        metadata = {
            "source": "Nghị định 100/2019/NĐ-CP",
            "dieu": "6",
            "khoan": "4",
            "diem": "e",
            "document_name": "Nghị định 100/2019/NĐ-CP",
        }

    class MockChain:
        def stream(self, inputs):
            yield "Theo quy định tại Điểm e Khoản 4 Điều 6 Nghị định 100/2019/NĐ-CP, hành vi vượt đèn đỏ đối với xe máy bị phạt tiền từ 800.000 đồng đến 1.000.000 đồng."

        class retriever:
            @staticmethod
            def invoke(query):
                return [MockDoc()]

    rag_components["chain"] = MockChain()
    rag_components["process"] = lambda inputs: {
        "context": "Khoản 4 Điều 6 Nghị định 100/2019/NĐ-CP",
        "input": inputs.get("input", "") if isinstance(inputs, dict) else str(inputs),
        "citations": [
            {
                "source": "Nghị định 100/2019/NĐ-CP",
                "dieu": "6",
                "khoan": "4",
                "diem": "e",
                "content": "Phạt tiền từ 800.000 đồng đến 1.000.000 đồng đối với xe mô tô vượt đèn đỏ.",
            }
        ],
    }

client = TestClient(app)

def test_static_frontend_serving():
    """Verify that root endpoint serves the built React SPA"""
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "Tra cứu Luật Giao thông Việt Nam" in response.text
    assert '<div id="root"></div>' in response.text
    print("✅ Static frontend root serving passed!")

def test_full_auth_and_chat_flow():
    """Verify Register -> Login -> Me -> Session -> Chat Stream -> History -> Delete Session"""
    unique_user = f"user_{int(time.time())}_{uuid.uuid4().hex[:4]}"
    pwd = "SecurePassword123"

    # 1. Register
    reg_res = client.post("/api/auth/register", json={"username": unique_user, "password": pwd})
    assert reg_res.status_code == 201, f"Register failed: {reg_res.text}"
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Register passed!")

    # 2. Login
    login_res = client.post("/api/auth/login", json={"username": unique_user, "password": pwd})
    assert login_res.status_code == 200
    print("✅ Login passed!")

    # 3. Get Me
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == unique_user
    print("✅ Get current user info passed!")

    # 4. Create Chat Session
    sess_res = client.post("/api/sessions", json={"title": "Kiểm tra mức phạt vượt đèn đỏ"}, headers=headers)
    assert sess_res.status_code == 201
    session_id = sess_res.json()["session_id"]
    print(f"✅ Created session {session_id} passed!")

    # 5. Chat Stream
    stream_res = client.post(
        "/api/chat/stream",
        json={"query": "Xe máy vượt đèn đỏ phạt bao nhiêu?", "session_id": session_id},
        headers=headers,
    )
    assert stream_res.status_code == 200, f"Status: {stream_res.status_code}, Body: {stream_res.text}"
    content = stream_res.text
    assert "event: session" in content
    assert "event: delta" in content
    assert "event: citations" in content
    assert "event: done" in content
    print("✅ SSE Chat Stream with citations passed!")

    # 6. Check Session History Messages
    hist_res = client.get(f"/api/sessions/{session_id}", headers=headers)
    assert hist_res.status_code == 200
    messages = hist_res.json()["messages"]
    assert len(messages) >= 2, f"Expected at least 2 messages (user + ai), got {len(messages)}"
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "ai"
    assert messages[1]["citations"] is not None
    print(f"✅ History messages retrieved with citations count: {len(messages[1]['citations'])}")

    # 7. Delete Session
    del_res = client.delete(f"/api/sessions/{session_id}", headers=headers)
    assert del_res.status_code == 200
    print("✅ Delete session passed!")

    # 8. Logout
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    print("✅ Logout passed!")

if __name__ == '__main__':
    test_static_frontend_serving()
    test_full_auth_and_chat_flow()
    print("\n🎉 ALL END-TO-END TESTS PASSED SUCCESSFULLY! 🎉")
