import type { RouteObject } from "react-router-dom";
import App from "@/App";
import ModernLogin from "@/pages/ModernLogin";
import ProtectedRoute from "@/middleware/ProtectedRoute";
import ChatLayout from "@/pages/ChatLayout";
import ConversationalSignup from "@/pages/ConversationalSignup";

const routes: RouteObject[] = [
  {
    // App is the root layout — renders on every page.
    // useRouteSync() lives here so it fires on app startup.
    element: <App />,
    children: [
      {
        path: "/",
        element: <ModernLogin />,
      },
      // Signup route
      {
        path: "/signup",
        element: <ConversationalSignup />,
      },
      // Protected routes
      {
        path: "/main-dashboard/:sessionId?",
        element: (
          <ProtectedRoute>
            <ChatLayout />
          </ProtectedRoute>
        ),
      },
    ],
  },
];

export default routes;
