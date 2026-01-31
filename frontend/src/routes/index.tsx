import type { RouteObject } from "react-router-dom";
import ModernLogin from "@/pages/ModernLogin";
import ProtectedRoute from "@/middleware/ProtectedRoute";
import ChatLayout from "@/pages/ChatLayout";
import ConversationalSignup from "@/pages/ConversationalSignup";

const routes: RouteObject[] = [
  {
    path: "/",
    element: <ModernLogin />,
  },
  {
    path: "/signup",
    element: <ConversationalSignup />,
  },
  {
    path: "/main-dashboard/:sessionId?",
    element: (
      <ProtectedRoute>
        <ChatLayout />
      </ProtectedRoute>
    ),
  },
];

export default routes;
