import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import (
    Employee,
    Shift,
    Assignment,
    Conflict,
    ConflictType,
    Schedule
)


class Storage:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.employees_file = data_dir / "employees.json"
        self.shifts_file = data_dir / "shifts.json"
        self.schedule_file = data_dir / "schedule.json"

    def save_employees(self, employees: List[Employee]) -> None:
        data = [e.to_dict() for e in employees]
        with open(self.employees_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_employees(self) -> List[Employee]:
        if not self.employees_file.exists():
            return []

        with open(self.employees_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return [Employee.from_dict(item) for item in data]

    def save_shifts(self, shifts: List[Shift]) -> None:
        data = [s.to_dict() for s in shifts]
        with open(self.shifts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_shifts(self) -> List[Shift]:
        if not self.shifts_file.exists():
            return []

        with open(self.shifts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return [Shift.from_dict(item) for item in data]

    def save_schedule(self, schedule: Schedule) -> None:
        data = schedule.to_dict()
        with open(self.schedule_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_schedule(self) -> Optional[Schedule]:
        if not self.schedule_file.exists():
            return None

        with open(self.schedule_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assignments = [Assignment.from_dict(a) for a in data.get('assignments', [])]
        conflicts = []
        for c_data in data.get('conflicts', []):
            conflicts.append(Conflict(
                conflict_type=ConflictType(c_data['conflict_type']),
                employee_id=c_data.get('employee_id'),
                shift_id=c_data.get('shift_id'),
                message=c_data.get('message', '')
            ))

        return Schedule(assignments=assignments, conflicts=conflicts)

    def clear_all(self) -> None:
        for file in [self.employees_file, self.shifts_file, self.schedule_file]:
            if file.exists():
                file.unlink()
