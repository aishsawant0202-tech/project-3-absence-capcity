/** TM-02 Team list: all teams with status and minimum capacity, searchable by name. */
import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError } from "../api/client";
import { Team, listTeams } from "../api/teams";

interface Props {
  created: Team | null; // team just created (TM-01): show the success message
  canCreate: boolean; // only TEAM_LEAD sees "Create team"; the backend checks it again
  onCreate: () => void;
  onOpen: (team: Team) => void;
}

export default function TeamsPage({ created, canCreate, onCreate, onOpen }: Props) {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setTeams(await listTeams());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load the teams.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Load the list once when the page opens
  useEffect(() => {
    load();
  }, [load]);

  // Search in the browser: case-insensitive "contains" on the name; empty search shows all
  const shown = useMemo(() => {
    const q = search.trim().toLowerCase();
    return q ? teams.filter((t) => t.name.toLowerCase().includes(q)) : teams;
  }, [teams, search]);

  return (
    <section>
      <div className="page-head">
        <h2>Teams</h2>
        {canCreate && <button className="primary" onClick={onCreate}>+ Create team</button>}
      </div>

      {created && (
        <p className="success" role="status">Team “{created.name}” was created. You are its team lead.</p>
      )}

      {loading ? (
        <p className="hint" role="status">Loading teams…</p>
      ) : error ? (
        <div className="form-error" role="alert">
          {error} <button onClick={load}>Retry</button>
        </div>
      ) : teams.length === 0 ? (
        <p className="empty">No teams yet.{canCreate && " Create the first one with “+ Create team”."}</p>
      ) : (
        <>
          <input
            type="search"
            className="search"
            placeholder="Search teams by name…"
            aria-label="Search teams by name"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          {shown.length === 0 ? (
            <p className="empty">No team matches “{search.trim()}”.</p>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Status</th>
                  <th className="num">Min. capacity (FTE)</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {shown.map((t) => (
                  <tr key={t.id} className="clickable" onClick={() => onOpen(t)}>
                    <td>{t.name}</td>
                    <td><span className={`badge ${t.status === "ACTIVE" ? "" : "badge-inactive"}`}>{t.status}</span></td>
                    <td className="num">{t.minRequiredFte}</td>
                    <td className="num">
                      <button
                        className="link"
                        onClick={(e) => {
                          e.stopPropagation(); // the row click would open it a second time
                          onOpen(t);
                        }}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="hint">{shown.length} of {teams.length} team(s)</p>
        </>
      )}
    </section>
  );
}
