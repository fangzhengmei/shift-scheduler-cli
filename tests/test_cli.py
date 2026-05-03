import pytest
import tempfile
import json
from datetime import date, time
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from shift_scheduler.cli import main, DATA_DIR
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


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def temp_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        original_dir = DATA_DIR
        try:
            from shift_scheduler import cli
            cli.DATA_DIR = data_dir
            yield data_dir
        finally:
            cli.DATA_DIR = original_dir


class TestEmployeeCommands:
    def test_add_employee_basic(self, runner, temp_data_dir):
        result = runner.invoke(
            main,
            ["employee", "add", "--id", "e1", "--name", "张三"]
        )

        assert result.exit_code == 0
        assert "已添加员工" in result.output
        assert "张三" in result.output

        employees_file = temp_data_dir / "employees.json"
        assert employees_file.exists()

        with open(employees_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]['id'] == "e1"
        assert data[0]['name'] == "张三"

    def test_add_employee_with_availability(self, runner, temp_data_dir):
        result = runner.invoke(
            main,
            [
                "employee", "add",
                "--id", "e1",
                "--name", "张三",
                "--available", "MONDAY,09:00,17:00",
                "--available", "WEDNESDAY,10:00,18:00"
            ]
        )

        assert result.exit_code == 0
        assert "可用时间段: 2 个" in result.output

    def test_add_employee_with_skills(self, runner, temp_data_dir):
        result = runner.invoke(
            main,
            [
                "employee", "add",
                "--id", "e1",
                "--name", "张三",
                "--skill", "python",
                "--skill", "testing"
            ]
        )

        assert result.exit_code == 0
        assert "技能: python, testing" in result.output

    def test_add_employee_duplicate_id(self, runner, temp_data_dir):
        runner.invoke(
            main,
            ["employee", "add", "--id", "e1", "--name", "张三"]
        )

        result = runner.invoke(
            main,
            ["employee", "add", "--id", "e1", "--name", "李四"]
        )

        assert result.exit_code == 0
        assert "已存在" in result.output

    def test_list_employees_empty(self, runner, temp_data_dir):
        result = runner.invoke(main, ["employee", "list"])
        assert result.exit_code == 0
        assert "暂无员工" in result.output

    def test_list_employees_with_data(self, runner, temp_data_dir):
        runner.invoke(
            main,
            ["employee", "add", "--id", "e1", "--name", "张三"]
        )

        result = runner.invoke(main, ["employee", "list"])
        assert result.exit_code == 0
        assert "ID: e1" in result.output
        assert "姓名: 张三" in result.output

    def test_remove_employee(self, runner, temp_data_dir):
        runner.invoke(
            main,
            ["employee", "add", "--id", "e1", "--name", "张三"]
        )

        result = runner.invoke(main, ["employee", "remove", "e1"])
        assert result.exit_code == 0
        assert "已删除员工 ID: e1" in result.output

        list_result = runner.invoke(main, ["employee", "list"])
        assert "暂无员工" in list_result.output


class TestShiftCommands:
    def test_add_shift_basic(self, runner, temp_data_dir):
        result = runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )

        assert result.exit_code == 0
        assert "已添加班次: s1" in result.output

        shifts_file = temp_data_dir / "shifts.json"
        assert shifts_file.exists()

        with open(shifts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]['id'] == "s1"
        assert data[0]['date'] == "2026-05-04"

    def test_add_shift_with_requirements(self, runner, temp_data_dir):
        result = runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00",
                "--required", "2",
                "--skill", "nurse",
                "--skill", "first-aid"
            ]
        )

        assert result.exit_code == 0
        assert "需要员工: 2 人" in result.output
        assert "所需技能: nurse, first-aid" in result.output

    def test_list_shifts_empty(self, runner, temp_data_dir):
        result = runner.invoke(main, ["shift", "list"])
        assert result.exit_code == 0
        assert "暂无班次" in result.output

    def test_list_shifts_with_data(self, runner, temp_data_dir):
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )

        result = runner.invoke(main, ["shift", "list"])
        assert result.exit_code == 0
        assert "ID: s1" in result.output
        assert "日期: 2026-05-04" in result.output

    def test_list_shifts_with_date_filter(self, runner, temp_data_dir):
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s2",
                "--date", "2026-05-10",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )

        result = runner.invoke(
            main,
            ["shift", "list", "--from", "2026-05-01", "--to", "2026-05-05"]
        )
        assert result.exit_code == 0
        assert "s1" in result.output
        assert "s2" not in result.output

    def test_remove_shift(self, runner, temp_data_dir):
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )

        result = runner.invoke(main, ["shift", "remove", "s1"])
        assert result.exit_code == 0
        assert "已删除班次 ID: s1" in result.output


