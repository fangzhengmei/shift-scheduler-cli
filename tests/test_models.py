import pytest
from datetime import date, time, datetime, timedelta

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


class TestTimeSlot:
    def test_overlaps_with_same_day_overlapping(self):
        slot1 = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        slot2 = TimeSlot(DayOfWeek.MONDAY, time(10, 0), time(18, 0))
        assert slot1.overlaps_with(slot2) is True

    def test_overlaps_with_same_day_non_overlapping(self):
        slot1 = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(12, 0))
        slot2 = TimeSlot(DayOfWeek.MONDAY, time(13, 0), time(17, 0))
        assert slot1.overlaps_with(slot2) is False

    def test_overlaps_with_different_day(self):
        slot1 = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        slot2 = TimeSlot(DayOfWeek.TUESDAY, time(9, 0), time(17, 0))
        assert slot1.overlaps_with(slot2) is False

    def test_to_dict_and_from_dict(self):
        slot = TimeSlot(DayOfWeek.WEDNESDAY, time(8, 30), time(16, 30))
        data = slot.to_dict()

        assert data['day_of_week'] == DayOfWeek.WEDNESDAY.value
        assert data['start_time'] == '08:30'
        assert data['end_time'] == '16:30'

        restored = TimeSlot.from_dict(data)
        assert restored.day_of_week == DayOfWeek.WEDNESDAY
        assert restored.start_time == time(8, 30)
        assert restored.end_time == time(16, 30)


class TestEmployee:
    def test_is_available_available_slot(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="Test", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        assert employee.is_available(shift) is True

    def test_is_available_shift_fully_covered(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="Test", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(10, 0),
            end_time=time(16, 0)
        )

        assert employee.is_available(shift) is True

    def test_is_available_exact_match(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="Test", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        assert employee.is_available(shift) is True

    def test_is_available_shift_starts_before_slot(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="Test", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(8, 0),
            end_time=time(16, 0)
        )

        assert employee.is_available(shift) is False

    def test_is_available_shift_ends_after_slot(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="Test", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(10, 0),
            end_time=time(18, 0)
        )

        assert employee.is_available(shift) is False

    def test_is_available_partial_overlap_not_covered(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(12, 0))
        employee = Employee(id="e1", name="Test", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(11, 0),
            end_time=time(13, 0)
        )

        assert employee.is_available(shift) is False

    def test_is_available_boundary_exact_start(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="Test", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(12, 0)
        )

        assert employee.is_available(shift) is True

    def test_is_available_boundary_exact_end(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="Test", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(14, 0),
            end_time=time(17, 0)
        )

        assert employee.is_available(shift) is True

    def test_is_available_no_overlap(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(12, 0))
        employee = Employee(id="e1", name="Test", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(13, 0),
            end_time=time(17, 0)
        )

        assert employee.is_available(shift) is False

    def test_is_available_different_day(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="Test", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 5),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        assert employee.is_available(shift) is False

    def test_to_dict_and_from_dict(self):
        slot = TimeSlot(DayOfWeek.FRIDAY, time(9, 0), time(17, 0))
        employee = Employee(
            id="emp001",
            name="张三",
            available_slots=[slot],
            skills={"python", "testing"}
        )

        data = employee.to_dict()
        restored = Employee.from_dict(data)

        assert restored.id == "emp001"
        assert restored.name == "张三"
        assert len(restored.available_slots) == 1
        assert restored.skills == {"python", "testing"}


class TestShift:
    def test_overlaps_with_same_day_overlapping(self):
        shift1 = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        shift2 = Shift(
            id="s2",
            date=date(2026, 5, 4),
            start_time=time(10, 0),
            end_time=time(18, 0)
        )
        assert shift1.overlaps_with(shift2) is True

    def test_overlaps_with_same_day_non_overlapping(self):
        shift1 = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(12, 0)
        )
        shift2 = Shift(
            id="s2",
            date=date(2026, 5, 4),
            start_time=time(13, 0),
            end_time=time(17, 0)
        )
        assert shift1.overlaps_with(shift2) is False

    def test_overlaps_with_different_day(self):
        shift1 = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        shift2 = Shift(
            id="s2",
            date=date(2026, 5, 5),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )
        assert shift1.overlaps_with(shift2) is False

    def test_duration(self):
        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 30)
        )

        duration = shift.duration()
        assert duration == timedelta(hours=8, minutes=30)

    def test_to_dict_and_from_dict(self):
        shift = Shift(
            id="shift001",
            date=date(2026, 5, 10),
            start_time=time(8, 0),
            end_time=time(16, 0),
            required_employees=2,
            required_skills={"nurse", "first-aid"}
        )

        data = shift.to_dict()
        restored = Shift.from_dict(data)

        assert restored.id == "shift001"
        assert restored.date == date(2026, 5, 10)
        assert restored.start_time == time(8, 0)
        assert restored.end_time == time(16, 0)
        assert restored.required_employees == 2
        assert restored.required_skills == {"nurse", "first-aid"}


class TestSchedule:
    def test_get_assignments_for_employee(self):
        assignment1 = Assignment(employee_id="e1", shift_id="s1")
        assignment2 = Assignment(employee_id="e1", shift_id="s2")
        assignment3 = Assignment(employee_id="e2", shift_id="s1")

        schedule = Schedule(assignments=[assignment1, assignment2, assignment3])

        e1_assignments = schedule.get_assignments_for_employee("e1")
        assert len(e1_assignments) == 2
        assert {a.shift_id for a in e1_assignments} == {"s1", "s2"}

    def test_get_assignments_for_shift(self):
        assignment1 = Assignment(employee_id="e1", shift_id="s1")
        assignment2 = Assignment(employee_id="e2", shift_id="s1")
        assignment3 = Assignment(employee_id="e1", shift_id="s2")

        schedule = Schedule(assignments=[assignment1, assignment2, assignment3])

        s1_assignments = schedule.get_assignments_for_shift("s1")
        assert len(s1_assignments) == 2
        assert {a.employee_id for a in s1_assignments} == {"e1", "e2"}

    def test_has_conflicts_true(self):
        conflict = Conflict(
            conflict_type=ConflictType.UNDERSTAFFED,
            shift_id="s1",
            message="Test conflict"
        )
        schedule = Schedule(conflicts=[conflict])
        assert schedule.has_conflicts() is True

    def test_has_conflicts_false(self):
        schedule = Schedule()
        assert schedule.has_conflicts() is False
