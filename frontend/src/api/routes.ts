import api from "./axiosConfig";
import type { RouteRegistryEntry } from "@/routes/registry";

/** GET /api/v1/routes — fetch currently synced routes from the backend */
export const getRoutes = () => api.get("/api/v1/routes");

/** POST /api/v1/routes/sync — push routes from frontend registry to backend */
export const syncRoutes = (routes: RouteRegistryEntry[]) =>
  api.post("/api/v1/routes/sync", { routes });

/** POST /api/v1/routes/action-completed — notify backend an action was executed */
export const notifyActionCompleted = (payload: {
  action_type: string;
  action_name?: string;
  success: boolean;
  result?: Record<string, any>;
  session_id?: string;
  message?: string;
}) => api.post("/api/v1/routes/action-completed", payload);
