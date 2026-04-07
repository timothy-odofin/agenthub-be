/**
 * useRouteSync — auto-syncs the frontend route registry to the backend.
 *
 * On mount, this hook:
 *   1. GETs the currently stored routes from the backend
 *   2. Compares them against the local ROUTE_REGISTRY
 *   3. If anything changed (new route, updated description, new actions),
 *      POSTs the full registry to the backend
 *   4. Backend stores them in routes.json — LLM reads at tool-call time
 *
 * This eliminates the need to manually update the backend when frontend
 * routes change. Just update routes/registry.ts and the sync happens
 * automatically on the next app load.
 *
 * Usage:
 *   function App() {
 *     useRouteSync();          // syncs on mount
 *     return <RouterProvider />;
 *   }
 */

import { useEffect, useRef } from "react";
import { ROUTE_REGISTRY } from "@/routes/registry";
import { getRoutes, syncRoutes } from "@/api/routes";

/**
 * Deep-compare two route sets to detect changes.
 *
 * Returns true if the routes are different (sync needed).
 * Compares by serializing to JSON — simple and reliable.
 */
function routesAreDifferent(
  local: typeof ROUTE_REGISTRY,
  remote: any[]
): boolean {
  if (local.length !== remote.length) return true;

  // Sort both by path for consistent comparison
  const sortByPath = (a: { path: string }, b: { path: string }) =>
    a.path.localeCompare(b.path);

  const localSorted = [...local].sort(sortByPath);
  const remoteSorted = [...remote].sort(sortByPath);

  return JSON.stringify(localSorted) !== JSON.stringify(remoteSorted);
}

export function useRouteSync() {
  // Prevent double-sync in React StrictMode
  const hasSynced = useRef(false);

  useEffect(() => {
    if (hasSynced.current) return;

    const doSync = async () => {
      try {
        // 1. Fetch what the backend currently has
        const res = await getRoutes();
        const remoteRoutes = res.data?.routes ?? [];

        // 2. Compare with local registry
        if (routesAreDifferent(ROUTE_REGISTRY, remoteRoutes)) {
          console.log(
            "🔄 Route sync: changes detected, pushing",
            ROUTE_REGISTRY.length,
            "routes to backend"
          );

          const syncRes = await syncRoutes(ROUTE_REGISTRY);
          if (syncRes.data?.success) {
            console.log(
              "✅ Route sync complete:",
              syncRes.data.synced_count,
              "routes"
            );
          } else {
            console.warn("⚠️ Route sync failed:", syncRes.data?.message);
          }
        } else {
          console.log("✅ Route sync: routes are up to date");
        }

        hasSynced.current = true;
      } catch (err) {
        // Non-fatal — if sync fails, the backend still has whatever
        // was synced last time. Navigation may still work.
        console.warn("⚠️ Route sync error (non-fatal):", err);
      }
    };

    doSync();
  }, []);
}
