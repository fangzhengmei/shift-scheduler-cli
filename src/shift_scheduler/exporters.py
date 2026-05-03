import csv
from datetime import date, time
from pathlib import Path
from typing import List, Dict, Set, Optional
from collections import defaultdict

from .models import (
    Employee,
    Shift,
    Assignment,
    Conflict,
    Schedule
)


class MarkdownExporter:
    def __init__(
        self,
        employees: List[Employee],
        shifts: List[Shift],
        schedule: Schedule
    ):
        self.employees = {e.id: e for e in employees}
        self.shifts = {s.id: s for s in shifts}
        self.schedule = schedule

    def export(self) -> str:
        lines = []

        lines.append("# 排班表")
        lines.append("")
        lines.append(f"生成日期: {date.today().isoformat()}")
        lines.append("")

        lines.append("## 班次分配")
        lines.append("")

        lines.append(self._generate_by_shift_table())
        lines.append("")

        lines.append("## 员工排班")
        lines.append("")
        lines.append(self._generate_by_employee_table())
        lines.append("")

        if self.schedule.has_conflicts():
            lines.append("## 冲突警告")
            lines.append("")
            for conflict in self.schedule.conflicts:
                lines.append(f"- **{conflict.conflict_type.value}**: {conflict.message}")
            lines.append("")

        lines.append("## 统计信息")
        lines.append("")
        lines.append(self._generate_statistics())

        return "\n".join(lines)

    def _generate_by_shift_table(self) -> str:
        lines = []

        lines.append("| 班次ID | 日期 | 时间 | 需要人数 | 已分配 | 员工 |")
        lines.append("|--------|------|------|----------|--------|------|")

        sorted_shifts = sorted(
            self.shifts.values(),
            key=lambda s: (s.date, s.start_time)
        )

        for shift in sorted_shifts:
            assignments = self.schedule.get_assignments_for_shift(shift.id)
            assigned_employees = [
                self.employees[a.employee_id].name for a in assignments
            ]
            assigned_count = len(assignments)

            time_str = f"{shift.start_time.strftime('%H:%M')} - {shift.end_time.strftime('%H:%M')}"
            employees_str = ", ".join(assigned_employees) if assigned_employees else "-"

            lines.append(
                f"| {shift.id} | {shift.date.isoformat()} | {time_str} | "
                f"{shift.required_employees} | {assigned_count} | {employees_str} |"
            )

        return "\n".join(lines)

    def _generate_by_employee_table(self) -> str:
        lines = []

        lines.append("| 员工ID | 姓名 | 班次数量 | 分配班次 |")
        lines.append("|--------|------|----------|----------|")

        sorted_employees = sorted(
            self.employees.values(),
            key=lambda e: e.name
        )

        for employee in sorted_employees:
            assignments = self.schedule.get_assignments_for_employee(employee.id)
            shift_count = len(assignments)

            assigned_shifts = []
            for a in assignments:
                shift = self.shifts[a.shift_id]
                assigned_shifts.append(
                    f"{shift.date.isoformat()} {shift.start_time.strftime('%H:%M')}-{shift.end_time.strftime('%H:%M')}"
                )

            shifts_str = ", ".join(assigned_shifts) if assigned_shifts else "-"

            lines.append(
                f"| {employee.id} | {employee.name} | {shift_count} | {shifts_str} |"
            )

        return "\n".join(lines)

    def _generate_statistics(self) -> str:
        lines = []

        total_assignments = len(self.schedule.assignments)
        total_employees = len(self.employees)
        total_shifts = len(self.shifts)

        shifts_by_date: Dict[date, int] = defaultdict(int)
        for shift in self.shifts.values():
            shifts_by_date[shift.date] += 1

        assigned_shifts_by_date: Dict[date, int] = defaultdict(int)
        for assignment in self.schedule.assignments:
            shift = self.shifts[assignment.shift_id]
            assigned_shifts_by_date[shift.date] += 1

        lines.append(f"- **总员工数**: {total_employees}")
        lines.append(f"- **总班次**: {total_shifts}")
        lines.append(f"- **总分配次数**: {total_assignments}")
        lines.append("")

        if shifts_by_date:
            lines.append("### 按日期统计")
            lines.append("")
            lines.append("| 日期 | 班次数 | 已分配 |")
            lines.append("|------|--------|--------|")

            for d in sorted(shifts_by_date.keys()):
                lines.append(f"| {d.isoformat()} | {shifts_by_date[d]} | {assigned_shifts_by_date.get(d, 0)} |")

        return "\n".join(lines)

    def save(self, file_path: Path) -> None:
        content = self.export()
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)


