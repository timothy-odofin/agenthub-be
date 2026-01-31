import api from "./axiosConfig";

export const login = (payload: any) =>
  api.post("/api/v1/auth/login", payload);

export const startConversationAuth = () =>
  api.get("/api/v1/auth/signup/conversation/start");

export const conversationalAuth = (payload: any) =>
  api.post("/api/v1/auth/signup/conversation", payload);
