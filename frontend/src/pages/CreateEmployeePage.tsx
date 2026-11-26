/** EM-FE-02 Add an employee. The fields and checks are in components/EmployeeForm.tsx (shared with Edit). */
import { Link, useNavigate } from "react-router-dom";
import { DemoUser } from "../api/client";
import { createEmployee, fullName } from "../api/employees";
import EmployeeForm from "../components/EmployeeForm";

interface Props {
  user: DemoUser; // only HR_ADMIN may add employees; the backend checks again (403)
}

export default function CreateEmployeePage({ user }: Props) {
  const navigate = useNavigate();
  const isHr = user.role === "HR_ADMIN";

  return (
    <section>
      <Link to="/employees" className="back">← Back to employees</Link>
      <h2>Add employee</h2>
      {!isHr && (
        <p className="notice">Only HR Admins can add employees. Switch the demo login role to HR_ADMIN.</p>
      )}
      <EmployeeForm
        canSubmit={isHr}
        onSubmit={async (values) => {
          const saved = await createEmployee(values);                       // POST /api/v1/employees
          navigate("/employees", { state: { message: `Employee “${fullName(saved)}” was added.` } });
        }}
        onCancel={() => navigate("/employees")}
      />
    </section>
  );
}