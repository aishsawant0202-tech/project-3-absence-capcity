/** TM-03 Team details: team data, team lead, members. TM-04: Edit and Activate/Deactivate for the team's lead. */
import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { ApiError, DemoUser } from "../api/client";
import { Team, TeamMember, getTeam, listTeamMembers, setTeamStatus } from "../api/teams";

interface Props {
  user: DemoUser; // who is looking: decides which actions are shown
}

type Members =
  | { kind: "list"; items: TeamMember[] }
  | { kind: "forbidden"; message: string }; // 403: not a member of this team and not HR Admin

export default function TeamDetailsPage({ user }: Props) {
  const teamId = Number(useParams().teamId);
  const [team, setTeam] = useState<Team | null>(null);
  const [members, setMembers] = useState<Members | null>(null);
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
    if (!Number.isInteger(teamId) || teamId <= 0) {
      setNotFound(true); // e.g. /teams/abc
      setLoading(false);
      return;
    }
    try {
      // Both requests at the same time. Members may fail with 403; that must not hide the team.
      const [teamResult, membersResult] = await Promise.allSettled([getTeam(teamId), listTeamMembers(teamId)]);
      if (teamResult.status === "rejected") throw teamResult.reason;
      setTeam(teamResult.value);

      if (membersResult.status === "fulfilled") {
        setMembers({ kind: "list", items: membersResult.value });
      } else if (membersResult.reason instanceof ApiError && membersResult.reason.code === "FORBIDDEN") {
        setMembers({ kind: "forbidden", message: membersResult.reason.message });
      } else {
        throw membersResult.reason;
      }
    } catch (err) {
      if (err instanceof ApiError && err.code === "NOT_FOUND") setNotFound(true);
      else setError(err instanceof ApiError ? err.message : "Could not load the team.");
    } finally {
      setLoading(false);
    }
  }, [teamId]);

  useEffect(() => {
    load();
  }, [load]);

  const back = <Link to="/teams" className="back">← Back to teams</Link>;

  if (loading) return <section>{back}<p className="hint" role="status">Loading team…</p></section>;
  if (notFound) {
    return (
      <section>
        {back}
        <h2>Team not found</h2>
        <p className="empty">There is no team with this id. It may have been typed wrong.</p>
      </section>
    );
  }
  if (error || !team) {
    return (
      <section>
        {back}
        <div className="form-error" role="alert">{error} <button onClick={load}>Retry</button></div>
      </section>
    );
  }

  // The lead's name comes from the members list; without access to it, show the id
  const leadName = members?.kind === "list" ? members.items.find((m) => m.id === team.teamLeadEmployeeId)?.name : undefined;
  const lead = team.teamLeadEmployeeId == null ? "No team lead" : leadName ?? `Employee #${team.teamLeadEmployeeId}`;

  // Only the lead of this team may edit and (de)activate (team decision 19.11); the backend checks again (403)
  const isLeadOfThisTeam = user.role === "TEAM_LEAD" && user.employeeId === team.teamLeadEmployeeId;

  async function toggleStatus(current: Team) {
    const next = current.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
    if (next === "INACTIVE" && !window.confirm(`Deactivate team “${current.name}”?\nNo new employees can be assigned to it.`)) {
      return;
    }
    setChangingStatus(true);
    setMessage("");
    setActionError("");
    try {
      const saved = await setTeamStatus(current.id, next);
      setTeam(saved); // badge and button text update at once
      setMessage(`Team “${saved.name}” is now ${saved.status === "ACTIVE" ? "active" : "inactive"}.`);
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
        <h2>{team.name}</h2>
        {isLeadOfThisTeam && (
          <div className="actions">
            <Link to={`/teams/${team.id}/edit`} className="button">Edit</Link>
            <button onClick={() => toggleStatus(team)} disabled={changingStatus}>
              {changingStatus ? "Saving…" : team.status === "ACTIVE" ? "Deactivate" : "Activate"}
            </button>
          </div>
        )}
      </div>
      {message && <p className="success" role="status">{message}</p>}
      {actionError && <p className="form-error" role="alert">{actionError}</p>}

      <dl className="team-card">
        <dt>Status</dt>
        <dd><span className={`badge ${team.status === "ACTIVE" ? "" : "badge-inactive"}`}>{team.status}</span></dd>
        <dt>Description</dt><dd>{team.description || "—"}</dd>
        <dt>Minimum capacity</dt><dd>{team.minRequiredFte} FTE</dd>
        <dt>Team lead</dt><dd>{lead}</dd>
      </dl>

      <h3>Members</h3>
      {members?.kind === "forbidden" ? (
        <p className="notice">{members.message}</p>
      ) : !members || members.items.length === 0 ? (
        <p className="empty">No employees assigned yet.</p>
      ) : (
        <MembersTable members={members.items} leadId={team.teamLeadEmployeeId} />
      )}
    </section>
  );
}

function MembersTable({ members, leadId }: { members: TeamMember[]; leadId: number | null }) {
  // Ordinary members only get id and name, so the extra columns appear only when the data is there
  const full = members.some((m) => m.email !== undefined);
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Name</th>
          {full && <th>Job title</th>}
          {full && <th className="num">FTE</th>}
          {full && <th>Status</th>}
        </tr>
      </thead>
      <tbody>
        {members.map((m) => (
          <tr key={m.id}>
            <td>{m.name}{m.id === leadId && <span className="badge badge-lead">Lead</span>}</td>
            {full && <td>{m.jobTitle || "—"}</td>}
            {full && <td className="num">{m.workingTimeShare}</td>}
            {full && (
              <td><span className={`badge ${m.status === "ACTIVE" ? "" : "badge-inactive"}`}>{m.status}</span></td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
