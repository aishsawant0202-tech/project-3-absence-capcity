/**
 * The employee form used by Add (EM-FE-02) and Edit (EM-FE-03), so both have the same fields and checks.
 * The page decides what Save does (POST or PATCH) through `onSubmit`.
 */
import { FormEvent, useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { Employee, EmployeeInput, EmploymentType } from "../api/employees";
import { Team, listTeams } from "../api/teams";

type Field = keyof EmployeeInput; // same names as the API fields
const FIELDS: Field[] = [
  "employeeRef", "firstName", "lastName", "email", "teamId",
  "jobTitle", "employmentType", "workingTimeShare", "startDate", "endDate",
];
type Errors = Partial<Record<Field, string>>; // one error message per field

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/; // same check as the backend

interface Props {
  initial?: Employee; // Edit: the current values; Add: empty form
  canSubmit: boolean; // false -> Save disabled (wrong role); the backend checks again
  onSubmit: (values: EmployeeInput) => Promise<void>; // throws ApiError on failure
  onCancel: () => void;
}

/** Client-side checks; the backend repeats them (400 VALIDATION_ERROR). */
function validate(v: {
  firstName: string; lastName: string; email: string; employmentType: EmploymentType;
  fte: string; startDate: string; endDate: string;
}): Errors {
  const errors: Errors = {};
  if (!v.firstName.trim()) errors.firstName = "First name is required.";
  if (!v.lastName.trim()) errors.lastName = "Last name is required.";
  if (!v.email.trim()) errors.email = "Email is required.";
  else if (!EMAIL_PATTERN.test(v.email.trim())) errors.email = "Enter a valid email, e.g. name@example.com.";

  const fte = Number(v.fte);
  if (v.fte.trim() === "") errors.workingTimeShare = "Working-time share is required.";
  else if (!Number.isFinite(fte) || fte <= 0 || fte > 1) errors.workingTimeShare = "Enter a number above 0 and at most 1, e.g. 0.8.";
  else if (!/^\d+(\.\d{1,2})?$/.test(v.fte.trim())) errors.workingTimeShare = "Use at most 2 decimal places.";

  if (!v.startDate) errors.startDate = "Start date is required.";
  if (v.employmentType === "CONTRACT") {
    if (!v.endDate) errors.endDate = "A contract employee needs an end date.";
    else if (v.startDate && v.endDate < v.startDate) errors.endDate = "End date must not be before the start date.";
  }
  return errors;
}

export default function EmployeeForm({ initial, canSubmit, onSubmit, onCancel }: Props) {
  // One state per field; Edit starts with the current values
  const [firstName, setFirstName] = useState(initial?.firstName ?? "");
  const [lastName, setLastName] = useState(initial?.lastName ?? "");
  const [email, setEmail] = useState(initial?.email ?? "");
  const [employeeRef, setEmployeeRef] = useState(initial?.employeeRef ?? "");
  const [jobTitle, setJobTitle] = useState(initial?.jobTitle ?? "");
  const [teamId, setTeamId] = useState(initial?.teamId != null ? String(initial.teamId) : "");
  const [employmentType, setEmploymentType] = useState<EmploymentType>(initial?.employmentType ?? "PERMANENT");
  const [fte, setFte] = useState(initial ? String(initial.workingTimeShare) : "1");
  const [startDate, setStartDate] = useState(initial?.startDate ?? "");
  const [endDate, setEndDate] = useState(initial?.endDate ?? "");

  const [teams, setTeams] = useState<Team[]>([]);
  const [errors, setErrors] = useState<Errors>({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  // Teams for the dropdown. Only ACTIVE teams can take employees; the current team stays visible.
  useEffect(() => {
    listTeams().then(setTeams).catch(() => setTeams([]));
  }, []);
  const teamOptions = teams.filter((t) => t.status === "ACTIVE" || String(t.id) === teamId);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();                                     // Do not reload the page
    setFormError("");
    const found = validate({ firstName, lastName, email, employmentType, fte, startDate, endDate });
    setErrors(found);
    if (Object.keys(found).length > 0) return;              // Errors -> show them, do not send

    setSaving(true);
    try {
      await onSubmit({
        employeeRef: employeeRef.trim() || null,
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        email: email.trim(),
        teamId: teamId ? Number(teamId) : null,
        jobTitle: jobTitle.trim() || null,
        employmentType,
        workingTimeShare: Number(fte),
        startDate,
        endDate: employmentType === "CONTRACT" ? endDate : null, // PERMANENT never has an end date
      });
    } catch (err) {
      // Show the backend's error at the right place
      if (!(err instanceof ApiError)) {
        setFormError("Something went wrong. Please try again.");
      } else if (err.code === "EMAIL_TAKEN") {
        setErrors({ email: err.message });                  // under the email field
      } else if (err.code === "EMPLOYEE_REF_TAKEN") {
        setErrors({ employeeRef: err.message });
      } else if (err.code === "TEAM_INACTIVE" || (err.code === "NOT_FOUND" && err.message.startsWith("Team"))) {
        setErrors({ teamId: err.message });                 // under the team dropdown
      } else if (err.code === "VALIDATION_ERROR" && err.fieldErrors.length > 0) {
        const fromServer: Errors = {};
        for (const fe of err.fieldErrors) {
          const field = FIELDS.find((f) => f === fe.field);
          if (field) fromServer[field] = fe.message;
        }
        setErrors(fromServer);
        if (Object.keys(fromServer).length === 0) setFormError(err.message);
      } else {
        // UNAUTHENTICATED, FORBIDDEN, date rules from the server, server down: above the form
        setFormError(err.message);
      }
    } finally {
      setSaving(false);
    }
  }

  /** A text input with label, optional hint and error, wired for screen readers. */
  function textField(id: Field, label: string, value: string, set: (v: string) => void, type = "text", hint?: string) {
    const htmlId = `employee-${id}`;
    return (
      <div className="field">
        <label htmlFor={htmlId}>{label}</label>
        <input
          id={htmlId}
          type={type}
          value={value}
          onChange={(e) => set(e.target.value)}
          aria-invalid={!!errors[id]}
          aria-describedby={errors[id] ? `${htmlId}-error` : hint ? `${htmlId}-hint` : undefined}
        />
        {hint && <p id={`${htmlId}-hint`} className="hint">{hint}</p>}
        {errors[id] && <p id={`${htmlId}-error`} className="field-error">{errors[id]}</p>}
      </div>
    );
  }

  return (
    <>
      {formError && <p className="form-error" role="alert">{formError}</p>}

      <form onSubmit={handleSubmit} noValidate>
        <div className="form-row">
          {textField("firstName", "First name *", firstName, setFirstName)}
          {textField("lastName", "Last name *", lastName, setLastName)}
        </div>
        {textField("email", "Email *", email, setEmail, "email")}
        {textField("jobTitle", "Job title", jobTitle, setJobTitle, "text", "e.g. Developer, QA Engineer")}

        <div className="field">
          <label htmlFor="employee-teamId">Team</label>
          <select
            id="employee-teamId"
            value={teamId}
            onChange={(e) => setTeamId(e.target.value)}
            aria-invalid={!!errors.teamId}
          >
            <option value="">No team</option>
            {teamOptions.map((t) => (
              <option key={t.id} value={t.id}>{t.name}{t.status === "INACTIVE" ? " (inactive)" : ""}</option>
            ))}
          </select>
          <p className="hint">Only active teams can be chosen.</p>
          {errors.teamId && <p className="field-error">{errors.teamId}</p>}
        </div>

        <div className="form-row">
          <div className="field">
            <label htmlFor="employee-employmentType">Employment type *</label>
            <select
              id="employee-employmentType"
              value={employmentType}
              onChange={(e) => setEmploymentType(e.target.value as EmploymentType)}
            >
              <option value="PERMANENT">Permanent</option>
              <option value="CONTRACT">Contract</option>
            </select>
          </div>
          {textField("workingTimeShare", "Working-time share (FTE) *", fte, setFte, "number", "1 = full-time, 0.5 = half-time")}
        </div>

        <div className="form-row">
          {textField("startDate", "Start date *", startDate, setStartDate, "date")}
          {employmentType === "CONTRACT" && textField("endDate", "End date *", endDate, setEndDate, "date")}
        </div>

        {textField("employeeRef", "Employee reference", employeeRef, setEmployeeRef, "text", "Optional, e.g. the ID from Onboarding (G2-5531).")}

        <div className="actions">
          <button type="submit" className="primary" disabled={saving || !canSubmit}>
            {saving ? "Saving…" : "Save"}
          </button>
          <button type="button" onClick={onCancel} disabled={saving}>Cancel</button>
        </div>
      </form>
    </>
  );
}