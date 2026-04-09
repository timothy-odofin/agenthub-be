
import { Outlet } from 'react-router-dom'
import { useRouteSync } from '@/hooks/useRouteSync'

function App() {
  // Auto-sync frontend route registry to backend on every app startup.
  // This runs before login — routes are public metadata.
  useRouteSync();

  return (
    <>
     <div >
        <Outlet/>
     </div>
    </>
  )
}

export default App
