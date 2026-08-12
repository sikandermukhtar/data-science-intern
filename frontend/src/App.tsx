import { useEffect } from 'react'
import { useChatStore } from '@/store/useChatStore'
import './App.css'
import MainLayout from "@/components/layout/MainLayout";
import ChatContainer from "@/components/chat/ChatContainer";

function App() {
  const init = useChatStore((state) => state.init);

  useEffect(() => {
    init();
  }, [init]);

  return (
    <>
      <MainLayout>
        <ChatContainer />
      </MainLayout>
    </>
  );
}

export default App;