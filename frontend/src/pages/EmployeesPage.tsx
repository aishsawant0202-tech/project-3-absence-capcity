/** EM-FE-01 Employee directory: all employees, search by name or email, filter by team, type and status. */
import { useCallback, useEffect, useMemo, useState } from "react";            // React tools: state, effects
import { useLocation, useNavigate } from "react-router-dom";                   // Page addresses
import { ApiError, DemoUser } from "../api/client";
import { Employee, EmployeeStatus, EmploymentType, fullName, listEmployees } from "../api/employees";
import { Team, listTeams } from "../api/teams";

interface Props {
  user: DemoUser; // only HR_ADMIN sees "+ Add employee"; the backend checks again (403)
}

export default function EmployeesPage({ user }: Props) {
  const navigate = useNavigate();
  const message = (useLocation().state as { message?: string } | null)?.message ?? ""; // e.g. "Employee … was added."
  const isHr = user.role === "HR_ADMIN";

  const [employees, setEmployees] = useState<Employee[]>([]);  // the list from the backend
  const [teams, setTeams] = useState<Team[]>([]);              // for the team filter and team names
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Filters (sent to the backend: GET /api/v1/employees?search=&teamId=&status=&employmentType=)
  const [search, setSearch] = useState("");
  const [teamId, setTeamId] = useState("");
  const [status, setStatus] = useState<EmployeeStatus | "">("");
  const [type, setType] = useState<EmploymentType | "">("");
  const anyFilter = search.trim() !== "" || teamId !== "" || status !== "" || type !== "";

  const load = useCallback(async () => {                       // Ask the backend for the list
    setLoading(true);
    setError("");
    try {
      setEmployees(await listEmployees({ search, teamId: teamId ? Number(teamId) : null, status, employmentType: type }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load the employees.");
    } finally {
      setLoading(false);
    }
  }, [search, teamId, status, type]);

  // Reload when a filter changes; wait 300 ms after typing so we do not send a request per letter
  useEffect(() => {
    const timer = setTimeout(load, 300);
    return () => clearTimeout(timer);
  }, [load]);

  // Teams for the filter and to show team names instead of ids (failure here is not fatal)
  useEffect(() => {
    listTeams().then(setTeams).catch(() => setTeams([]));
  }, []);
  const teamName = useMemo(() => new Map(teams.map((t) => [t.id, t.name])), [teams]);

  function clearFilters() {
    setSearch("");
    setTeamId("");
    setStatus("");
    setType("");
  }

  return (
    <section>
      <div className="page-head">
        <h2>Employees</h2>
        {isHr && <button className="primary" onClick={() => navigate("/employees/new")}>+ Add employee</button>}
      </div>

      {message && <p className="success" role="status">{message}</p>}

      <input
        type="search"
        className="search"
        placeholder="Search by name or email…"
        aria-label="Search employees by name or email"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <div className="filters">
        <label>
          Team{" "}
          <select value={teamId} onChange={(e) => setTeamId(e.target.value)}>
            <option value="">All teams</option>
            {teams.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
        </label>
        <label>
          Type{" "}
          <select value={type} onChange={(e) => setType(e.target.value as EmploymentType | "")}>
            <option value="">All types</option>
            <option value="PERMANENT">Permanent</option>
            <option value="CONTRACT">Contract</option>
          </select>
        </label>
        <label>
          Status{" "}
          <select value={status} onChange={(e) => setStatus(e.target.value as EmployeeStatus | "")}>
            <option value="">All statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
          </select>
        </label>
        {anyFilter && <button className="link" onClick={clearFilters}>Clear filters</button>}
      </div>

      {loading ? (
        <p className="hint" role="status">Loading employees…</p>
      ) : error ? (
        <div className="form-error" role="alert">
          {error} <button onClick={load}>Retry</button>
        </div>
      ) : employees.length === 0 ? (
        <p className="empty">
          {anyFilter ? "No employee matches these filters." : "No employees yet."}
          {!anyFilter && isHr && " Add the first one with “+ Add employee”."}
        </p>
      ) : (
        <>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Job title</th>
                  <th>Team</th>
                  <th>Type</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {employees.map((e) => (
                  <tr key={e.id} className="clickable" onClick={() => navigate(`/employees/${e.id}`)}>
                    <td>
                      <button
                        className="link"
                        onClick={(ev) => {
                          ev.stopPropagation(); // the row click would open it a second time
                          navigate(`/employees/${e.id}`);
                        }}
                      >
                        {fullName(e)}
                      </button>
                    </td>
                    <td>{e.email}</td>
                    <td>{e.jobTitle || "—"}</td>
                    <td>{e.teamId == null ? "—" : teamName.get(e.teamId) ?? `Team #${e.teamId}`}</td>
                    <td>{e.employmentType === "PERMANENT" ? "Permanent" : "Contract"}</td>
                    <td><span className={`badge ${e.status === "ACTIVE" ? "" : "badge-inactive"}`}>{e.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="hint">{employees.length} employee(s)</p>
        </>
      )}
    </section>
  );
}