export interface FileAttachment {
    name: string;
    size: number;
    type: string;
    url?: string;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    files?: FileAttachment[];
    timestamp: number;
}

export interface ChatSession {
    id: string;
    title: string;
    updatedAt: number;
    isArchived?: boolean;
}