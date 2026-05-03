from dataclasses import dataclass, field
from datetime import date, time, datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Set


class DayOfWeek(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class TimeSlot:
    day_of_week: DayOfWeek
    start_time: time
    end_time: time

    def overlaps_with(self, other: 'TimeSlot') -> bool:
        if self.day_of_week != other.day_of_week:
            return False
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)

    def to_dict(self) -> Dict:
        return {
            'day_of_week': self.day_of_week.value,
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M')
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TimeSlot':
        return cls(
            day_of_week=DayOfWeek(data['day_of_week']),
            start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(data['end_time'], '%H:%M').time()
        )


@dataclass
class Employee:
    id: str
    name: str
    available_slots: List[TimeSlot] = field(default_factory=list)
    skills: Set[str] = field(default_factory=set)

    def is_available(self, shift: 'Shift') -> bool:
        for slot in self.available_slots:
            if self._shift_overlaps_with_slot(shift, slot):
                return True
        return False

    def _shift_overlaps_with_slot(self, shift: 'Shift', slot: TimeSlot) -> bool:
        shift_day = DayOfWeek(shift.date.weekday())
        if shift_day != slot.day_of_week:
            return False
        return not (shift.end_time <= slot.start_time or slot.end_time <= shift.start_time)

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'available_slots': [slot.to_dict() for slot in self.available_slots],
            'skills': list(self.skills)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Employee':
        return cls(
            id=data['id'],
            name=data['name'],
            available_slots=[TimeSlot.from_dict(slot) for slot in data.get('available_slots', [])],
            skills=set(data.get('skills', []))
        )


@dataclass
class Shift:
    id: str
    date: date
    start_time: time
    end_time: time
    required_employees: int = 1
    required_skills: Set[str] = field(default_factory=set)

    def overlaps_with(self, other: 'Shift') -> bool:
        if self.date != other.date:
            return False
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)

    def duration(self) -> timedelta:
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        return end - start

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'start_time': self.start_time.strftime('%H:%M'),
            'end_time': self.end_time.strftime('%H:%M'),
            'required_employees': self.required_employees,
            'required_skills': list(self.required_skills)
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Shift':
        return cls(
            id=data['id'],
            date=date.fromisoformat(data['date']),
            start_time=datetime.strptime(data['start_time'], '%H:%M').time(),
            end_time=datetime.strptime(data['end_time'], '%H:%M').time(),
            required_employees=data.get('required_employees', 1),
            required_skills=set(data.get('required_skills', []))
        )


@dataclass
class Assignment:
    employee_id: str
    shift_id: str

    def to_dict(self) -> Dict:
        return {
            'employee_id': self.employee_id,
            'shift_id': self.shift_id
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Assignment':
        return cls(
            employee_id=data['employee_id'],
            shift_id=data['shift_id']
        )


class ConflictType(Enum):
    UNAVAILABLE = "unavailable"
    OVERLAPPING = "overlapping"
    INSUFFICIENT_SKILLS = "insufficient_skills"
    UNDERSTAFFED = "understaffed"


@dataclass
class Conflict:
    conflict_type: ConflictType
    employee_id: Optional[str] = None
    shift_id: Optional[str] = None
    message: str = ""

    def to_dict(self) -> Dict:
        return {
            'conflict_type': self.conflict_type.value,
            'employee_id': self.employee_id,
            'shift_id': self.shift_id,
            'message': self.message
        }


@dataclass
class Schedule:
    assignments: List[Assignment] = field(default_factory=list)
    conflicts: List[Conflict] = field(default_factory=list)

    def get_assignments_for_employee(self, employee_id: str) -> List[Assignment]:
        return [a for a in self.assignments if a.employee_id == employee_id]

    def get_assignments_for_shift(self, shift_id: str) -> List[Assignment]:
        return [a for a in self.assignments if a.shift_id == shift_id]

    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def to_dict(self) -> Dict:
        return {
            'assignments': [a.to_dict() for a in self.assignments],
            'conflicts': [c.to_dict() for c in self.conflicts]
        }