class TestScheduleCommand:
    def test_schedule_no_employees(self, runner, temp_data_dir):
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )

        result = runner.invoke(main, ["schedule"])
        assert result.exit_code == 0
        assert "没有员工数据" in result.output

    def test_schedule_no_shifts(self, runner, temp_data_dir):
        runner.invoke(
            main,
            ["employee", "add", "--id", "e1", "--name", "张三"]
        )

        result = runner.invoke(main, ["schedule"])
        assert result.exit_code == 0
        assert "没有班次数据" in result.output

    def test_schedule_success(self, runner, temp_data_dir):
        runner.invoke(
            main,
            [
                "employee", "add",
                "--id", "e1",
                "--name", "张三",
                "--available", "MONDAY,09:00,17:00"
            ]
        )
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )

        result = runner.invoke(main, ["schedule"])
        assert result.exit_code == 0
        assert "总分配次数: 1" in result.output
        assert "无冲突" in result.output

    def test_schedule_with_conflicts(self, runner, temp_data_dir):
        runner.invoke(
            main,
            [
                "employee", "add",
                "--id", "e1",
                "--name", "张三",
                "--available", "TUESDAY,09:00,17:00"
            ]
        )
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )

        result = runner.invoke(main, ["schedule"])
        assert result.exit_code == 0
        assert "冲突数量:" in result.output


class TestExportCommand:
    def test_export_no_schedule(self, runner, temp_data_dir):
        result = runner.invoke(main, ["export"])
        assert result.exit_code == 0
        assert "没有排班数据" in result.output

    def test_export_success(self, runner, temp_data_dir):
        runner.invoke(
            main,
            [
                "employee", "add",
                "--id", "e1",
                "--name", "张三",
                "--available", "MONDAY,09:00,17:00"
            ]
        )
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )
        runner.invoke(main, ["schedule"])

        with tempfile.TemporaryDirectory() as export_dir:
            result = runner.invoke(
                main,
                ["export", "-o", export_dir]
            )

            assert result.exit_code == 0
            assert "已导出 Markdown" in result.output
            assert "已导出 CSV" in result.output

            md_file = Path(export_dir) / "schedule.md"
            assert md_file.exists()

            assignments_file = Path(export_dir) / "assignments.csv"
            assert assignments_file.exists()


class TestStatusCommand:
    def test_status_no_schedule(self, runner, temp_data_dir):
        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "暂无排班数据" in result.output

    def test_status_with_schedule(self, runner, temp_data_dir):
        runner.invoke(
            main,
            [
                "employee", "add",
                "--id", "e1",
                "--name", "张三",
                "--available", "MONDAY,09:00,17:00"
            ]
        )
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )
        runner.invoke(main, ["schedule"])

        result = runner.invoke(main, ["status"])
        assert result.exit_code == 0
        assert "总分配次数: 1" in result.output

    def test_status_by_employee(self, runner, temp_data_dir):
        runner.invoke(
            main,
            [
                "employee", "add",
                "--id", "e1",
                "--name", "张三",
                "--available", "MONDAY,09:00,17:00"
            ]
        )
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )
        runner.invoke(main, ["schedule"])

        result = runner.invoke(main, ["status", "-e", "e1"])
        assert result.exit_code == 0
        assert "张三" in result.output
        assert "分配班次: 1 个" in result.output

    def test_status_by_shift(self, runner, temp_data_dir):
        runner.invoke(
            main,
            [
                "employee", "add",
                "--id", "e1",
                "--name", "张三",
                "--available", "MONDAY,09:00,17:00"
            ]
        )
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )
        runner.invoke(main, ["schedule"])

        result = runner.invoke(main, ["status", "-s", "s1"])
        assert result.exit_code == 0
        assert "s1" in result.output
        assert "已分配: 1 人" in result.output


class TestClearCommand:
    def test_clear(self, runner, temp_data_dir):
        runner.invoke(
            main,
            ["employee", "add", "--id", "e1", "--name", "张三"]
        )
        runner.invoke(
            main,
            [
                "shift", "add",
                "--id", "s1",
                "--date", "2026-05-04",
                "--start", "09:00",
                "--end", "17:00"
            ]
        )

        result = runner.invoke(main, ["clear"])
        assert result.exit_code == 0
        assert "已清除所有数据" in result.output

        employees_result = runner.invoke(main, ["employee", "list"])
        assert "暂无员工" in employees_result.output

        shifts_result = runner.invoke(main, ["shift", "list"])
        assert "暂无班次" in shifts_result.output
