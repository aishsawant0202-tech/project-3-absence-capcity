/**
 * The team form used by Create (TM-01) and Edit (TM-04), so both have exactly the same fields and checks.
 * The page decides what Save does (POST or PATCH) through `onSubmit`.
 */
import { FormEvent, useState } from "react";
import { ApiError } from "../api/client";
import { TeamCreate } from "../api/teams";

type Field = "name" | "description" | "minRequiredFte"; // same names as the API fields
const FIELDS: Field[] = ["name", "description", "minRequiredFte"];
type Errors = Partial<Record<Field, string>>;

const NAME_MAX = 100; // String(100) in the Team model
const FTE_MAX = 999.99; // Numeric(5, 2)

export interface TeamFormValues {
  name: string;
  description: string | null;
  minRequiredFte: number;
}

interface Props {
  initial?: TeamFormValues; // Edit: the current values; Create: empty form
  canSubmit: boolean; // false -> Save disabled (e.g. wrong role); the backend checks again
  onSubmit: (values: TeamCreate) => Promise<void>; // throws ApiError on failure
  onCancel: () => void;
}

/** Client-side checks; the backend repeats them (400 VALIDATION_ERROR). */
function validate(name: string, fte: string): Errors {
  const errors: Errors = {};
  const trimmed = name.trim();
  if (!trimmed) errors.name = "Team name is required.";
  else if (trimmed.length > NAME_MAX) errors.name = `Team name can have at most ${NAME_MAX} characters.`;

  const value = Number(fte);
  if (fte.trim() === "") errors.minRequiredFte = "Minimum required capacity is required.";
  else if (!Number.isFinite(value)) errors.minRequiredFte = "Enter a number, e.g. 5 or 2.5.";
  else if (value < 0) errors.minRequiredFte = "Capacity must be 0 or more.";
  else if (value > FTE_MAX) errors.minRequiredFte = `Capacity can be at most ${FTE_MAX}.`;
  else if (!/^\d+(\.\d{1,2})?$/.test(fte.trim())) errors.minRequiredFte = "Use at most 2 decimal places.";
  return errors;
}

export default function TeamForm({ initial, canSubmit, onSubmit, onCancel }: Props) {
  const [name, setName] = useState(initial?.name ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [fte, setFte] = useState(initial ? String(initial.minRequiredFte) : "");
  const [errors, setErrors] = useState<Errors>({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setFormError("");
    const found = validate(name, fte);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    setSaving(true);
    try {
      await onSubmit({ name: name.trim(), description: description.trim() || null, minRequiredFte: Number(fte) });
    } catch (err) {
      if (!(err instanceof ApiError)) {
        setFormError("Something went wrong. Please try again.");
      } else if (err.code === "TEAM_NAME_TAKEN") {
        setErrors({ name: err.message }); // shown under the name field
      } else if (err.code === "VALIDATION_ERROR" && err.fieldErrors.length > 0) {
        const fromServer: Errors = {};
        for (const fe of err.fieldErrors) {
          const field = FIELDS.find((f) => f === fe.field);
          if (field) fromServer[field] = fe.message;
        }
        setErrors(fromServer);
        if (Object.keys(fromServer).length === 0) setFormError(err.message);
      } else {
        // UNAUTHENTICATED, FORBIDDEN, NOT_FOUND, ALREADY_TEAM_LEAD, server down: above the form
        setFormError(err.message);
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      {formError && <p className="form-error" role="alert">{formError}</p>}

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="team-name">Team name *</label>
          <input
            id="team-name"
            value={name}
            maxLength={NAME_MAX}
            onChange={(e) => setName(e.target.value)}
            aria-invalid={!!errors.name}
            aria-describedby={errors.name ? "team-name-error" : undefined}
          />
          {errors.name && <p id="team-name-error" className="field-error">{errors.name}</p>}
        </div>

        <div className="field">
          <label htmlFor="team-description">Description</label>
          <textarea
            id="team-description"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          {errors.description && <p className="field-error">{errors.description}</p>}
        </div>

        <div className="field">
          <label htmlFor="team-fte">Minimum required capacity (FTE) *</label>
          <input
            id="team-fte"
            type="number"
            min={0}
            max={FTE_MAX}
            step={0.01}
            value={fte}
            onChange={(e) => setFte(e.target.value)}
            aria-invalid={!!errors.minRequiredFte}
            aria-describedby={errors.minRequiredFte ? "team-fte-error" : "team-fte-hint"}
          />
          <p id="team-fte-hint" className="hint">Full-time equivalents, e.g. 5 or 2.5.</p>
          {errors.minRequiredFte && <p id="team-fte-error" className="field-error">{errors.minRequiredFte}</p>}
        </div>

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
