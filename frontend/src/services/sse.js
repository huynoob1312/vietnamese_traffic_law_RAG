/**
 * Utility function to consume Server-Sent Events (SSE) from the RAG backend stream
 */
export async function streamChatResponse({
  query,
  sessionId = null,
  onSession,
  onDelta,
  onCitations,
  onDone,
  onError,
  signal,
}) {
  const token = localStorage.getItem('traffic_law_token');
  const headers = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch('/api/chat/stream', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        query,
        session_id: sessionId || undefined,
      }),
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text();
      let errorMsg = `Lỗi hệ thống (${response.status})`;
      try {
        const errorJson = JSON.parse(errorText);
        errorMsg = errorJson.detail || errorMsg;
      } catch {
        // fallback
      }
      throw new Error(errorMsg);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split('\n\n');
      buffer = blocks.pop() || '';

      for (const block of blocks) {
        if (!block.trim()) continue;

        const lines = block.split('\n');
        let eventType = 'message';
        let dataStr = '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventType = line.replace('event:', '').trim();
          } else if (line.startsWith('data:')) {
            dataStr = line.replace('data:', '').trim();
          }
        }

        if (dataStr) {
          try {
            const parsed = JSON.parse(dataStr);
            if (eventType === 'session') {
              onSession?.(parsed);
            } else if (eventType === 'delta') {
              onDelta?.(parsed.content || parsed.text || '');
            } else if (eventType === 'citations') {
              onCitations?.(parsed);
            } else if (eventType === 'done') {
              onDone?.(parsed);
            }
          } catch (e) {
            console.error('Failed to parse SSE JSON:', dataStr, e);
          }
        }
      }
    }
  } catch (err) {
    if (err.name === 'AbortError') {
      console.log('Stream request aborted');
    } else {
      onError?.(err);
    }
  }
}
