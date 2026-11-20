import { useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { DemoUser, getDemoUser, saveDemoUser } from "./api/client";
import { Team } from "./api/teams";
import DemoUserBar from "./components/DemoUserBar";
import CreateTeamPage from "./pages/CreateTeamPage";
import EditTeamPage from "./pages/EditTeamPage";
import TeamDetailsPage from "./pages/TeamDetailsPage";
import TeamsPage from "./pages/TeamsPage";

/**
 * Pages and their addresses:
 *   /teams        team list (TM-02)
 *   /teams/new    create a team (TM-01)
 *   /teams/:id    team details and members (TM-03)
 *   /teams/:id/edit  edit a team (TM-04)
 */
function App() {
  const [user, setUser] = useState<DemoUser>(getDemoUser);
  const canCreate = user.role === "TEAM_LEAD";

  function changeUser(next: DemoUser) {
    saveDemoUser(next);
    setUser(next);
  }

  return (
    <main className="container">
      <p className="eyebrow">PROJECT 3</p>
      <h1>Absence &amp; Capacity</h1>
      <DemoUserBar user={user} onChange={changeUser} />

      <Routes>
        <Route path="/" element={<Navigate to="/teams" replace />} />
        <Route path="/teams" element={<TeamsRoute canCreate={canCreate} />} />
        <Route path="/teams/new" element={<CreateTeamRoute canCreate={canCreate} />} />
        {/* key: reload the page when the demo user changes, because what they may see changes */}
        <Route path="/teams/:teamId" element={<TeamDetailsPage key={`${user.role}-${user.employeeId}`} user={user} />} />
        <Route path="/teams/:teamId/edit" element={<EditTeamPage user={user} />} />
        <Route path="*" element={<PageNotFound />} />
      </Routes>
    </main>
  );
}

/** Team list; shows the success message when we come from "Create team". */
function TeamsRoute({ canCreate }: { canCreate: boolean }) {
  const navigate = useNavigate();
  const created = (useLocation().state as { created?: Team } | null)?.created ?? null;
  return (
    <TeamsPage
      created={created}
      canCreate={canCreate}
      onCreate={() => navigate("/teams/new")}
      onOpen={(team) => navigate(`/teams/${team.id}`)}
    />
  );
}

function CreateTeamRoute({ canCreate }: { canCreate: boolean }) {
  const navigate = useNavigate();
  return (
    <CreateTeamPage
      canCreate={canCreate}
      onCreated={(team) => navigate("/teams", { state: { created: team } })}
      onCancel={() => navigate("/teams")}
    />
  );
}

function PageNotFound() {
  return (
    <section>
      <h2>Page not found</h2>
      <p><Link to="/teams">← Back to teams</Link></p>
    </section>
  );
}

export default App;
