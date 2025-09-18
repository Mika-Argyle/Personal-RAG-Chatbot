// TypeScript interfaces matching backend models
export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  response: string;
  context_used?: boolean;
  sources?: string[];
}

export interface Message {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  contextUsed?: boolean;
  sources?: string[];
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}