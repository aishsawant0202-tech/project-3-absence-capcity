import { useState } from "react";
import { Link, NavLink, Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { DemoUser, getDemoUser, saveDemoUser } from "./api/client";
import { Team } from "./api/teams";
import DemoUserBar from "./components/DemoUserBar";
import CreateEmployeePage from "./pages/CreateEmployeePage";
import CreateTeamPage from "./pages/CreateTeamPage";
import EditEmployeePage from "./pages/EditEmployeePage";
import EmployeeDetailsPage from "./pages/EmployeeDetailsPage";
import EmployeesPage from "./pages/EmployeesPage";
import MyProfilePage from "./pages/MyProfilePage";
import EditTeamPage from "./pages/EditTeamPage";
import TeamDetailsPage from "./pages/TeamDetailsPage";
import TeamsPage from "./pages/TeamsPage";

/**
 * Pages and their addresses:
 *   /teams        team list (TM-02)
 *   /teams/new    create a team (TM-01)
 *   /teams/:id    team details and members (TM-03)
 *   /teams/:id/edit  edit a team (TM-04)
 *   /employees           employee directory (Member 3)
 *   /employees/new       add an employee
 *   /employees/:id       employee profile
 *   /employees/:id/edit  edit an employee / change team
 *   /my-profile          the logged-in employee's own profile
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
      <nav className="main-nav" aria-label="Main">
        <NavLink to="/teams">Teams</NavLink>
        <NavLink to="/employees">Employees</NavLink>
        <NavLink to="/my-profile">My profile</NavLink>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/teams" replace />} />
        <Route path="/teams" element={<TeamsRoute canCreate={canCreate} />} />
        <Route path="/teams/new" element={<CreateTeamRoute canCreate={canCreate} />} />
        {/* key: reload the page when the demo user changes, because what they may see changes */}
        <Route path="/teams/:teamId" element={<TeamDetailsPage key={`${user.role}-${user.employeeId}`} user={user} />} />
        <Route path="/teams/:teamId/edit" element={<EditTeamPage user={user} />} />
        {/* Employee Management (Member 3); key: reload when the demo user changes */}
        <Route path="/employees" element={<EmployeesPage user={user} />} />
        <Route path="/employees/new" element={<CreateEmployeePage user={user} />} />
        <Route path="/employees/:employeeId" element={<EmployeeDetailsPage key={`${user.role}-${user.employeeId}`} user={user} />} />
        <Route path="/employees/:employeeId/edit" element={<EditEmployeePage user={user} />} />
        <Route path="/my-profile" element={<MyProfilePage key={`${user.role}-${user.employeeId}`} />} />
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