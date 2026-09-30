import React, { useState } from 'react';
import { AuthProvider } from './context/AuthContext';
import { ChatProvider } from './context/ChatContext';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import AuthModal from './components/AuthModal';

function AppContent() {
  const [authModalOpen, setAuthModalOpen] = useState(false);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-aged-paper text-charcoal font-pplxSans">
      <Sidebar onOpenAuth={() => setAuthModalOpen(true)} />
      <ChatArea />
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ChatProvider>
        <AppContent />
      </ChatProvider>
    </AuthProvider>
  );
}
