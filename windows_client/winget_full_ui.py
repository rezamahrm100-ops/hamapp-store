"""Advanced native WinGet command families inside the HamApp window.

This is not a second store, elevated shell, generic computer-control agent or
auto-installer. WinGet remains the sole upstream package management engine.
"""
import threading
from windows_client import winget_full_surface as engine


def open_full_surface(parent):
    import tkinter as tk
    from tkinter import ttk, messagebox

    window = tk.Toplevel(parent)
    window.title("هَماپ | تمام فرمان‌های رسمی WinGet")
    window.geometry("850x620")
    window.minsize(670, 480)
    window.configure(bg="#101827")
    window.transient(parent)

    text, muted, surface = "#f8fafc", "#b9c6d8", "#1e293b"
    top = tk.Frame(window, bg="#101827", padx=18, pady=15)
    top.pack(fill="both", expand=True)
    tk.Label(top, text="کنسول تخصصی موتور WinGet", fg=text, bg="#101827",
             font=("Segoe UI", 18, "bold"), anchor="e").pack(fill="x")
    tk.Label(top, text="دسترسی به خانواده‌های فرمان WinGet از داخل هَماپ؛" +
             " نصب، ارتقا و حذف بسته همچنان از مسیر ایمن شناسهٔ دقیق انجام می‌شود.",
             fg=muted, bg="#101827", justify="right", anchor="e",
             wraplength=800).pack(fill="x", pady=(4, 13))

    fields = tk.Frame(top, bg="#101827")
    fields.pack(fill="x")
    selected = tk.StringVar(value="--info")
    choices = list(engine.OPERATIONS)
    selector = ttk.Combobox(fields, state="readonly", values=choices,
                            textvariable=selected, font=("Segoe UI", 12), width=19)
    selector.pack(side="right", padx=(8, 0))
    tk.Label(fields, text="خانوادهٔ فرمان:", fg=text, bg="#101827").pack(side="right")
    args = ttk.Entry(fields, font=("Consolas", 11), justify="left")
    args.pack(side="right", fill="x", expand=True, padx=(8, 12), ipady=6)
    tk.Label(fields, text="پارامترها:", fg=text, bg="#101827").pack(side="right")
    hints = tk.StringVar()
    tk.Label(top, textvariable=hints, fg=muted, bg="#101827", anchor="e",
             wraplength=790).pack(fill="x", pady=(8, 10))

    result = tk.Text(top, bg=surface, fg=text, height=20, padx=12, pady=12,
                     wrap="word", font=("Consolas", 10), borderwidth=0)
    result.pack(fill="both", expand=True)
    result.insert("1.0", "برای مشاهدهٔ امکانات، «راهنمای رسمی» را بزنید.")
    result.configure(state="disabled")
    status = tk.StringVar(value="هیچ فرمانی اجرا نشده است.")
    tk.Label(top, textvariable=status, bg="#101827", fg=muted, anchor="e",
             wraplength=780).pack(fill="x", pady=(9, 0))
    toolbar = tk.Frame(top, bg="#101827")
    toolbar.pack(fill="x", pady=(12, 0))
    busy = False
    buttons = []

    def message(value):
        result.configure(state="normal")
        result.delete("1.0", "end")
        result.insert("1.0", value[:engine.MAX_OUTPUT])
        result.configure(state="disabled")

    def update_hint(*_):
        key = selected.get()
        hints.set(engine.OPERATIONS.get(key, "") + " · بسته‌های شخص ثالث؛ " +
                  "در صورت درخواست تغییر، تأیید جداگانه لازم است.")

    def work(plan_value):
        nonlocal busy
        if busy:
            return
        try:
            spec = engine.plan(selected.get(), "" if plan_value == "help" and
                               selected.get() in engine.INFO else (
                               "--help" if plan_value == "help" else args.get()))
        except engine.EngineError as exc:
            messagebox.showerror("پارامترهای WinGet", str(exc), parent=window)
            return
        if spec.state_changing:
            if not messagebox.askyesno(
                "تأیید تغییر توسط WinGet",
                "WinGet ممکن است تنظیمات/منابع سیستم را تغییر دهد، برنامه‌ای " +
                "را دریافت کند یا پیکربندی جدید اجرا کند. فقط پس از بررسی " +
                "فرمان رسمی ادامه دهید.\n\n" + " ".join(spec.argv) + "\n\nاجرا شود؟",
                parent=window):
                return
            if spec.high_risk and not messagebox.askyesno(
                "تأیید دوم برای تغییرات گسترده",
                "این خانوادهٔ فرمان ممکن است دسترسی شبکه، منابع مورداعتماد " +
                "یا وضعیت سیستم را تغییر دهد. هَماپ عملیات را خودکار تکرار نمی‌کند." +
                "\n\nبرای اجرای همین یک فرمان تأیید نهایی می‌دهید؟",
                parent=window):
                return
        busy = True
        for item in buttons:
            item.configure(state="disabled")
        status.set("در حال اجرای WinGet؛ فرایند درون هَماپ مدیریت می‌شود ...")

        def runner():
            try:
                output, error = engine.execute(
                    spec, allow_mutation=spec.state_changing), None
            except (engine.EngineError, ValueError, OSError) as exc:
                output, error = None, str(exc)
            def done():
                nonlocal busy
                if not window.winfo_exists():
                    return
                busy = False
                for item in buttons:
                    item.configure(state="normal")
                if error:
                    status.set("فرمان به‌طور موفق تأیید نشد.")
                    message(error)
                else:
                    status.set("پاسخ مستقیم از WinGet دریافت شد. " +
                               ("عملیات تغییر درخواست شد؛ تأیید نسخه/امضا مستقل نیست."
                                if output["state_change_requested"] else
                                "این فرمان فقط اطلاعات را مشاهده کرد."))
                    message(output["output"] or "(WinGet پاسخی برای نمایش برنگرداند)")
            try:
                window.after(0, done)
            except RuntimeError:
                pass
        threading.Thread(target=runner, daemon=True).start()

    help_btn = ttk.Button(toolbar, text="راهنمای رسمی",
                          command=lambda: work("help"))
    help_btn.pack(side="right", padx=7)
    buttons.append(help_btn)
    run_btn = ttk.Button(toolbar, text="اجرای فرمان انتخابی",
                         command=lambda: work("run"))
    run_btn.pack(side="right", padx=7)
    buttons.append(run_btn)
    ttk.Button(toolbar, text="بستن", command=window.destroy).pack(side="left")
    selector.bind("<<ComboboxSelected>>", update_hint)
    update_hint()
    return window
