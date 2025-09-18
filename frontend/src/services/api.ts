import axios from 'axios';
import { ChatRequest, ChatResponse } from '../types/chat';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatService = {
  sendMessage: async (message: string): Promise<ChatResponse> => {
    const request: ChatRequest = { message };
    const response = await apiClient.post('/api/chat', request);
    return response.data;
  },

  healthCheck: async (): Promise<{ status: string }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  getKnowledgeBaseStats: async (): Promise<any> => {
    const response = await apiClient.get('/api/knowledge-base/stats');
    return response.data;
  },
};

export default chatService;