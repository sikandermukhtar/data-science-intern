import { create } from 'zustand';
import type { Message, ChatSession, FileAttachment } from '@/types/chat';

const BACKEND_URL = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8000';

interface ChatState {
    sessions: ChatSession[];
    archivedSessions: ChatSession[];
    activeSessionId: string | null;
    messages: Record<string, Message[]>;
    isLoading: boolean;
    loadingStatus: string | null;
    init: () => Promise<void>;
    fetchSessions: () => Promise<void>;
    fetchArchivedSessions: () => Promise<void>;
    setCurrentSession: (sessionId: string) => Promise<void>;
    createNewSession: () => Promise<void>;
    sendMessage: (content: string, files?: File[]) => Promise<void>;
    archiveSession: (sessionId: string) => Promise<void>;
    unarchiveSession: (sessionId: string) => Promise<void>;
    deleteSession: (sessionId: string) => Promise<void>;
}

let activeWs: WebSocket | null = null;

export const useChatStore = create<ChatState>((set, get) => {
    
    const connectWebSocket = (sessionId: string) => {
        if (activeWs) {
            activeWs.close();
            activeWs = null;
        }
        const ws = new WebSocket(`${WS_URL}/ws/chat/${sessionId}`);
        activeWs = ws;
        ws.onopen = () => {
            console.log(`WebSocket connected for session: ${sessionId}`);
        };
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const { event_type, payload } = data;
            const currentMessages = get().messages[sessionId] || [];
            switch (event_type) {
                case 'worker_spawned':
                    set({
                        isLoading: true,
                        loadingStatus: `Worker running task: ${payload.task}`
                    });
                    break;
                case 'processing':
                    set({
                        isLoading: true,
                        loadingStatus: payload.status
                    });
                    break;
                case 'code_executed':
                    const codeMsg: Message = {
                        id: `code-${Date.now()}-${Math.random()}`,
                        role: 'assistant',
                        content: `#### 💻 Running Sandbox Script\n\`\`\`python\n${payload.code}\n\`\`\`\n\n**Console Output:**\n\`\`\`\n${payload.stdout || '(No stdout)'}\n${payload.stderr ? 'STDERR:\n' + payload.stderr : ''}\n\`\`\``,
                        timestamp: Date.now()
                    };
                    const updatedWithCode = [...currentMessages, codeMsg];
                    const imageFiles = payload.files ? payload.files.filter((f: any) => f.type.startsWith('image/')) : [];
                    if (imageFiles.length > 0) {
                        const chartMsg: Message = {
                            id: `chart-${Date.now()}-${Math.random()}`,
                            role: 'assistant',
                            content: '---charts---',
                            files: imageFiles.map((f: any) => ({
                                name: f.name,
                                size: f.size,
                                type: f.type,
                                url: `${BACKEND_URL}${f.url}`
                            })),
                            timestamp: Date.now() + 100
                        };
                        updatedWithCode.push(chartMsg);
                    }
                    set((state) => ({
                        messages: {
                            ...state.messages,
                            [sessionId]: updatedWithCode
                        }
                    }));
                    break;
                case 'turn_complete':
                    const responseMsg: Message = {
                        id: `resp-${Date.now()}`,
                        role: 'assistant',
                        content: payload.content,
                        timestamp: Date.now()
                    };
                    const updatedMessages = [...(get().messages[sessionId] || []), responseMsg];
                    const finalImages = payload.files ? payload.files.filter((f: any) => f.type.startsWith('image/')) : [];
                    if (finalImages.length > 0) {
                        const chartMsg: Message = {
                            id: `chart-final-${Date.now()}`,
                            role: 'assistant',
                            content: '---charts---',
                            files: finalImages.map((f: any) => ({
                                name: f.name,
                                size: f.size,
                                type: f.type,
                                url: `${BACKEND_URL}${f.url}`
                            })),
                            timestamp: Date.now() + 100
                        };
                        updatedMessages.push(chartMsg);
                    }
                    set((state) => ({
                        messages: {
                            ...state.messages,
                            [sessionId]: updatedMessages
                        },
                        isLoading: false,
                        loadingStatus: null
                    }));
                    // Refresh session titles/timestamps
                    get().fetchSessions();
                    break;
                case 'error':
                    const errorMsg: Message = {
                        id: `err-${Date.now()}`,
                        role: 'assistant',
                        content: `❌ **Pipeline Error**\n\`\`\`\n${payload.message}\n\`\`\`\n*Details:*\n\`\`\`\n${payload.details || ''}\n\`\`\``,
                        timestamp: Date.now()
                    };
                    set((state) => ({
                        messages: {
                            ...state.messages,
                            [sessionId]: [...(state.messages[sessionId] || []), errorMsg]
                        },
                        isLoading: false,
                        loadingStatus: null
                    }));
                    break;
                default:
                    break;
            }
        };
        ws.onclose = () => {
            console.log(`WebSocket closed for session: ${sessionId}`);
        };
        ws.onerror = (err) => {
            console.error('WebSocket error:', err);
        };
    };

    return {
        sessions: [],
        archivedSessions: [],
        activeSessionId: null,
        messages: {},
        isLoading: false,
        loadingStatus: null,

        fetchSessions: async () => {
            try {
                const res = await fetch(`${BACKEND_URL}/api/sessions`);
                const sessions = await res.json();
                set({ sessions });
            } catch (err) {
                console.error('Failed to fetch sessions:', err);
            }
        },

        fetchArchivedSessions: async () => {
            try {
                const res = await fetch(`${BACKEND_URL}/api/sessions?archived_only=true`);
                const archivedSessions = await res.json();
                set({ archivedSessions });
            } catch (err) {
                console.error('Failed to fetch archived sessions:', err);
            }
        },

        init: async () => {
            try {
                await get().fetchSessions();
                await get().fetchArchivedSessions();
                const { sessions } = get();
                if (sessions.length > 0) {
                    await get().setCurrentSession(sessions[0].id);
                } else {
                    await get().createNewSession();
                }
            } catch (err) {
                console.error('Failed to initialize chat store:', err);
            }
        },

        setCurrentSession: async (sessionId) => {
            set({ activeSessionId: sessionId });
            
            try {
                const res = await fetch(`${BACKEND_URL}/api/sessions/${sessionId}/messages`);
                const backendMessages = await res.json();
                const formattedMessages: Message[] = backendMessages
                    .filter((m: any) => m.role !== 'system')
                    .map((msg: any, index: number) => ({
                        id: msg.id || `msg-${index}-${Date.now()}`,
                        role: msg.role,
                        content: msg.content,
                        files: msg.files ? msg.files.map((f: any) => ({
                            ...f,
                            url: f.url ? (f.url.startsWith('http') ? f.url : `${BACKEND_URL}${f.url}`) : undefined
                        })) : undefined,
                        timestamp: msg.timestamp || Date.now()
                    }));
                set((state) => ({
                    messages: {
                        ...state.messages,
                        [sessionId]: formattedMessages
                    }
                }));
                connectWebSocket(sessionId);
            } catch (err) {
                console.error(`Failed to load messages for session ${sessionId}:`, err);
            }
        },

        createNewSession: async () => {
            try {
                const res = await fetch(`${BACKEND_URL}/api/sessions`, { method: 'POST' });
                const { id } = await res.json();
                const newSession: ChatSession = {
                    id,
                    title: 'New Session',
                    updatedAt: Date.now()
                };
                set((state) => ({
                    sessions: [newSession, ...state.sessions],
                    activeSessionId: id,
                    messages: {
                        ...state.messages,
                        [id]: []
                    }
                }));
                connectWebSocket(id);
            } catch (err) {
                console.error('Failed to create new session:', err);
            }
        },

        archiveSession: async (sessionId: string) => {
            try {
                await fetch(`${BACKEND_URL}/api/sessions/${sessionId}/archive`, { method: 'POST' });
                await get().fetchSessions();
                await get().fetchArchivedSessions();

                // If currently viewing the session that just got archived, switch to next active session
                const { activeSessionId, sessions } = get();
                if (activeSessionId === sessionId) {
                    if (sessions.length > 0) {
                        await get().setCurrentSession(sessions[0].id);
                    } else {
                        await get().createNewSession();
                    }
                }
            } catch (err) {
                console.error(`Failed to archive session ${sessionId}:`, err);
            }
        },

        unarchiveSession: async (sessionId: string) => {
            try {
                await fetch(`${BACKEND_URL}/api/sessions/${sessionId}/unarchive`, { method: 'POST' });
                await get().fetchSessions();
                await get().fetchArchivedSessions();
            } catch (err) {
                console.error(`Failed to unarchive session ${sessionId}:`, err);
            }
        },

        deleteSession: async (sessionId: string) => {
            try {
                await fetch(`${BACKEND_URL}/api/sessions/${sessionId}`, { method: 'DELETE' });

                // Remove from messages cache
                set((state) => {
                    const updatedMessages = { ...state.messages };
                    delete updatedMessages[sessionId];
                    return { messages: updatedMessages };
                });

                await get().fetchSessions();
                await get().fetchArchivedSessions();

                // If currently viewing the deleted session, switch or create new
                const { activeSessionId, sessions } = get();
                if (activeSessionId === sessionId) {
                    if (sessions.length > 0) {
                        await get().setCurrentSession(sessions[0].id);
                    } else {
                        await get().createNewSession();
                    }
                }
            } catch (err) {
                console.error(`Failed to delete session ${sessionId}:`, err);
            }
        },

        sendMessage: async (content, files) => {
            const { activeSessionId, messages } = get();
            if (!activeSessionId) return;
            const sessionMessages = messages[activeSessionId] || [];
            
            const uploadedFiles: FileAttachment[] = [];
            if (files && files.length > 0) {
                set({ isLoading: true, loadingStatus: 'Uploading files...' });
                for (const file of files) {
                    const formData = new FormData();
                    formData.append('file', file);
                    try {
                        const res = await fetch(`${BACKEND_URL}/api/sessions/${activeSessionId}/upload`, {
                            method: 'POST',
                            body: formData
                        });
                        const data = await res.json();
                        uploadedFiles.push({
                            name: data.filename,
                            size: data.size,
                            type: file.type,
                            url: `/static/${activeSessionId}/${data.filename}`
                        });
                    } catch (err) {
                        console.error(`Failed to upload file ${file.name}:`, err);
                    }
                }
            }
            const userMsg: Message = {
                id: `u-${Date.now()}`,
                role: 'user',
                content,
                files: uploadedFiles.length > 0 ? uploadedFiles : undefined,
                timestamp: Date.now()
            };
            set((state) => ({
                messages: {
                    ...state.messages,
                    [activeSessionId]: [...sessionMessages, userMsg]
                },
                isLoading: true,
                loadingStatus: 'Sending message...'
            }));
            if (activeWs && activeWs.readyState === WebSocket.OPEN) {
                activeWs.send(JSON.stringify({
                    type: 'message',
                    content,
                    files: uploadedFiles.length > 0 ? uploadedFiles : undefined
                }));
            } else {
                console.error('WebSocket connection is not active');
                set({ isLoading: false, loadingStatus: null });
            }
        }
    };
});
