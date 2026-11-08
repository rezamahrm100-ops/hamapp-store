"""Native owner first-run connection centre; no editing configuration files."""
import shutil
import subprocess
import sys
import threading

from windows_client import publisher_connection as connection


def open_setup(parent):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    bg, panel, fg, muted = "#101827", "#1e293b", "#f8fafc", "#b9c6d8"
    window = tk.Toplevel(parent)
    window.title("هَماپ | حساب‌ها و کلیدهای اتصال")
    window.geometry("850x720")
    window.minsize(720, 570)
    window.transient(parent)
    window.configure(bg=bg)

    frame = tk.Frame(window, bg=bg)
    frame.pack(fill="both", expand=True, padx=24, pady=12)
    tk.Label(frame, text="راه‌اندازی و اتصال‌های هَماپ",
             font=("Segoe UI", 20, "bold"), fg=fg, bg=bg, anchor="e").pack(fill="x", pady=(2, 5))
    tk.Label(frame, text="جست‌وجو و نصب عمومی WinGet به حساب نیاز ندارد. " +
             "انتشار برنامهٔ اختصاصی فقط به صف بررسی خصوصی ارسال می‌شود و انتشار خودکار نیست.",
             font=("Segoe UI", 10), fg=muted, bg=bg, anchor="e", wraplength=790,
             justify="right").pack(fill="x", pady=(0, 12))

    engine_bar = tk.Frame(frame, bg=panel, padx=12, pady=10)
    engine_bar.pack(fill="x", pady=(0, 13))
    engine_status = tk.StringVar(value="وضعیت موتورهای نصب بررسی نشده است.")
    tk.Label(engine_bar, textvariable=engine_status, fg=fg, bg=panel,
             font=("Segoe UI", 10), anchor="e", justify="right").pack(side="right", fill="x", expand=True)

    def inspect_engines():
        def work():
            winget = shutil.which("winget")
            cli = shutil.which("gh")
            message = ("WinGet: " + ("یافت شد" if winget else "نصب نیست؛ App Installer لازم است") +
                       "   |   GitHub CLI (اختیاری): " + ("یافت شد" if cli else "نصب نیست"))
            window.after(0, lambda: engine_status.set(message) if window.winfo_exists() else None)
        threading.Thread(target=work, daemon=True).start()

    ttk.Button(engine_bar, text="بررسی ابزارها", command=inspect_engines).pack(side="left")
    ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=7)
    tk.Label(frame, text="سرویس اختیاری ارسال بسته برای بررسی ناشر",
             fg=fg, bg=bg, font=("Segoe UI", 14, "bold"), anchor="e").pack(fill="x")
    tk.Label(frame, text="نشانی سرور، نام ناشر، گواهی عمومی CA و اثرانگشت TLS را " +
             "از مدیر سرویس بگیرید. کلید خصوصی امضا را در این صفحه وارد نکنید.",
             fg=muted, bg=bg, justify="right", anchor="e", wraplength=780).pack(fill="x", pady=(3, 9))

    fields = {}
    labels = (
        ("publisher", "شناسهٔ ناشر / نام مخزن در حساب مالک", "my-publisher"),
        ("origin", "نشانی HTTPS سرویس خصوصی", "https://your-host.example:443"),
        ("trusted_ca", "مسیر گواهی عمومی CA (.pem)", "C:\\Users\\...\\ca.pem"),
        ("server_cert_sha256", "اثر انگشت SHA-256 گواهی سرور", "64 hex characters"),
        ("token", "توکن خصوصی ناشر (مخفی؛ خالی یعنی حفظ توکن قبلی)", ""))
    for key, title, hint in labels:
        row = tk.Frame(frame, bg=bg)
        row.pack(fill="x", pady=4)
        label = tk.Label(row, text=title, fg=fg, bg=bg,
                         width=37, font=("Segoe UI", 9), anchor="e")
        label.pack(side="right", padx=(12, 0))
        entry = ttk.Entry(row, justify="left", font=("Segoe UI", 10),
                          show="•" if key == "token" else "")
        entry.pack(side="right", fill="x", expand=True, ipady=3)
        fields[key] = entry
        if key == "trusted_ca":
            ttk.Button(row, text="انتخاب PEM", command=lambda e=entry: (
                e.delete(0, "end"),
                e.insert(0, filedialog.askopenfilename(parent=window,
                       title="انتخاب گواهی عمومی CA", filetypes=[("PEM certificate", "*.pem *.crt"), ("All files", "*.*")]))
            )).pack(side="left", padx=5)

    try:
        saved = connection.read_profile()
    except (OSError, ValueError) as exc:
        saved = None
        messagebox.showerror("پیکربندی مخدوش", str(exc), parent=window)
    if saved:
        for key, value in saved["details"].items():
            if key in fields:
                fields[key].insert(0, value)

    status = tk.StringVar(value="هنوز اتصال آزمایش نشده است. توکن فقط با DPAPI ویندوز نگهداری می‌شود.")
    tk.Label(frame, textvariable=status, fg=muted, bg=bg, justify="right",
             anchor="e", wraplength=750).pack(fill="x", pady=(12, 8))

    def details():
        return {key: fields[key].get().strip() for key in
                ("publisher", "origin", "trusted_ca", "server_cert_sha256")}

    busy = False
    async_buttons = []

    def run_background(message, fn, on_done):
        nonlocal busy
        if busy:
            return
        busy = True
        status.set(message)
        for button in async_buttons:
            button.config(state="disabled")
        def work():
            try:
                outcome, error = fn(), None
            except (Exception) as exc:
                # Display generic transport errors, never secret contents.
                outcome, error = None, type(exc).__name__ + ": " + str(exc)[:160]
            def complete():
                nonlocal busy
                if not window.winfo_exists():
                    return
                busy = False
                on_done(outcome, error)
                for button in async_buttons:
                    button.config(state="normal")
            try:
                window.after(0, complete)
            except RuntimeError:
                pass
        threading.Thread(target=work, daemon=True).start()

    actions = tk.Frame(frame, bg=bg)
    actions.pack(fill="x", pady=6)

    def save():
        try:
            connection.save_profile(details(), fields["token"].get())
            fields["token"].delete(0, "end")
            status.set("اطلاعات ذخیره شد. توکن در حافظهٔ رمزگذاری‌شدهٔ حساب ویندوز نگهداری می‌شود.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("خطای ذخیرهٔ اتصال", str(exc), parent=window)

    def test_connection():
        try:
            cfg = connection.validate_profile(details())
        except (OSError, ValueError) as exc:
            messagebox.showerror("خطای تنظیمات", str(exc), parent=window)
            return
        def done(reply, error):
            status.set("اتصال TLS و اثرانگشت سرور تأیید شد؛ احراز هویت ناشر هنوز انجام نشده است."
                       if error is None else "اتصال معتبر نیست: " + error)
        run_background("در حال بررسی TLS و سرویس خصوصی (بدون ارسال توکن)...",
                       lambda: connection.probe(cfg), done)

    def delete():
        if not messagebox.askyesno("حذف اتصال",
                                   "اطلاعات اتصال و توکن رمزگذاری‌شده از این ویندوز حذف شوند؟",
                                   parent=window):
            return
        try:
            connection.remove_profile()
            for field in fields.values():
                field.delete(0, "end")
            status.set("اطلاعات اتصال محلی حذف شد.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("خطا", str(exc), parent=window)

    for title, callback in (
        ("ذخیرهٔ امن", save),
        ("بررسی TLS", test_connection),
        ("حذف اتصال", delete)
    ):
        button = ttk.Button(actions, text=title, command=callback)
        button.pack(side="right", padx=6)
        async_buttons.append(button)

    ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=10)
    tk.Label(frame, text="ارسال نسخهٔ واقعی به صف بررسی خصوصی",
             font=("Segoe UI", 13, "bold"), fg=fg, bg=bg, anchor="e").pack(fill="x")
    tk.Label(frame, text="فقط پس از تنظیم و تأیید سرویس. ارسال به معنی انتشار، " +
             "امضای برنامه یا تأیید هویت ناشر نیست.",
             fg=muted, bg=bg, anchor="e").pack(fill="x")
    files = tk.Frame(frame, bg=bg)
    files.pack(fill="x", pady=8)
    candidate = tk.StringVar()
    artifact = tk.StringVar()
    for title, variable, filetypes in (
        ("فایل اطلاعات انتشار JSON", candidate, [("JSON", "*.json")]),
        ("فایل APK / EXE / MSI / MSIX", artifact,
         [("Application files", "*.apk *.exe *.msi *.msix *.msixbundle")])):
        row = tk.Frame(files, bg=bg)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=title, bg=bg, fg=fg, width=28, anchor="e").pack(side="right")
        ttk.Entry(row, textvariable=variable).pack(side="right", fill="x", expand=True, padx=8)
        ttk.Button(row, text="انتخاب فایل", command=lambda v=variable, ft=filetypes:
                   v.set(filedialog.askopenfilename(parent=window, filetypes=ft))).pack(side="left")

    def submit():
        if not candidate.get() or not artifact.get():
            messagebox.showerror("فایل‌ها ناقص", "هر دو فایل JSON و بسته را انتخاب کنید.", parent=window)
            return
        if not messagebox.askyesno("تأیید ارسال خصوصی",
                                   "فایل انتخاب‌شده پس از بررسی TLS، امضا و هش محلی " +
                                   "به صف بررسی خصوصی شما ارسال می‌شود. ادامه؟",
                                   parent=window):
            return
        def done(receipt, error):
            if error:
                status.set("ارسال خصوصی رد شد: " + error)
            else:
                status.set("فایل در صف بررسی ذخیره شد؛ شناسه: " +
                           receipt["submission_id"] + " — انتشار خودکار انجام نشده است.")
        run_background("در حال اعتبارسنجی و ارسال امن فایل ...",
                       lambda: connection.submit(candidate.get(), artifact.get()), done)

    upload_button = ttk.Button(frame, text="ارسال برای بررسی (بدون انتشار)", command=submit)
    upload_button.pack(anchor="e", pady=7)
    async_buttons.append(upload_button)
    inspect_engines()
