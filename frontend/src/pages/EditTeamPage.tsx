/** TM-04 Edit a team: the shared form, filled with the current values. Only the team's lead may use it. */
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, DemoUser } from "../api/client";
import { Team, getTeam, updateTeam } from "../api/teams";
import TeamForm from "../components/TeamForm";

interface Props {
  user: DemoUser;
}

export default function EditTeamPage({ user }: Props) {
  const teamId = Number(useParams().teamId);
  const navigate = useNavigate();
  const [team, setTeam] = useState<Team | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setTeam(await getTeam(teamId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load the team.");
    } finally {
      setLoading(false);
    }
  }, [teamId]);

  useEffect(() => {
    load();
  }, [load]);

  const details = `/teams/${teamId}`;
  const back = <Link to={details} className="back">← Back to team</Link>;

  if (loading) return <section>{back}<p className="hint" role="status">Loading team…</p></section>;
  if (error || !team) {
    return (
      <section>
        <Link to="/teams" className="back">← Back to teams</Link>
        <div className="form-error" role="alert">{error || "Team not found."}</div>
      </section>
    );
  }

  // Someone who typed the edit address without being this team's lead (the backend would answer 403 too)
  const isLeadOfThisTeam = user.role === "TEAM_LEAD" && user.employeeId === team.teamLeadEmployeeId;
  if (!isLeadOfThisTeam) {
    return (
      <section>
        {back}
        <h2>Not allowed</h2>
        <p className="notice">Only the team lead of “{team.name}” can edit this team.</p>
      </section>
    );
  }

  return (
    <section>
      {back}
      <h2>Edit team</h2>
      <TeamForm
        initial={team}
        canSubmit
        onSubmit={async (values) => {
          const saved = await updateTeam(team.id, values);
          navigate(details, { state: { message: `Team “${saved.name}” was updated.` } });
        }}
        onCancel={() => navigate(details)}
      />
    </section>
  );
}
