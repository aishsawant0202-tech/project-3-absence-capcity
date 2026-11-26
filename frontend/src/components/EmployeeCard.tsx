/** Employee details as a key-value card. Used by the profile page (EM-FE-04) and My profile (EM-FE-05). */
import { Employee, formatDate } from "../api/employees";

interface Props {
  employee: Employee;
  teamName: string | null; // null = no team
}

export default function EmployeeCard({ employee: e, teamName }: Props) {
  return (
    <dl className="team-card">
      <dt>Status</dt>
      <dd><span className={`badge ${e.status === "ACTIVE" ? "" : "badge-inactive"}`}>{e.status}</span></dd>
      <dt>Email</dt><dd>{e.email}</dd>
      <dt>Job title</dt><dd>{e.jobTitle || "—"}</dd>
      <dt>Team</dt><dd>{teamName ?? "No team"}</dd>
      <dt>Employment type</dt><dd>{e.employmentType === "PERMANENT" ? "Permanent" : "Contract"}</dd>
      <dt>Working-time share</dt><dd>{e.workingTimeShare} FTE</dd>
      <dt>Start date</dt><dd>{formatDate(e.startDate)}</dd>
      {e.employmentType === "CONTRACT" && (<><dt>End date</dt><dd>{formatDate(e.endDate)}</dd></>)}
      {e.employeeRef && (<><dt>Employee reference</dt><dd>{e.employeeRef}</dd></>)}
    </dl>
  );
}