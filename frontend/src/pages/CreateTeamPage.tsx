/** TM-01 Create a team. The fields and checks are in components/TeamForm.tsx (shared with Edit). */
import { Team, createTeam } from "../api/teams";
import TeamForm from "../components/TeamForm";

interface Props {
  canCreate: boolean; // only TEAM_LEAD; the backend checks this again (403)
  onCreated: (team: Team) => void;
  onCancel: () => void;
}

export default function CreateTeamPage({ canCreate, onCreated, onCancel }: Props) {
  return (
    <section>
      <h2>Create a team</h2>
      {!canCreate && (
        <p className="notice">Only Team Leads can create teams. Switch the demo login role to TEAM_LEAD.</p>
      )}
      <TeamForm
        canSubmit={canCreate}
        onSubmit={async (values) => onCreated(await createTeam(values))}
        onCancel={onCancel}
      />
    </section>
  );
}
