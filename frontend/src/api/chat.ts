import api from "./axiosConfig";
import type { SendChatMessagePayload, ProvidersResponse } from "@/types";

export const createChatSession = (title?: string) =>
  api.post("/api/v1/chat/sessions", { title });

export const getChatSessions = (page: number = 1, limit: number = 20) =>
  api.get(`/api/v1/chat/sessions?page=${page}&limit=${limit}`);

export const sendChatMessage = (payload: SendChatMessagePayload) =>
  api.post("/api/v1/chat/message", payload);

export const getSessionMessages = (sessionId: string, limit: number = 50) =>
  api.get(`/api/v1/chat/sessions/${sessionId}/messages?limit=${limit}`);

export const updateSessionTitle = (sessionId: string, title: string) =>
  api.put(`/api/v1/chat/sessions/${sessionId}/title`, { title });

export const deleteSession = (sessionId: string) =>
  api.delete(`/api/v1/chat/sessions/${sessionId}`);

export const getLLMProviders = () =>
  api.get<ProvidersResponse>("/api/v1/llm/providers");
