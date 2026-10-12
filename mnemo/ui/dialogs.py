"""Modal dialogs for Mnemo: Confirmations, Parameter Filling, and Command Runner."""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable

import customtkinter as ctk

from mnemo.runner import CommandRunner, ExecutionResult
from mnemo.template import extract_parameters, substitute_parameters
from mnemo.ui.theme import COLORS, FONTS


class ConfirmDialog(ctk.CTkToplevel):
    """Clean confirmation dialog with keyboard navigation (Enter / Y to confirm, Esc / N to cancel)."""

    def __init__(
        self,
        parent: ctk.CTk,
        title: str,
        message: str,
        confirm_text: str = "Yes",
        cancel_text: str = "No",
        is_destructive: bool = False,
        on_confirm: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("420x210")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_confirm = on_confirm

        # Center on parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 210
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 105
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

        # Content frame
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=24, pady=20)

        lbl_title = ctk.CTkLabel(
            frame,
            text=title,
            font=FONTS["section_title"],
            anchor="w",
        )
        lbl_title.pack(fill="x", pady=(0, 8))

        lbl_msg = ctk.CTkLabel(
            frame,
            text=message,
            font=FONTS["body"],
            text_color=COLORS["text_muted"],
            wraplength=370,
            justify="left",
            anchor="w",
        )
        lbl_msg.pack(fill="x", pady=(0, 20))

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        self.btn_cancel = ctk.CTkButton(
            btn_row,
            text=f"{cancel_text} (Esc)",
            font=FONTS["body"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            width=100,
            command=self.destroy,
        )
        self.btn_cancel.pack(side="right", padx=(8, 0))

        self.btn_ok = ctk.CTkButton(
            btn_row,
            text=f"{confirm_text} (Enter)",
            font=FONTS["body_bold"],
            fg_color=COLORS["danger"] if is_destructive else COLORS["primary"],
            hover_color=COLORS["danger_hover"]
            if is_destructive
            else COLORS["primary_hover"],
            width=115,
            command=self._confirm_and_close,
        )
        self.btn_ok.pack(side="right")

        # Keyboard bindings: Enter, KP_Enter, y, Y confirm
        self.bind("<Return>", lambda e: self._confirm_and_close())
        self.bind("<KP_Enter>", lambda e: self._confirm_and_close())
        self.bind("<Key-y>", lambda e: self._confirm_and_close())
        self.bind("<Key-Y>", lambda e: self._confirm_and_close())

        # Keyboard bindings: Escape, n, N cancel
        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Key-n>", lambda e: self.destroy())
        self.bind("<Key-N>", lambda e: self.destroy())

        # Also bind on the buttons directly
        self.btn_ok.bind("<Return>", lambda e: self._confirm_and_close())
        self.btn_ok.bind("<KP_Enter>", lambda e: self._confirm_and_close())
        self.btn_ok.bind("<space>", lambda e: self._confirm_and_close())
        self.btn_cancel.bind("<Return>", lambda e: self.destroy())

        # Ensure modal has focus and focus is set on Yes/Confirm button
        self.focus_force()
        self.btn_ok.focus_set()
        self.after(50, self.btn_ok.focus_set)

    def _confirm_and_close(self) -> None:
        if self.on_confirm:
            self.on_confirm()
        self.destroy()


class ParameterFillDialog(ctk.CTkToplevel):
    """Dialog allowing users to supply values for {param} variables in commands."""

    def __init__(
        self,
        parent: ctk.CTk,
        template_content: str,
        on_run_command: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("Fill Command Parameters")
        self.geometry("640x520")
        self.minsize(550, 420)
        self.transient(parent)
        self.grab_set()

        self.template_content = template_content
        self.on_run_command = on_run_command
        self.params = extract_parameters(template_content)
        self.entries: dict[str, ctk.CTkEntry] = {}

        # Center on parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 320
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 260
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

        self._build_ui()
        self._update_preview()

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        # Header
        header = ctk.CTkLabel(
            container,
            text="⚡ Substitute Parameters",
            font=FONTS["section_title"],
            anchor="w",
        )
        header.pack(fill="x", pady=(0, 4))

        sub = ctk.CTkLabel(
            container,
            text=f"Detected {len(self.params)} parameter(s). Enter values below to render the command.",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        sub.pack(fill="x", pady=(0, 12))

        # Parameters inputs scrollable
        params_scroll = ctk.CTkScrollableFrame(container, height=150)
        params_scroll.pack(fill="both", expand=True, pady=(0, 12))

        for param in self.params:
            row = ctk.CTkFrame(params_scroll, fg_color="transparent")
            row.pack(fill="x", pady=4)

            lbl = ctk.CTkLabel(
                row,
                text=f"{{{param}}}:",
                font=FONTS["code_small"],
                width=140,
                anchor="w",
            )
            lbl.pack(side="left")

            entry = ctk.CTkEntry(
                row,
                placeholder_text=f"Value for {param}...",
                font=FONTS["code"],
                height=32,
            )
            entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
            entry.bind("<KeyRelease>", lambda e: self._update_preview())
            self.entries[param] = entry

        # Preview Section
        lbl_preview = ctk.CTkLabel(
            container,
            text="Rendered Preview:",
            font=FONTS["body_bold"],
            anchor="w",
        )
        lbl_preview.pack(fill="x", pady=(4, 4))

        self.preview_box = ctk.CTkTextbox(
            container,
            font=FONTS["code"],
            height=120,
            wrap="word",
        )
        self.preview_box.pack(fill="both", expand=True, pady=(0, 16))

        # Action Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", side="bottom")

        self.btn_copy = ctk.CTkButton(
            btn_row,
            text="📋 Copy Rendered",
            font=FONTS["body_bold"],
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary_hover"],
            command=self._copy_rendered,
        )
        self.btn_copy.pack(side="left", padx=(0, 8))

        if self.on_run_command:
            btn_run = ctk.CTkButton(
                btn_row,
                text="▶ Run in Terminal",
                font=FONTS["body_bold"],
                fg_color=COLORS["success"],
                hover_color=COLORS["success_hover"],
                command=self._run_rendered,
            )
            btn_run.pack(side="left", padx=(0, 8))

        btn_close = ctk.CTkButton(
            btn_row,
            text="Close",
            font=FONTS["body"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            width=80,
            command=self.destroy,
        )
        btn_close.pack(side="right")

    def _get_current_rendered(self) -> str:
        vals = {p: entry.get().strip() for p, entry in self.entries.items()}
        return substitute_parameters(self.template_content, vals)

    def _update_preview(self) -> None:
        rendered = self._get_current_rendered()
        self.preview_box.delete("1.0", "end")
        self.preview_box.insert("1.0", rendered)

    def _copy_rendered(self) -> None:
        rendered = self._get_current_rendered()
        self.clipboard_clear()
        self.clipboard_append(rendered)
        self.btn_copy.configure(text="✓ Copied!", fg_color=COLORS["success"])
        self.after(
            1500,
            lambda: self.btn_copy.configure(
                text="📋 Copy Rendered", fg_color=COLORS["primary"]
            ),
        )

    def _run_rendered(self) -> None:
        rendered = self._get_current_rendered()
        self.destroy()
        if self.on_run_command:
            self.on_run_command(rendered)


class CommandRunnerDialog(ctk.CTkToplevel):
    """Interactive command execution modal with real-time output stream."""

    def __init__(
        self,
        parent: ctk.CTk,
        command: str,
        initial_shell: str = "powershell",
    ) -> None:
        super().__init__(parent)
        self.title("Run Command - Mnemo")
        self.geometry("700x520")
        self.minsize(580, 420)
        self.transient(parent)
        self.grab_set()

        self.command = command.strip()
        self.runner = CommandRunner()
        self.is_running = False

        # Center on parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() // 2) - 350
        py = parent.winfo_y() + (parent.winfo_height() // 2) - 260
        self.geometry(f"+{max(0, px)}+{max(0, py)}")

        self._build_ui(initial_shell)

    def _build_ui(self, initial_shell: str) -> None:
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        # Header row
        hdr_frame = ctk.CTkFrame(container, fg_color="transparent")
        hdr_frame.pack(fill="x", pady=(0, 8))

        lbl_title = ctk.CTkLabel(
            hdr_frame,
            text="▶ Terminal Command Runner",
            font=FONTS["section_title"],
            anchor="w",
        )
        lbl_title.pack(side="left")

        # Shell selector
        lbl_shell = ctk.CTkLabel(hdr_frame, text="Shell:", font=FONTS["small"])
        lbl_shell.pack(side="left", padx=(20, 6))

        shells = ["powershell", "cmd"] if sys.platform == "win32" else ["bash", "sh"]
        self.shell_var = ctk.StringVar(
            value=initial_shell if initial_shell in shells else shells[0]
        )
        self.shell_menu = ctk.CTkOptionMenu(
            hdr_frame,
            values=shells,
            variable=self.shell_var,
            width=110,
            height=28,
            font=FONTS["small"],
        )
        self.shell_menu.pack(side="left")

        # Command input / view
        lbl_cmd = ctk.CTkLabel(
            container,
            text="Command:",
            font=FONTS["body_bold"],
            anchor="w",
        )
        lbl_cmd.pack(fill="x", pady=(4, 2))

        self.cmd_box = ctk.CTkTextbox(
            container,
            font=FONTS["code"],
            height=60,
            wrap="word",
        )
        self.cmd_box.insert("1.0", self.command)
        self.cmd_box.pack(fill="x", pady=(0, 10))

        # Status & controls row
        ctrl_frame = ctk.CTkFrame(container, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=(0, 6))

        self.btn_execute = ctk.CTkButton(
            ctrl_frame,
            text="▶ Execute",
            font=FONTS["body_bold"],
            fg_color=COLORS["success"],
            hover_color=COLORS["success_hover"],
            width=110,
            command=self._start_execution,
        )
        self.btn_execute.pack(side="left", padx=(0, 8))

        self.btn_stop = ctk.CTkButton(
            ctrl_frame,
            text="⏹ Stop",
            font=FONTS["body_bold"],
            fg_color=COLORS["danger"],
            hover_color=COLORS["danger_hover"],
            width=90,
            state="disabled",
            command=self._stop_execution,
        )
        self.btn_stop.pack(side="left", padx=(0, 12))

        self.lbl_status = ctk.CTkLabel(
            ctrl_frame,
            text="Ready to execute",
            font=FONTS["small"],
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        self.lbl_status.pack(side="left", fill="x", expand=True)

        self.btn_copy_output = ctk.CTkButton(
            ctrl_frame,
            text="Copy Output",
            font=FONTS["small"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            width=90,
            command=self._copy_output,
        )
        self.btn_copy_output.pack(side="right")

        # Terminal output display
        self.term_box = ctk.CTkTextbox(
            container,
            font=FONTS["code"],
            fg_color=COLORS["terminal_bg"][1],
            text_color=COLORS["terminal_fg"][1],
            wrap="char",
        )
        self.term_box.pack(fill="both", expand=True, pady=(4, 12))

        # Close button
        btn_close = ctk.CTkButton(
            container,
            text="Close",
            font=FONTS["body"],
            fg_color=COLORS["secondary"],
            text_color=COLORS["text"],
            hover_color=COLORS["secondary_hover"],
            width=80,
            command=self._on_close,
        )
        btn_close.pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _append_output(self, text: str) -> None:
        self.term_box.insert("end", text)
        self.term_box.see("end")

    def _start_execution(self) -> None:
        if self.is_running:
            return

        cmd = self.cmd_box.get("1.0", "end").strip()
        if not cmd:
            self.lbl_status.configure(
                text="No command to execute", text_color=COLORS["warning"][1]
            )
            return

        self.is_running = True
        self.btn_execute.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.shell_menu.configure(state="disabled")
        self.lbl_status.configure(text="Running...", text_color=COLORS["primary"][1])
        self.term_box.delete("1.0", "end")

        shell = self.shell_var.get()

        def worker():
            res = self.runner.run(
                command=cmd,
                shell_type=shell,
                on_output=lambda line: self.after(0, self._append_output, line),
            )
            self.after(0, self._on_execution_completed, res)

        threading.Thread(target=worker, daemon=True).start()

    def _stop_execution(self) -> None:
        self.runner.cancel()
        self.lbl_status.configure(text="Terminating...", text_color=COLORS["danger"][1])

    def _on_execution_completed(self, res: ExecutionResult) -> None:
        self.is_running = False
        self.btn_execute.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.shell_menu.configure(state="normal")

        if res.cancelled:
            status_txt = (
                f"Cancelled (Code: {res.returncode}, {res.duration_seconds:.2f}s)"
            )
            color = COLORS["danger"][1]
        elif res.timed_out:
            status_txt = f"Timed out after {res.duration_seconds:.2f}s"
            color = COLORS["danger"][1]
        elif res.returncode == 0:
            status_txt = f"Success (Exit code: 0, took {res.duration_seconds:.2f}s)"
            color = COLORS["success"][1]
        else:
            status_txt = f"Failed (Exit code: {res.returncode}, took {res.duration_seconds:.2f}s)"
            color = COLORS["warning"][1]

        self.lbl_status.configure(text=status_txt, text_color=color)

    def _copy_output(self) -> None:
        txt = self.term_box.get("1.0", "end").strip()
        if txt:
            self.clipboard_clear()
            self.clipboard_append(txt)
            self.btn_copy_output.configure(text="✓ Copied")
            self.after(1500, lambda: self.btn_copy_output.configure(text="Copy Output"))

    def _on_close(self) -> None:
        if self.is_running:
            self.runner.cancel()
        self.destroy()
