import pytest
from datetime import date, time

from shift_scheduler.models import (
    Employee,
    Shift,
    TimeSlot,
    DayOfWeek,
    ConflictType
)
from shift_scheduler.scheduler import ShiftScheduler


class TestShiftScheduler:
    def test_basic_scheduling(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="张三", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        scheduler = ShiftScheduler([employee], [shift])
        schedule = scheduler.schedule()

        assert len(schedule.assignments) == 1
        assert schedule.assignments[0].employee_id == "e1"
        assert schedule.assignments[0].shift_id == "s1"
        assert not schedule.has_conflicts()

    def test_scheduling_with_multiple_employees(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee1 = Employee(id="e1", name="张三", available_slots=[slot])
        employee2 = Employee(id="e2", name="李四", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0),
            required_employees=2
        )

        scheduler = ShiftScheduler([employee1, employee2], [shift])
        schedule = scheduler.schedule()

        assert len(schedule.assignments) == 2
        assigned_employees = {a.employee_id for a in schedule.assignments}
        assert assigned_employees == {"e1", "e2"}
        assert not schedule.has_conflicts()

    def test_scheduling_insufficient_employees(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="张三", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0),
            required_employees=3
        )

        scheduler = ShiftScheduler([employee], [shift])
        schedule = scheduler.schedule()

        assert len(schedule.assignments) == 1
        assert schedule.has_conflicts()
        understaffed_conflicts = [
            c for c in schedule.conflicts
            if c.conflict_type == ConflictType.UNDERSTAFFED
        ]
        assert len(understaffed_conflicts) == 1

    def test_scheduling_unavailable_employee(self):
        slot = TimeSlot(DayOfWeek.TUESDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="张三", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        scheduler = ShiftScheduler([employee], [shift])
        schedule = scheduler.schedule()

        assert len(schedule.assignments) == 0
        assert schedule.has_conflicts()

    def test_skill_matching(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        employee1 = Employee(
            id="e1",
            name="张三",
            available_slots=[slot],
            skills={"python"}
        )
        employee2 = Employee(
            id="e2",
            name="李四",
            available_slots=[slot],
            skills={"java"}
        )

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0),
            required_skills={"python"}
        )

        scheduler = ShiftScheduler([employee1, employee2], [shift])
        schedule = scheduler.schedule()

        assert len(schedule.assignments) == 1
        assert schedule.assignments[0].employee_id == "e1"

    def test_overlapping_shifts_avoidance(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(18, 0))
        employee = Employee(id="e1", name="张三", available_slots=[slot])

        shift1 = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(13, 0)
        )
        shift2 = Shift(
            id="s2",
            date=date(2026, 5, 4),
            start_time=time(12, 0),
            end_time=time(17, 0)
        )

        scheduler = ShiftScheduler([employee], [shift1, shift2])
        schedule = scheduler.schedule()

        assert len(schedule.assignments) == 1

    def test_non_overlapping_shifts_same_employee(self):
        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(18, 0))
        employee = Employee(id="e1", name="张三", available_slots=[slot])

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

        scheduler = ShiftScheduler([employee], [shift1, shift2])
        schedule = scheduler.schedule()

        assert len(schedule.assignments) == 2

    def test_check_conflicts_unavailable(self):
        from shift_scheduler.models import Assignment, Conflict, ConflictType

        slot = TimeSlot(DayOfWeek.TUESDAY, time(9, 0), time(17, 0))
        employee = Employee(id="e1", name="张三", available_slots=[slot])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        from shift_scheduler.models import Schedule
        schedule = Schedule(assignments=[Assignment("e1", "s1")])

        scheduler = ShiftScheduler([employee], [shift])
        conflicts = scheduler.check_conflicts(schedule)

        unavailable_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.UNAVAILABLE
        ]
        assert len(unavailable_conflicts) == 1

    def test_check_conflicts_overlapping(self):
        from shift_scheduler.models import Assignment, Conflict, ConflictType

        slot = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(18, 0))
        employee = Employee(id="e1", name="张三", available_slots=[slot])

        shift1 = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(13, 0)
        )
        shift2 = Shift(
            id="s2",
            date=date(2026, 5, 4),
            start_time=time(12, 0),
            end_time=time(17, 0)
        )

        from shift_scheduler.models import Schedule
        schedule = Schedule(
            assignments=[Assignment("e1", "s1"), Assignment("e1", "s2")]
        )

        scheduler = ShiftScheduler([employee], [shift1, shift2])
        conflicts = scheduler.check_conflicts(schedule)

        overlapping_conflicts = [
            c for c in conflicts if c.conflict_type == ConflictType.OVERLAPPING
        ]
        assert len(overlapping_conflicts) == 1

    def test_get_available_employees_for_shift(self):
        slot1 = TimeSlot(DayOfWeek.MONDAY, time(9, 0), time(17, 0))
        slot2 = TimeSlot(DayOfWeek.TUESDAY, time(9, 0), time(17, 0))

        employee1 = Employee(id="e1", name="张三", available_slots=[slot1])
        employee2 = Employee(id="e2", name="李四", available_slots=[slot2])

        shift = Shift(
            id="s1",
            date=date(2026, 5, 4),
            start_time=time(9, 0),
            end_time=time(17, 0)
        )

        scheduler = ShiftScheduler([employee1, employee2], [shift])
        available = scheduler.get_available_employees_for_shift("s1")

        assert len(available) == 1
        assert available[0].id == "e1"
