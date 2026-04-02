import { Suspense, lazy } from "react";
import { Route, Switch } from "wouter";
import AppShell from "@/components/layout/AppShell";

const Dashboard    = lazy(() => import("@/pages/Dashboard"));
const HostDetail   = lazy(() => import("@/pages/HostDetail"));
const Alerts       = lazy(() => import("@/pages/Alerts"));
const Insights     = lazy(() => import("@/pages/Insights"));
const Maintenance  = lazy(() => import("@/pages/Maintenance"));

function Spinner() {
  return (
    <div className="flex items-center justify-center h-64 text-slate-500 text-sm">
      Loading…
    </div>
  );
}

export default function App() {
  return (
    <AppShell>
      <Suspense fallback={<Spinner />}>
        <Switch>
          <Route path="/" component={Dashboard} />
          <Route path="/hosts/:id" component={HostDetail} />
          <Route path="/alerts" component={Alerts} />
          <Route path="/insights" component={Insights} />
          <Route path="/maintenance" component={Maintenance} />
          <Route>
            <div className="p-8 text-slate-400">404 — Page not found</div>
          </Route>
        </Switch>
      </Suspense>
    </AppShell>
  );
}
