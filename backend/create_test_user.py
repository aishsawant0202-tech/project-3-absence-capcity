
from datetime import date

from app.database import SessionLocal
from app.models import (
    Employee,
    EmployeeStatus,
    EmploymentType,
    UserAccount,
    SystemRole,
    AccountStatus,
)
from app.security import hash_password


db = SessionLocal()

try:
    username = "testuser"
    password = "TestPassword123!"

    # Check whether the account already exists
    existing = db.query(UserAccount).filter_by(
        username=username
    ).first()

    if existing:
        print("Test user already exists.")
    else:
        # Create employee
        employee = Employee(
            first_name="Test",
            last_name="User",
            email="testuser@example.com",
            employment_type=EmploymentType.PERMANENT,
            working_time_share=1.00,
            start_date=date.today(),
            status=EmployeeStatus.ACTIVE,
        )

        db.add(employee)
        db.flush()

        # Create linked user account
        account = UserAccount(
            employee_id=employee.id,
            username=username,
            password_hash=hash_password(password),
            system_role=SystemRole.HR_ADMIN,
            status=AccountStatus.ACTIVE,
            must_change_password=False,
        )

        db.add(account)
        db.commit()

        print("Test account created successfully.")
        print("Username:", username)
        print("Employee ID:", employee.id)
        print("Account ID:", account.id)

except Exception:
    db.rollback()
    raise

finally:
    db.close()
