import click
from datetime import date, time, datetime
from pathlib import Path
from typing import List, Optional

from . import __version__
from .models import (
    Employee,
    Shift,
    TimeSlot,
    DayOfWeek,
    Schedule
)
from .scheduler import ShiftScheduler
from .storage import Storage
from .exporters import MarkdownExporter, CSVExporter


DATA_DIR = Path.home() / ".shift-scheduler" / "data"


def get_storage() -> Storage:
    return Storage(DATA_DIR)


@click.group()
@click.version_option(__version__)
def main():
    """轮班排班 CLI 工具 - 管理员工排班、匹配可用时间与班次需求"""
    pass


@main.group()
def employee():
    """员工管理命令"""
    pass


@employee.command("add")
@click.option("--id", required=True, help="员工唯一标识")
@click.option("--name", required=True, help="员工姓名")
@click.option("--available", multiple=True,
              help="可用时间段，格式: 星期几,开始时间,结束时间 (如: MONDAY,09:00,18:00)")
@click.option("--skill", multiple=True, help="员工技能")
def add_employee(id: str, name: str, available: tuple, skill: tuple):
    """添加新员工"""
    storage = get_storage()
    employees = storage.load_employees()

    if any(e.id == id for e in employees):
        click.echo(f"错误: 员工 ID '{id}' 已存在")
        return

    available_slots: List[TimeSlot] = []
    for slot_str in available:
        parts = slot_str.split(',')
        if len(parts) != 3:
            click.echo(f"错误: 时间段格式错误: {slot_str}")
            return

        try:
            day = DayOfWeek[parts[0].strip().upper()]
            start = datetime.strptime(parts[1].strip(), '%H:%M').time()
            end = datetime.strptime(parts[2].strip(), '%H:%M').time()
            available_slots.append(TimeSlot(day, start, end))
        except (KeyError, ValueError) as e:
            click.echo(f"错误: 时间段解析失败: {slot_str}. {e}")
            return

    employee = Employee(
        id=id,
        name=name,
        available_slots=available_slots,
        skills=set(skill)
    )

    employees.append(employee)
    storage.save_employees(employees)

    click.echo(f"已添加员工: {employee.name} (ID: {employee.id})")
    if available_slots:
        click.echo(f"  可用时间段: {len(available_slots)} 个")
    if skill:
        click.echo(f"  技能: {', '.join(skill)}")


@employee.command("list")
def list_employees():
    """列出所有员工"""
    storage = get_storage()
    employees = storage.load_employees()

    if not employees:
        click.echo("暂无员工")
        return

    for e in employees:
        click.echo(f"ID: {e.id}")
        click.echo(f"  姓名: {e.name}")
        if e.skills:
            click.echo(f"  技能: {', '.join(e.skills)}")
        if e.available_slots:
            click.echo(f"  可用时间段:")
            for slot in e.available_slots:
                day_name = slot.day_of_week.name.title()
                click.echo(f"    - {day_name}: {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}")
        click.echo()


@employee.command("remove")
@click.argument("employee_id")
def remove_employee(employee_id: str):
    """删除员工"""
    storage = get_storage()
    employees = storage.load_employees()

    employees = [e for e in employees if e.id != employee_id]
    storage.save_employees(employees)

    click.echo(f"已删除员工 ID: {employee_id}")


@main.group()
def shift():
    """班次管理命令"""
    pass


