"""Generate fake HR and payroll extracts for two days into landing/."""
import csv
import json
import random
from datetime import date
from pathlib import Path

from faker import Faker

fake = Faker("en_AU")
random.seed(42)
Faker.seed(42)

LANDING = Path(__file__).resolve().parent.parent / "landing"

DEPARTMENTS = [
    {"department_code": "ENG", "department_name": "Engineering", "cost_centre": "CC100"},
    {"department_code": "SALES", "department_name": "Sales", "cost_centre": "CC200"},
    {"department_code": "FIN", "department_name": "Finance", "cost_centre": "CC300"},
    {"department_code": "HR", "department_name": "Human Resources", "cost_centre": "CC400"},
    {"department_code": "OPS", "department_name": "Operations", "cost_centre": "CC500"},
]
JOB_TITLES = {
    "ENG": ["Engineer", "Senior Engineer"],
    "SALES": ["Account Executive", "Sales Manager"],
    "FIN": ["Analyst", "Accountant"],
    "HR": ["HR Advisor"],
    "OPS": ["Operations Officer"],
}
LOCATIONS = ["Melbourne", "Sydney", "Brisbane"]


def make_employee(n, as_of):
    dept = random.choice(DEPARTMENTS)["department_code"]
    first, last = fake.first_name(), fake.last_name()
    return {
        "employee_id": f"E{n:03d}",
        "first_name": first,
        "last_name": last,
        "email": f"{first}.{last}@example.com".lower(),
        "department_code": dept,
        "job_title": random.choice(JOB_TITLES[dept]),
        "location": random.choice(LOCATIONS),
        "employment_status": "active",
        "hire_date": fake.date_between(start_date="-5y", end_date="-2m").isoformat(),
        "termination_date": None,
        "last_modified": f"{as_of.isoformat()}T09:00:00",
    }


def payroll_lines(employees, salaries, pay_run_id, pay_date):
    lines = []
    for e in employees:
        if e["employment_status"] != "active":
            continue
        base = salaries[e["employee_id"]]
        gross = base
        lines.append((e["employee_id"], "BASE", base))
        if random.random() < 0.3:
            overtime = random.randrange(100, 601, 50)
            gross += overtime
            lines.append((e["employee_id"], "OVERTIME", overtime))
        lines.append((e["employee_id"], "TAX", -round(gross * 0.25, 2)))
        lines.append((e["employee_id"], "SUPER", round(gross * 0.12, 2)))
    return [
        {"pay_run_id": pay_run_id, "pay_date": pay_date.isoformat(),
         "employee_id": emp, "pay_component": comp, "amount": amt}
        for emp, comp, amt in lines
    ]


def write_day(day, employees, departments, lines):
    folder = LANDING / day.isoformat()
    folder.mkdir(parents=True, exist_ok=True)

    with open(folder / "employees.json", "w") as f:
        json.dump(employees, f, indent=2)

    with open(folder / "departments.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=departments[0].keys())
        writer.writeheader()
        writer.writerows(departments)

    with open(folder / "payroll_lines.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=lines[0].keys())
        writer.writeheader()
        writer.writerows(lines)

    print(f"{folder.name}: {len(employees)} employees, {len(lines)} payroll lines")


def main():
    # Day 1: 50 employees, first pay run
    day1 = date(2026, 10, 15)
    employees = [make_employee(n, day1) for n in range(1, 51)]
    salaries = {e["employee_id"]: random.randrange(3000, 6001, 50) for e in employees}
    write_day(day1, employees, DEPARTMENTS,
              payroll_lines(employees, salaries, "PR-001", day1))

    # Day 2: changes that the warehouse must handle
    day2 = date(2026, 10, 29)
    stamp = f"{day2.isoformat()}T09:00:00"
    by_id = {e["employee_id"]: e for e in employees}

    by_id["E005"].update(department_code="SALES", job_title="Account Executive", last_modified=stamp)
    by_id["E012"].update(department_code="FIN", job_title="Analyst", last_modified=stamp)
    by_id["E020"].update(employment_status="terminated", termination_date="2026-10-25", last_modified=stamp)

    new_hire = make_employee(51, day2)
    new_hire["hire_date"] = "2026-10-20"
    employees.append(new_hire)
    salaries["E051"] = 4500

    lines = payroll_lines(employees, salaries, "PR-002", day2)
    lines.append({"pay_run_id": "PR-002", "pay_date": day2.isoformat(),
                  "employee_id": "", "pay_component": "BASE", "amount": 1000})  # bad row
    write_day(day2, employees, DEPARTMENTS, lines)


if __name__ == "__main__":
    main()