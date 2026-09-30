import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { historyAPI } from '../services/api';
import { streamChatResponse } from '../services/sse';
import { useAuth } from './AuthContext';

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [loadingSession, setLoadingSession] = useState(false);
  const abortControllerRef = useRef(null);

  // Load sessions whenever authentication state changes
  useEffect(() => {
    if (isAuthenticated) {
      loadSessions();
    } else {
      setSessions([]);
      setActiveSessionId(null);
      setMessages([]);
    }
  }, [isAuthenticated]);

  const loadSessions = async () => {
    try {
      const data = await historyAPI.getSessions();
      setSessions(data);
    } catch (err) {
      console.error('Failed to load chat sessions:', err);
    }
  };

  const selectSession = async (sessionId) => {
    if (isStreaming) return; // Prevent switching while receiving stream
    setLoadingSession(true);
    try {
      const data = await historyAPI.getSession(sessionId);
      setActiveSessionId(sessionId);
      setMessages(data.messages || []);
    } catch (err) {
      console.error('Failed to load session details:', err);
    } finally {
      setLoadingSession(false);
    }
  };

  const createNewChat = () => {
    if (isStreaming && abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setActiveSessionId(null);
    setMessages([]);
  };

  const deleteSession = async (sessionId) => {
    try {
      await historyAPI.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => (s.session_id || s.id) !== sessionId));
      if (activeSessionId === sessionId) {
        createNewChat();
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const sendMessage = async (queryText) => {
    if (!queryText.trim() || isStreaming) return;

    const userMsg = {
      id: 'usr_' + Date.now(),
      role: 'user',
      content: queryText.trim(),
      created_at: new Date().toISOString(),
    };

    const aiMsgPlaceholder = {
      id: 'ai_' + Date.now(),
      role: 'ai',
      content: '',
      citations: [],
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg, aiMsgPlaceholder]);
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    let currentSessionId = activeSessionId;

    await streamChatResponse({
      query: queryText.trim(),
      sessionId: currentSessionId,
      signal: controller.signal,
      onSession: (sessionData) => {
        if (!currentSessionId && sessionData?.session_id) {
          currentSessionId = sessionData.session_id;
          setActiveSessionId(currentSessionId);
          // If authenticated, refresh sessions list
          if (isAuthenticated) {
            loadSessions();
          }
        }
      },
      onDelta: (textChunk) => {
        setMessages((prev) => {
          if (prev.length === 0) return prev;
          const next = [...prev];
          const lastIdx = next.length - 1;
          if (next[lastIdx].role === 'ai') {
            next[lastIdx] = {
              ...next[lastIdx],
              content: next[lastIdx].content + textChunk,
            };
          }
          return next;
        });
      },
      onCitations: (citationsList) => {
        setMessages((prev) => {
          if (prev.length === 0) return prev;
          const next = [...prev];
          const lastIdx = next.length - 1;
          if (next[lastIdx].role === 'ai') {
            next[lastIdx] = {
              ...next[lastIdx],
              citations: citationsList,
            };
          }
          return next;
        });
      },
      onDone: () => {
        setIsStreaming(false);
        abortControllerRef.current = null;
        if (isAuthenticated) {
          loadSessions();
        }
      },
      onError: (err) => {
        console.error('Chat stream error:', err);
        setMessages((prev) => {
          if (prev.length === 0) return prev;
          const next = [...prev];
          const lastIdx = next.length - 1;
          if (next[lastIdx].role === 'ai') {
            next[lastIdx] = {
              ...next[lastIdx],
              content:
                next[lastIdx].content +
                '\n\n*(Lưu ý: Không thể hoàn tất phản hồi hoặc mất kết nối máy chủ.)*',
            };
          }
          return next;
        });
        setIsStreaming(false);
        abortControllerRef.current = null;
      },
    });
  };

  const value = {
    sessions,
    activeSessionId,
    messages,
    isStreaming,
    loadingSession,
    loadSessions,
    selectSession,
    createNewChat,
    deleteSession,
    sendMessage,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