@shift.command("add")
@click.option("--id", required=True, help="班次唯一标识")
@click.option("--date", required=True, help="日期 (格式: YYYY-MM-DD)")
@click.option("--start", required=True, help="开始时间 (格式: HH:MM)")
@click.option("--end", required=True, help="结束时间 (格式: HH:MM)")
@click.option("--required", type=int, default=1, help="需要的员工数量")
@click.option("--skill", multiple=True, help="所需技能")
def add_shift(id: str, date: str, start: str, end: str, required: int, skill: tuple):
    """添加新班次"""
    storage = get_storage()
    shifts = storage.load_shifts()

    if any(s.id == id for s in shifts):
        click.echo(f"错误: 班次 ID '{id}' 已存在")
        return

    try:
        shift_date = datetime.strptime(date, '%Y-%m-%d').date()
        start_time = datetime.strptime(start, '%H:%M').time()
        end_time = datetime.strptime(end, '%H:%M').time()
    except ValueError as e:
        click.echo(f"错误: 日期或时间格式错误. {e}")
        return

    shift = Shift(
        id=id,
        date=shift_date,
        start_time=start_time,
        end_time=end_time,
        required_employees=required,
        required_skills=set(skill)
    )

    shifts.append(shift)
    storage.save_shifts(shifts)

    click.echo(f"已添加班次: {shift.id}")
    click.echo(f"  日期: {shift.date.isoformat()}")
    click.echo(f"  时间: {start} - {end}")
    click.echo(f"  需要员工: {required} 人")
    if skill:
        click.echo(f"  所需技能: {', '.join(skill)}")


@shift.command("list")
@click.option("--from", "from_date", help="起始日期 (格式: YYYY-MM-DD)")
@click.option("--to", "to_date", help="结束日期 (格式: YYYY-MM-DD)")
def list_shifts(from_date: Optional[str], to_date: Optional[str]):
    """列出所有班次"""
    storage = get_storage()
    shifts = storage.load_shifts()

    if not shifts:
        click.echo("暂无班次")
        return

    try:
        start_filter = datetime.strptime(from_date, '%Y-%m-%d').date() if from_date else None
        end_filter = datetime.strptime(to_date, '%Y-%m-%d').date() if to_date else None
    except ValueError as e:
        click.echo(f"错误: 日期格式错误. {e}")
        return

    sorted_shifts = sorted(shifts, key=lambda s: (s.date, s.start_time))

    for s in sorted_shifts:
        if start_filter and s.date < start_filter:
            continue
        if end_filter and s.date > end_filter:
            continue

        click.echo(f"ID: {s.id}")
        click.echo(f"  日期: {s.date.isoformat()}")
        click.echo(f"  时间: {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}")
        click.echo(f"  需要员工: {s.required_employees} 人")
        if s.required_skills:
            click.echo(f"  所需技能: {', '.join(s.required_skills)}")
        click.echo()


@shift.command("remove")
@click.argument("shift_id")
def remove_shift(shift_id: str):
    """删除班次"""
    storage = get_storage()
    shifts = storage.load_shifts()

    shifts = [s for s in shifts if s.id != shift_id]
    storage.save_shifts(shifts)

    click.echo(f"已删除班次 ID: {shift_id}")