class CSVExporter:
    def __init__(
        self,
        employees: List[Employee],
        shifts: List[Shift],
        schedule: Schedule
    ):
        self.employees = {e.id: e for e in employees}
        self.shifts = {s.id: s for s in shifts}
        self.schedule = schedule

    def export_assignments(self) -> List[Dict]:
        rows = []

        for assignment in self.schedule.assignments:
            employee = self.employees[assignment.employee_id]
            shift = self.shifts[assignment.shift_id]

            rows.append({
                'employee_id': employee.id,
                'employee_name': employee.name,
                'shift_id': shift.id,
                'date': shift.date.isoformat(),
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'required_employees': shift.required_employees
            })

        return rows

    def export_shifts(self) -> List[Dict]:
        rows = []

        sorted_shifts = sorted(
            self.shifts.values(),
            key=lambda s: (s.date, s.start_time)
        )

        for shift in sorted_shifts:
            assignments = self.schedule.get_assignments_for_shift(shift.id)
            assigned_employees = [
                self.employees[a.employee_id].name for a in assignments
            ]

            rows.append({
                'shift_id': shift.id,
                'date': shift.date.isoformat(),
                'start_time': shift.start_time.strftime('%H:%M'),
                'end_time': shift.end_time.strftime('%H:%M'),
                'required_employees': shift.required_employees,
                'assigned_count': len(assignments),
                'assigned_employees': ", ".join(assigned_employees)
            })

        return rows

    def export_employees(self) -> List[Dict]:
        rows = []

        sorted_employees = sorted(
            self.employees.values(),
            key=lambda e: e.name
        )

        for employee in sorted_employees:
            assignments = self.schedule.get_assignments_for_employee(employee.id)

            assigned_shifts = []
            for a in assignments:
                shift = self.shifts[a.shift_id]
                assigned_shifts.append(
                    f"{shift.date.isoformat()} {shift.start_time.strftime('%H:%M')}-{shift.end_time.strftime('%H:%M')}"
                )

            rows.append({
                'employee_id': employee.id,
                'employee_name': employee.name,
                'shift_count': len(assignments),
                'assigned_shifts': ", ".join(assigned_shifts)
            })

        return rows

    def export_conflicts(self) -> List[Dict]:
        rows = []

        for conflict in self.schedule.conflicts:
            employee_name = ""
            if conflict.employee_id and conflict.employee_id in self.employees:
                employee_name = self.employees[conflict.employee_id].name

            rows.append({
                'conflict_type': conflict.conflict_type.value,
                'employee_id': conflict.employee_id or "",
                'employee_name': employee_name,
                'shift_id': conflict.shift_id or "",
                'message': conflict.message
            })

        return rows

    def save_assignments(self, file_path: Path) -> None:
        rows = self.export_assignments()
        if not rows:
            return

        fieldnames = [
            'employee_id', 'employee_name', 'shift_id',
            'date', 'start_time', 'end_time', 'required_employees'
        ]

        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def save_shifts(self, file_path: Path) -> None:
        rows = self.export_shifts()
        if not rows:
            return

        fieldnames = [
            'shift_id', 'date', 'start_time', 'end_time',
            'required_employees', 'assigned_count', 'assigned_employees'
        ]

        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def save_employees(self, file_path: Path) -> None:
        rows = self.export_employees()
        if not rows:
            return

        fieldnames = [
            'employee_id', 'employee_name', 'shift_count', 'assigned_shifts'
        ]

        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def save_conflicts(self, file_path: Path) -> None:
        rows = self.export_conflicts()
        if not rows:
            return

        fieldnames = [
            'conflict_type', 'employee_id', 'employee_name',
            'shift_id', 'message'
        ]

        with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
