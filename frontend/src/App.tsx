import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  clearToken,
  getCurrentUser,
  getToken,
  type CurrentUser,
  type DemoUser,
} from "./api/client";


import { Team } from "./api/teams";
import LoginPage from "./pages/LoginPage";
import CreateEmployeePage from "./pages/CreateEmployeePage";
import EditEmployeePage from "./pages/EditEmployeePage";
import EmployeeDetailsPage from "./pages/EmployeeDetailsPage";
import EmployeesPage from "./pages/EmployeesPage";
import MyProfilePage from "./pages/MyProfilePage";
import CreateTeamPage from "./pages/CreateTeamPage";
import EditTeamPage from "./pages/EditTeamPage";
import TeamDetailsPage from "./pages/TeamDetailsPage";
import TeamsPage from "./pages/TeamsPage";

function App() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  async function loadCurrentUser() {
    const token = getToken();

    if (!token) {
      setUser(null);
      setCheckingAuth(false);
      return;
    }

    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch {
      clearToken();
      setUser(null);
    } finally {
      setCheckingAuth(false);
    }
  }

    useEffect(() => {
    void loadCurrentUser();
  }, []);

  function handleLoginSuccess() {
    setCheckingAuth(true);
    void loadCurrentUser();
  }

  function handleLogout() {
    clearToken();
    setUser(null);
  }

  if (checkingAuth) {
    return <main className="container"><p>Loading...</p></main>;
  }

  if (!user) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage onLoginSuccess={handleLoginSuccess} />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  const demoUser: DemoUser = {
    role: user.role,
    employeeId: user.employee_id,
  };

  const canCreate = user.role === "TEAM_LEAD";

  return (
    <main className="container">
      <p className="eyebrow">PROJECT 3</p>
      <h1>Absence &amp; Capacity</h1>

      <div className="user-info">
        <span>
          Logged in as <strong>{user.first_name} {user.last_name}</strong>
          {" "}({user.role})
        </span>
        <button onClick={handleLogout}>Logout</button>
      </div>

      <nav className="main-nav" aria-label="Main">
        <NavLink to="/teams">Teams</NavLink>
        <NavLink to="/employees">Employees</NavLink>
        <NavLink to="/my-profile">My profile</NavLink>
      </nav>

      <Routes>
        <Route path="/" element={<Navigate to="/teams" replace />} />
        <Route path="/login" element={<Navigate to="/teams" replace />} />
        <Route path="/teams" element={<TeamsRoute canCreate={canCreate} />} />
        <Route path="/teams/new" element={<CreateTeamRoute canCreate={canCreate} />} />
        <Route
          path="/teams/:teamId"
          element={
            <TeamDetailsPage
              key={`${user.role}-${user.employee_id}`}
              user={demoUser}
            />
          }
        />
        <Route
          path="/teams/:teamId/edit"
          element={<EditTeamPage user={demoUser} />}
        />
        {/* Employee Management (Member 3) */}
        <Route path="/employees" element={<EmployeesPage user={demoUser} />} />
        <Route path="/employees/new" element={<CreateEmployeePage user={demoUser} />} />
        <Route
          path="/employees/:employeeId"
          element={<EmployeeDetailsPage key={`${user.role}-${user.employee_id}`} user={demoUser} />}
        />
        <Route path="/employees/:employeeId/edit" element={<EditEmployeePage user={demoUser} />} />
        <Route path="/my-profile" element={<MyProfilePage key={`${user.role}-${user.employee_id}`} />} />
        <Route path="*" element={<PageNotFound />} />
      </Routes>
    </main>
  );
}

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