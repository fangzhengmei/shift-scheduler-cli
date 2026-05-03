import pytest
import tempfile
import csv
from datetime import date, time
from pathlib import Path

from shift_scheduler.models import (
    Employee,
    Shift,
    TimeSlot,
    DayOfWeek,
    Assignment,
    Conflict,
    ConflictType,
    Schedule
)
from shift_scheduler.exporters import MarkdownExporter, CSVExporter


class TestMarkdownExporter:
    def test_export_basic(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="张三", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        schedule = Schedule(assignments=[Assignment("e1", "s1")])

        exporter = MarkdownExporter([employee], [shift], schedule)
        content = exporter.export()

        assert "# 排班表" in content
        assert "张三" in content
        assert "s1" in content

    def test_export_with_conflicts(self):
        employee = Employee(id="e1", name="张三")
        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        conflict = Conflict(
            conflict_type=ConflictType.UNDERSTAFFED,
            shift_id="s1",
            message="Shift needs more employees"
        )
        schedule = Schedule(conflicts=[conflict])

        exporter = MarkdownExporter([employee], [shift], schedule)
        content = exporter.export()

        assert "## 冲突警告" in content
        assert "understaffed" in content

    def test_save_to_file(self):
        employee = Employee(id="e1", name="张三")
        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        schedule = Schedule(assignments=[Assignment("e1", "s1")])

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "schedule.md"
            exporter = MarkdownExporter([employee], [shift], schedule)
            exporter.save(file_path)

            assert file_path.exists()
            content = file_path.read_text(encoding='utf-8')
            assert "# 排班表" in content


class TestCSVExporter:
    def test_export_assignments(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="张三", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        schedule = Schedule(assignments=[Assignment("e1", "s1")])

        exporter = CSVExporter([employee], [shift], schedule)
        rows = exporter.export_assignments()

        assert len(rows) == 1
        assert rows[0]['employee_id'] == "e1"
        assert rows[0]['employee_name'] == "张三"
        assert rows[0]['shift_id'] == "s1"
        assert rows[0]['date'] == "2026-05-04"

    def test_export_shifts(self):
        employee = Employee(id="e1", name="张三")
        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0),
            required_employees=2
        )

        schedule = Schedule(assignments=[Assignment("e1", "s1")])

        exporter = CSVExporter([employee], [shift], schedule)
        rows = exporter.export_shifts()

        assert len(rows) == 1
        assert rows[0]['shift_id'] == "s1"
        assert rows[0]['required_employees'] == 2
        assert rows[0]['assigned_count'] == 1
        assert "张三" in rows[0]['assigned_employees']

    def test_export_employees(self):
        employee1 = Employee(id="e1", name="张三")
        employee2 = Employee(id="e2", name="李四")

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        schedule = Schedule(assignments=[Assignment("e1", "s1")])

        exporter = CSVExporter([employee1, employee2], [shift], schedule)
        rows = exporter.export_employees()

        assert len(rows) == 2

        for row in rows:
            if row['employee_id'] == "e1":
                assert row['employee_name'] == "张三"
                assert row['shift_count'] == 1
            else:
                assert row['employee_name'] == "李四"
                assert row['shift_count'] == 0

    def test_export_conflicts(self):
        employee = Employee(id="e1", name="张三")
        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        conflict = Conflict(
            conflict_type=ConflictType.UNAVAILABLE,
            employee_id="e1",
            shift_id="s1",
            message="Employee not available"
        )
        schedule = Schedule(conflicts=[conflict])

        exporter = CSVExporter([employee], [shift], schedule)
        rows = exporter.export_conflicts()

        assert len(rows) == 1
        assert rows[0]['conflict_type'] == "unavailable"
        assert rows[0]['employee_id'] == "e1"
        assert rows[0]['employee_name'] == "张三"
        assert rows[0]['shift_id'] == "s1"

    def test_save_assignments(self):
        employee = Employee(id="e1", name="张三")
        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        schedule = Schedule(assignments=[Assignment("e1", "s1")])

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "assignments.csv"
            exporter = CSVExporter([employee], [shift], schedule)
            exporter.save_assignments(file_path)

            assert file_path.exists()

            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 1
            assert rows[0]['employee_id'] == "e1"
            assert rows[0]['employee_name'] == "张三"

    def test_save_shifts(self):
        employee = Employee(id="e1", name="张三")
        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        schedule = Schedule(assignments=[Assignment("e1", "s1")])

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "shifts.csv"
            exporter = CSVExporter([employee], [shift], schedule)
            exporter.save_shifts(file_path)

            assert file_path.exists()

    def test_save_employees(self):
        employee = Employee(id="e1", name="张三")
        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        schedule = Schedule(assignments=[Assignment("e1", "s1")])

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "employees.csv"
            exporter = CSVExporter([employee], [shift], schedule)
            exporter.save_employees(file_path)

            assert file_path.exists()

    def test_save_conflicts(self):
        employee = Employee(id="e1", name="张三")
        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        conflict = Conflict(
            conflict_type=ConflictType.UNDERSTAFFED,
            shift_id="s1",
            message="Test conflict"
        )
        schedule = Schedule(conflicts=[conflict])

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "conflicts.csv"
            exporter = CSVExporter([employee], [shift], schedule)
            exporter.save_conflicts(file_path)

            assert file_path.exists()

    def test_empty_assignments_no_file(self):
        employee = Employee(id="e1", name="张三")
        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        schedule = Schedule()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "assignments.csv"
            exporter = CSVExporter([employee], [shift], schedule)
            exporter.save_assignments(file_path)

            assert not file_path.exists()
