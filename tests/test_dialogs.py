"""Tests for modal dialogs."""

from pathlib import Path

import customtkinter as ctk

from mnemo.ui.dialogs import CommandRunnerDialog, ConfirmDialog, ParameterFillDialog


def test_confirm_dialog(tmp_path: Path):
    root = ctk.CTk()
    root.withdraw()

    confirmed = []

    def on_ok():
        confirmed.append(True)

    dlg = ConfirmDialog(
        root, title="Confirm Test", message="Are you sure?", on_confirm=on_ok
    )
    dlg.withdraw()
    dlg._confirm_and_close()

    assert confirmed == [True]
    root.destroy()


def test_confirm_dialog_keyboard_enter():
    root = ctk.CTk()
    root.withdraw()

    confirmed = []

    def on_ok():
        confirmed.append(True)

    dlg = ConfirmDialog(
        root, title="Test Enter", message="Confirm with Enter?", on_confirm=on_ok
    )
    dlg.update()
    dlg.btn_ok.focus_set()
    dlg.event_generate("<KeyPress-Return>")
    dlg.update()

    assert confirmed == [True]
    root.destroy()


def test_confirm_dialog_keyboard_y():
    root = ctk.CTk()
    root.withdraw()

    confirmed = []

    def on_ok():
        confirmed.append(True)

    dlg = ConfirmDialog(
        root, title="Test Y", message="Confirm with Y?", on_confirm=on_ok
    )
    dlg.update()
    dlg.btn_ok.focus_set()
    dlg.event_generate("<KeyPress-y>")
    dlg.update()

    assert confirmed == [True]
    root.destroy()


def test_parameter_fill_dialog():
    root = ctk.CTk()
    root.withdraw()

    command_template = "docker run -p {port}:80 {image}"
    dlg = ParameterFillDialog(root, template_content=command_template)
    dlg.withdraw()

    assert "port" in dlg.entries
    assert "image" in dlg.entries

    dlg.entries["port"].insert(0, "8080")
    dlg.entries["image"].insert(0, "nginx:latest")

    rendered = dlg._get_current_rendered()
    assert rendered == "docker run -p 8080:80 nginx:latest"

    dlg.destroy()
    root.destroy()


def test_command_runner_dialog():
    root = ctk.CTk()
    root.withdraw()

    dlg = CommandRunnerDialog(root, command="Write-Output 'Testing runner'")
    dlg.withdraw()
    assert dlg.command == "Write-Output 'Testing runner'"

    dlg.destroy()
    root.destroy()
