import { Route, Switch } from "wouter";
import AppShell from "./components/layout/AppShell";
import Dashboard from "./pages/Dashboard";
import HostDetail from "./pages/HostDetail";
import Alerts from "./pages/Alerts";
import Insights from "./pages/Insights";
import Maintenance from "./pages/Maintenance";
import Security from "./pages/Security";

export default function App() {
  return (
    <AppShell>
      <Switch>
        <Route path="/" component={Dashboard} />
        <Route path="/hosts/:id" component={HostDetail} />
        <Route path="/alerts" component={Alerts} />
        <Route path="/insights" component={Insights} />
        <Route path="/maintenance" component={Maintenance} />
        <Route path="/security" component={Security} />
        <Route>
          <div className="flex items-center justify-center h-64 text-slate-500">
            404 - Page Not Found
          </div>
        </Route>
      </Switch>
    </AppShell>
  );
}
