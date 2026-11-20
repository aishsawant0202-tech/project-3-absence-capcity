/**
 * TEMPORARY demo login: pick the role and employee id that are sent as X-Role / X-Employee-Id.
 * TODO(Member 4): remove when the real login exists.
 */
import { DemoUser, ROLES, Role } from "../api/client";

interface Props {
  user: DemoUser;
  onChange: (user: DemoUser) => void;
}

export default function DemoUserBar({ user, onChange }: Props) {
  return (
    <div className="demo-bar">
      <span className="demo-tag">Demo login</span>
      <label>
        Role{" "}
        <select value={user.role} onChange={(e) => onChange({ ...user, role: e.target.value as Role })}>
          {ROLES.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </label>
      <label>
        Employee id{" "}
        <input
          type="number"
          min={1}
          value={user.employeeId}
          onChange={(e) => {
            const id = Number.parseInt(e.target.value, 10);
            if (Number.isInteger(id) && id > 0) onChange({ ...user, employeeId: id });
          }}
        />
      </label>
    </div>
  );
}
