import React, { useEffect, useRef } from 'react';
import { useChat } from '../context/ChatContext';
import SearchInput from './SearchInput';
import CitationCard from './CitationCard';
import { Sparkles, User, Bot } from 'lucide-react';

const SUGGESTIONS = [
  'Mức phạt không đội mũ bảo hiểm xe máy là bao nhiêu?',
  'Nồng độ cồn kịch khung với ô tô bị phạt tiền và tước bằng lái thế nào?',
  'Lỗi vượt đèn đỏ đối với xe máy phạt bao nhiêu tiền?',
  'Quên mang Giấy đăng ký xe máy bị xử phạt ra sao?',
];

export default function ChatArea() {
  const { messages, isStreaming, sendMessage } = useChat();
  const messagesEndRef = useRef(null);

  // Auto scroll down when messages change or streaming
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  const isEmpty = messages.length === 0;

  return (
    <main className="flex-1 flex flex-col h-screen overflow-hidden bg-aged-paper relative">
      {isEmpty ? (
        /* Empty State / Hero Home View */
        <div className="flex-1 flex flex-col justify-center items-center px-4 overflow-y-auto">
          <div className="w-full max-w-content text-center mb-8">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-pill bg-white border border-pebble shadow-subtle mb-4 text-xs text-charcoal font-medium">
              <Sparkles size={13} className="text-deep-teal" />
              <span>Hệ thống RAG Pháp Lý Giao Thông</span>
            </div>
            <h1 className="text-2xl font-medium tracking-tight text-charcoal mb-2">
              Tra cứu Luật Giao thông Việt Nam
            </h1>
            <p className="text-sm text-ash-gray max-w-md mx-auto leading-relaxed">
              Truy vấn chính xác theo Luật Đường bộ số 35/2024/QH15 và Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15 kèm căn cứ Điều, Khoản cụ thể.
            </p>
          </div>

          <div className="w-full max-w-content mb-8">
            <SearchInput
              onSend={sendMessage}
              isStreaming={isStreaming}
              placeholder="Đặt câu hỏi về luật, mức phạt, tình huống giao thông..."
            />
          </div>

          {/* Quick suggestion pills */}
          <div className="w-full max-w-content">
            <div className="text-[11px] font-medium text-stone uppercase tracking-wider mb-2.5 text-center">
              Gợi ý câu hỏi phổ biến
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {SUGGESTIONS.map((text, idx) => (
                <button
                  key={idx}
                  onClick={() => sendMessage(text)}
                  className="text-left p-3 rounded-card bg-white hover:bg-subtle-fill border border-pebble text-xs text-charcoal transition-all shadow-subtle hover:border-deep-teal/40"
                >
                  {text}
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        /* Conversation Message Thread */
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 overflow-y-auto px-4 py-6">
            <div className="w-full max-w-content mx-auto space-y-6">
              {messages.map((msg, index) => {
                const isUser = msg.role === 'user';
                const isLastAi = !isUser && index === messages.length - 1;
                const isThinking = isLastAi && isStreaming && !msg.content;

                return (
                  <div key={msg.id || index} className="space-y-1.5 animate-in fade-in duration-150">
                    {/* Header: role indicator */}
                    <div className="flex items-center gap-1.5 text-xs text-stone">
                      {isUser ? (
                        <>
                          <User size={13} className="text-charcoal" />
                          <span className="font-medium text-charcoal">Bạn</span>
                        </>
                      ) : (
                        <>
                          <Bot size={13} className="text-deep-teal" />
                          <span className="font-medium text-charcoal">Trợ lý Pháp lý AI</span>
                        </>
                      )}
                    </div>

                    {/* Message Bubble/Content */}
                    {isUser ? (
                      <div className="p-3.5 bg-white rounded-card border border-pebble shadow-subtle text-sm text-charcoal leading-relaxed whitespace-pre-wrap">
                        {msg.content}
                      </div>
                    ) : (
                      <div className="p-4 bg-white rounded-card border border-pebble shadow-subtle text-sm text-charcoal leading-relaxed">
                        {isThinking ? (
                          /* Skeleton shimmer placeholder as defined in DESIGN.md */
                          <div className="space-y-2 py-1">
                            <div className="h-2.5 bg-skeleton-bar rounded-pill animate-shimmer w-3/4" />
                            <div className="h-2.5 bg-skeleton-bar rounded-pill animate-shimmer w-full" />
                            <div className="h-2.5 bg-skeleton-bar rounded-pill animate-shimmer w-5/6" />
                          </div>
                        ) : (
                          <div className="whitespace-pre-wrap space-y-2 font-normal">
                            {msg.content}
                            {isLastAi && isStreaming && (
                              <span className="inline-block w-1.5 h-4 ml-1 bg-deep-teal align-middle animate-pulse" />
                            )}
                          </div>
                        )}

                        {/* Citations Drawer */}
                        {msg.citations && msg.citations.length > 0 && (
                          <CitationCard citations={msg.citations} />
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Sticky Bottom Search Bar */}
          <div className="p-4 bg-aged-paper border-t border-pebble/40 shrink-0">
            <SearchInput
              onSend={sendMessage}
              isStreaming={isStreaming}
              placeholder="Đặt câu hỏi tiếp theo..."
            />
          </div>
        </div>
      )}
    </main>
  );
}
