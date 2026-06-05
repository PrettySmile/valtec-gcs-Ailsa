import { useWebSocket } from "./hooks/useWebSocket";
import FleetDashboard from "./components/FleetDashboard";

function App() {
  useWebSocket();
  return <FleetDashboard />;
}

export default App;
