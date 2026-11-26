/** EM-FE-03 Edit an employee or move them to another team. Only HR Admin may use it. */
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError, DemoUser } from "../api/client";
import { Employee, fullName, getEmployee, updateEmployee } from "../api/employees";
import EmployeeForm from "../components/EmployeeForm";

interface Props {
  user: DemoUser;
}

export default function EditEmployeePage({ user }: Props) {
  const employeeId = Number(useParams().employeeId);       // the 5 in /employees/5/edit
  const navigate = useNavigate();
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {                   // Load the current data for the form
    setLoading(true);
    setError("");
    setNotFound(false);
    try {
      setEmployee(await getEmployee(employeeId));
    } catch (err) {
      if (err instanceof ApiError && (err.code === "NOT_FOUND" || err.code === "VALIDATION_ERROR")) setNotFound(true);
      else setError(err instanceof ApiError ? err.message : "Could not load the employee.");
    } finally {
      setLoading(false);
    }
  }, [employeeId]);

  useEffect(() => {
    load();
  }, [load]);

  const details = `/employees/${employeeId}`;
  const back = <Link to={details} className="back">← Back to employee</Link>;

  if (loading) return <section>{back}<p className="hint" role="status">Loading employee…</p></section>;
  if (notFound) {
    return (
      <section>
        <Link to="/employees" className="back">← Back to employees</Link>
        <h2>Employee not found</h2>
      </section>
    );
  }
  if (error || !employee) {
    return (
      <section>
        <Link to="/employees" className="back">← Back to employees</Link>
        <div className="form-error" role="alert">{error} <button onClick={load}>Retry</button></div>
      </section>
    );
  }

  // Someone who typed the edit address without being HR Admin (the backend would answer 403 too)
  if (user.role !== "HR_ADMIN") {
    return (
      <section>
        {back}
        <h2>Not allowed</h2>
        <p className="notice">Only HR Admins can edit employees.</p>
      </section>
    );
  }

  return (
    <section>
      {back}
      <h2>Edit {fullName(employee)}</h2>
      <EmployeeForm
        initial={employee}
        canSubmit
        onSubmit={async (values) => {
          const saved = await updateEmployee(employee.id, values);          // PATCH /api/v1/employees/5
          navigate(details, { state: { message: `Employee “${fullName(saved)}” was updated.` } });
        }}
        onCancel={() => navigate(details)}
      />
    </section>
  );
}