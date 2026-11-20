import { Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { EmptyState } from "./components/EmptyState";
import { Landing } from "./pages/Landing";
import { CreateGoal } from "./pages/CreateGoal";
import { Discovery } from "./pages/Discovery";
import { ProfileReview } from "./pages/ProfileReview";
import { RoadmapPage } from "./pages/RoadmapPage";
import { Dashboard } from "./pages/Dashboard";
import { CheckIn } from "./pages/CheckIn";
import { SignIn } from "./pages/SignIn";
import { History } from "./pages/History";
import { Settings } from "./pages/Settings";
import { Link } from "react-router-dom";

export function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/create" element={<CreateGoal />} />
        <Route path="/goals/:goalId/discovery" element={<Discovery />} />
        <Route path="/goals/:goalId/profile" element={<ProfileReview />} />
        <Route path="/goals/:goalId/roadmap" element={<RoadmapPage />} />
        <Route path="/goals/:goalId/dashboard" element={<Dashboard />} />
        <Route path="/goals/:goalId/checkin" element={<CheckIn />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/history" element={<History />} />
        <Route path="/settings" element={<Settings />} />
        <Route
          path="*"
          element={
            <div className="page page-narrow">
              <EmptyState
                title="This page doesn't exist"
                description="The link may be old or mistyped."
                action={
                  <Link to="/" className="btn btn-primary">
                    Go to the start
                  </Link>
                }
              />
            </div>
          }
        />
      </Routes>
    </AppShell>
  );
}
