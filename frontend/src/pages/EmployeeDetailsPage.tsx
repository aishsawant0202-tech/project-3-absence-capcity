/** EM-FE-04 Employee profile: details, team and status. HR Admin: Edit and Activate/Deactivate. */
import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { ApiError, DemoUser } from "../api/client";
import { Employee, fullName, getEmployee, setEmployeeStatus } from "../api/employees";
import { getTeam } from "../api/teams";
import EmployeeCard from "../components/EmployeeCard";

interface Props {
  user: DemoUser; // who is looking: decides which actions are shown
}

export default function EmployeeDetailsPage({ user }: Props) {
  const employeeId = Number(useParams().employeeId);        // the 5 in /employees/5
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [teamName, setTeamName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState("");
  // Success message: from the edit page (via navigation state) or after a status change
  const [message, setMessage] = useState<string>((useLocation().state as { message?: string } | null)?.message ?? "");
  const [actionError, setActionError] = useState("");
  const [changingStatus, setChangingStatus] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    setNotFound(false);
    if (!Number.isInteger(employeeId) || employeeId <= 0) {
      setNotFound(true); // e.g. /employees/abc
      setLoading(false);
      return;
    }
    try {
      const found = await getEmployee(employeeId);
      setEmployee(found);
      // Team name for the card; if the team cannot be loaded, show its id instead
      setTeamName(found.teamId == null ? null : await getTeam(found.teamId).then((t) => t.name, () => `Team #${found.teamId}`));
    } catch (err) {
      if (err instanceof ApiError && err.code === "NOT_FOUND") setNotFound(true);
      else setError(err instanceof ApiError ? err.message : "Could not load the employee.");
    } finally {
      setLoading(false);
    }
  }, [employeeId]);

  useEffect(() => {
    load();
  }, [load]);

  const back = <Link to="/employees" className="back">← Back to employees</Link>;

  if (loading) return <section>{back}<p className="hint" role="status">Loading employee…</p></section>;
  if (notFound) {
    return (
      <section>
        {back}
        <h2>Employee not found</h2>
        <p className="empty">There is no employee with this id. It may have been typed wrong.</p>
      </section>
    );
  }
  if (error || !employee) {
    return (
      <section>
        {back}
        <div className="form-error" role="alert">{error} <button onClick={load}>Retry</button></div>
      </section>
    );
  }

  const isHr = user.role === "HR_ADMIN"; // only HR Admin may edit and (de)activate; the backend checks again (403)

  async function toggleStatus(current: Employee) {
    const next = current.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
    if (next === "INACTIVE" && !window.confirm(`Deactivate “${fullName(current)}”?\nThe employee is kept, but marked as inactive.`)) {
      return;
    }
    setChangingStatus(true);
    setMessage("");
    setActionError("");
    try {
      const saved = await setEmployeeStatus(current.id, next);   // PATCH /api/v1/employees/5/status
      setEmployee(saved); // badge and button text update at once
      setMessage(`“${fullName(saved)}” is now ${saved.status === "ACTIVE" ? "active" : "inactive"}.`);
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not change the status.");
    } finally {
      setChangingStatus(false);
    }
  }

  return (
    <section>
      {back}
      <div className="page-head">
        <h2>{fullName(employee)}</h2>
        {isHr && (
          <div className="actions">
            <Link to={`/employees/${employee.id}/edit`} className="button">Edit</Link>
            <button onClick={() => toggleStatus(employee)} disabled={changingStatus}>
              {changingStatus ? "Saving…" : employee.status === "ACTIVE" ? "Deactivate" : "Activate"}
            </button>
          </div>
        )}
      </div>
      {message && <p className="success" role="status">{message}</p>}
      {actionError && <p className="form-error" role="alert">{actionError}</p>}

      <EmployeeCard employee={employee} teamName={teamName} />
      {employee.teamId != null && (
        <p><Link to={`/teams/${employee.teamId}`} className="back">Open team →</Link></p>
      )}
    </section>
  );
}