@main.command()
@click.option("--output", "-o", help="排班结果输出文件 (JSON)")
def schedule(output: Optional[str]):
    """执行排班 - 匹配员工可用时间与班次需求"""
    storage = get_storage()
    employees = storage.load_employees()
    shifts = storage.load_shifts()

    if not employees:
        click.echo("错误: 没有员工数据")
        return

    if not shifts:
        click.echo("错误: 没有班次数据")
        return

    click.echo("开始排班...")
    click.echo(f"  员工数量: {len(employees)}")
    click.echo(f"  班次数量: {len(shifts)}")
    click.echo()

    scheduler = ShiftScheduler(employees, shifts)
    result = scheduler.schedule()

    click.echo("排班结果:")
    click.echo(f"  总分配次数: {len(result.assignments)}")

    if result.has_conflicts():
        click.echo(f"  冲突数量: {len(result.conflicts)}")
        click.echo()
        click.echo("冲突详情:")
        for conflict in result.conflicts:
            click.echo(f"  - [{conflict.conflict_type.value}] {conflict.message}")
    else:
        click.echo("  无冲突")

    storage.save_schedule(result)

    if output:
        output_path = Path(output)
        with open(output_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        click.echo(f"\n排班结果已保存到: {output_path}")


@main.command()
@click.option("--format", "-f", type=click.Choice(['markdown', 'csv', 'all']),
              default='all', help="导出格式")
@click.option("--output-dir", "-o", default=".", help="输出目录")
def export(format: str, output_dir: str):
    """导出排班结果 (Markdown 和 CSV)"""
    storage = get_storage()
    employees = storage.load_employees()
    shifts = storage.load_shifts()
    schedule = storage.load_schedule()

    if not schedule:
        click.echo("错误: 没有排班数据，请先运行 'schedule' 命令")
        return

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if format in ['markdown', 'all']:
        md_exporter = MarkdownExporter(employees, shifts, schedule)
        md_file = output_path / "schedule.md"
        md_exporter.save(md_file)
        click.echo(f"已导出 Markdown: {md_file}")

    if format in ['csv', 'all']:
        csv_exporter = CSVExporter(employees, shifts, schedule)

        assignments_file = output_path / "assignments.csv"
        csv_exporter.save_assignments(assignments_file)
        click.echo(f"已导出 CSV (分配表): {assignments_file}")

        shifts_file = output_path / "shifts.csv"
        csv_exporter.save_shifts(shifts_file)
        click.echo(f"已导出 CSV (班次表): {shifts_file}")

        employees_file = output_path / "employees.csv"
        csv_exporter.save_employees(employees_file)
        click.echo(f"已导出 CSV (员工表): {employees_file}")

        if schedule.has_conflicts():
            conflicts_file = output_path / "conflicts.csv"
            csv_exporter.save_conflicts(conflicts_file)
            click.echo(f"已导出 CSV (冲突表): {conflicts_file}")


@main.command()
@click.option("--employee", "-e", help="指定员工 ID 查看")
@click.option("--shift", "-s", help="指定班次 ID 查看")
def status(employee: Optional[str], shift: Optional[str]):
    """查看排班状态"""
    storage = get_storage()
    employees = storage.load_employees()
    shifts = storage.load_shifts()
    schedule = storage.load_schedule()

    employee_dict = {e.id: e for e in employees}
    shift_dict = {s.id: s for s in shifts}

    if not schedule:
        click.echo("暂无排班数据")
        return

    click.echo("排班状态:")
    click.echo(f"  总分配次数: {len(schedule.assignments)}")
    click.echo(f"  冲突数量: {len(schedule.conflicts)}")
    click.echo()

    if employee:
        emp = employee_dict.get(employee)
        if not emp:
            click.echo(f"错误: 未找到员工 ID: {employee}")
            return

        assignments = schedule.get_assignments_for_employee(employee)
        click.echo(f"员工: {emp.name} (ID: {employee})")
        click.echo(f"  分配班次: {len(assignments)} 个")

        for a in assignments:
            s = shift_dict.get(a.shift_id)
            if s:
                click.echo(f"    - {s.date.isoformat()} {s.start_time.strftime('%H:%M')}-{s.end_time.strftime('%H:%M')} (ID: {s.id})")

    elif shift:
        s = shift_dict.get(shift)
        if not s:
            click.echo(f"错误: 未找到班次 ID: {shift}")
            return

        assignments = schedule.get_assignments_for_shift(shift)
        click.echo(f"班次: {s.id}")
        click.echo(f"  日期: {s.date.isoformat()}")
        click.echo(f"  时间: {s.start_time.strftime('%H:%M')} - {s.end_time.strftime('%H:%M')}")
        click.echo(f"  需要员工: {s.required_employees} 人")
        click.echo(f"  已分配: {len(assignments)} 人")

        if assignments:
            click.echo(f"  分配的员工:")
            for a in assignments:
                emp = employee_dict.get(a.employee_id)
                if emp:
                    click.echo(f"    - {emp.name} (ID: {emp.id})")

    else:
        click.echo("按班次查看分配:")
        sorted_shifts = sorted(shifts, key=lambda s: (s.date, s.start_time))
        for s in sorted_shifts:
            assignments = schedule.get_assignments_for_shift(s.id)
            assigned_names = [employee_dict[a.employee_id].name for a in assignments if a.employee_id in employee_dict]
            status_mark = "✓" if len(assignments) >= s.required_employees else "!"
            click.echo(f"  {status_mark} {s.id} ({s.date.isoformat()}): {len(assignments)}/{s.required_employees} 人 - {', '.join(assigned_names) or '无人'}")


@main.command()
def clear():
    """清除所有数据"""
    storage = get_storage()
    storage.clear_all()
    click.echo("已清除所有数据")


if __name__ == "__main__":
    main()
