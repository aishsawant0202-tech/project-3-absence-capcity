/** EM-FE-05 My profile: the logged-in employee's own data (GET /api/v1/employees/me). */
import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { Employee, fullName, getMyProfile } from "../api/employees";
import { getTeam } from "../api/teams";
import EmployeeCard from "../components/EmployeeCard";

export default function MyProfilePage() {
  const [me, setMe] = useState<Employee | null>(null);
  const [teamName, setTeamName] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    setNotFound(false);
    try {
      const found = await getMyProfile();                     // GET /api/v1/employees/me
      setMe(found);
      setTeamName(found.teamId == null ? null : await getTeam(found.teamId).then((t) => t.name, () => `Team #${found.teamId}`));
    } catch (err) {
      if (err instanceof ApiError && err.code === "NOT_FOUND") setNotFound(true);
      else setError(err instanceof ApiError ? err.message : "Could not load your profile.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <section><p className="hint" role="status">Loading your profile…</p></section>;
  if (notFound) {
    return (
      <section>
        <h2>My profile</h2>
        <p className="notice">There is no employee record for your login. Check the employee id in the demo login.</p>
      </section>
    );
  }
  if (error || !me) {
    return (
      <section>
        <h2>My profile</h2>
        <div className="form-error" role="alert">{error} <button onClick={load}>Retry</button></div>
      </section>
    );
  }

  return (
    <section>
      <h2>My profile</h2>
      <p className="hint">{fullName(me)}</p>
      <EmployeeCard employee={me} teamName={teamName} />
    </section>
  );
}