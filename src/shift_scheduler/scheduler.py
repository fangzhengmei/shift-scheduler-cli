from typing import List, Dict, Set, Tuple
from collections import defaultdict

from .models import (
    Employee,
    Shift,
    Assignment,
    Conflict,
    ConflictType,
    Schedule
)


class ShiftScheduler:
    def __init__(self, employees: List[Employee], shifts: List[Shift]):
        self.employees = {e.id: e for e in employees}
        self.shifts = {s.id: s for s in shifts}
        self._employee_by_id = {e.id: e for e in employees}
        self._shift_by_id = {s.id: s for s in shifts}

    def schedule(self) -> Schedule:
        assignments: List[Assignment] = []
        conflicts: List[Conflict] = []

        employee_assignments: Dict[str, List[str]] = defaultdict(list)

        sorted_shifts = sorted(
            self.shifts.values(),
            key=lambda s: (s.date, s.start_time)
        )

        for shift in sorted_shifts:
            eligible_employees = self._get_eligible_employees(
                shift,
                employee_assignments
            )

            assigned_count = 0
            for employee in eligible_employees:
                if assigned_count >= shift.required_employees:
                    break

                if not self._would_cause_overlap(
                    employee.id,
                    shift,
                    employee_assignments
                ):
                    assignment = Assignment(employee.id, shift.id)
                    assignments.append(assignment)
                    employee_assignments[employee.id].append(shift.id)
                    assigned_count += 1

            if assigned_count < shift.required_employees:
                conflicts.append(Conflict(
                    conflict_type=ConflictType.UNDERSTAFFED,
                    shift_id=shift.id,
                    message=f"Shift {shift.id} needs {shift.required_employees} employees, "
                            f"but only {assigned_count} were assigned"
                ))

        return Schedule(assignments=assignments, conflicts=conflicts)

    def _get_eligible_employees(
        self,
        shift: Shift,
        employee_assignments: Dict[str, List[str]]
    ) -> List[Employee]:
        eligible = []

        for employee in self.employees.values():
            if employee.is_available(shift):
                if shift.required_skills:
                    if not shift.required_skills.issubset(employee.skills):
                        continue
                eligible.append(employee)

        eligible.sort(key=lambda e: len(employee_assignments[e.id]))

        return eligible

    def _would_cause_overlap(
        self,
        employee_id: str,
        new_shift: Shift,
        employee_assignments: Dict[str, List[str]]
    ) -> bool:
        assigned_shift_ids = employee_assignments.get(employee_id, [])

        for shift_id in assigned_shift_ids:
            assigned_shift = self.shifts[shift_id]
            if new_shift.overlaps_with(assigned_shift):
                return True

        return False

    def check_conflicts(self, schedule: Schedule) -> List[Conflict]:
        conflicts: List[Conflict] = []

        for assignment in schedule.assignments:
            employee = self._employee_by_id.get(assignment.employee_id)
            shift = self._shift_by_id.get(assignment.shift_id)

            if not employee or not shift:
                continue

            if not employee.is_available(shift):
                conflicts.append(Conflict(
                    conflict_type=ConflictType.UNAVAILABLE,
                    employee_id=employee.id,
                    shift_id=shift.id,
                    message=f"Employee {employee.name} is not available for shift {shift.id}"
                ))

            if shift.required_skills:
                if not shift.required_skills.issubset(employee.skills):
                    missing_skills = shift.required_skills - employee.skills
                    conflicts.append(Conflict(
                        conflict_type=ConflictType.INSUFFICIENT_SKILLS,
                        employee_id=employee.id,
                        shift_id=shift.id,
                        message=f"Employee {employee.name} missing skills: {', '.join(missing_skills)}"
                    ))

        employee_shift_map: Dict[str, List[Shift]] = defaultdict(list)
        for assignment in schedule.assignments:
            employee = self._employee_by_id.get(assignment.employee_id)
            shift = self._shift_by_id.get(assignment.shift_id)
            if employee and shift:
                employee_shift_map[employee.id].append(shift)

        for employee_id, shifts in employee_shift_map.items():
            shifts_sorted = sorted(shifts, key=lambda s: (s.date, s.start_time))
            employee = self._employee_by_id[employee_id]

            for i in range(len(shifts_sorted)):
                for j in range(i + 1, len(shifts_sorted)):
                    if shifts_sorted[i].overlaps_with(shifts_sorted[j]):
                        conflicts.append(Conflict(
                            conflict_type=ConflictType.OVERLAPPING,
                            employee_id=employee.id,
                            shift_id=shifts_sorted[i].id,
                            message=f"Employee {employee.name} has overlapping shifts: "
                                    f"{shifts_sorted[i].id} and {shifts_sorted[j].id}"
                        ))

        for shift_id, shift in self.shifts.items():
            assigned_count = len([
                a for a in schedule.assignments if a.shift_id == shift_id
            ])
            if assigned_count < shift.required_employees:
                conflicts.append(Conflict(
                    conflict_type=ConflictType.UNDERSTAFFED,
                    shift_id=shift_id,
                    message=f"Shift {shift_id} needs {shift.required_employees} employees, "
                            f"but only {assigned_count} were assigned"
                ))

        return self._deduplicate_conflicts(conflicts)

    def _deduplicate_conflicts(self, conflicts: List[Conflict]) -> List[Conflict]:
        seen = set()
        unique = []

        for conflict in conflicts:
            key = (
                conflict.conflict_type.value,
                conflict.employee_id,
                conflict.shift_id,
                conflict.message
            )
            if key not in seen:
                seen.add(key)
                unique.append(conflict)

        return unique

    def get_available_employees_for_shift(self, shift_id: str) -> List[Employee]:
        shift = self.shifts.get(shift_id)
        if not shift:
            return []

        available = []
        for employee in self.employees.values():
            if employee.is_available(shift):
                if shift.required_skills:
                    if shift.required_skills.issubset(employee.skills):
                        available.append(employee)
                else:
                    available.append(employee)

        return available

    def get_employee_shifts(self, employee_id: str, schedule: Schedule) -> List[Shift]:
        employee = self.employees.get(employee_id)
        if not employee:
            return []

        assignments = schedule.get_assignments_for_employee(employee_id)
        return [self.shifts[a.shift_id] for a in assignments]
