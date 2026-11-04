"""Native WinGet explorer shown independently from the owner-approved store catalog.

The explorer is a user-selected third-party manager, not a HamApp publisher.
It never trusts the static read model to authorize package installation.
"""
import threading
from windows_client import winget_discovery


def open_explorer(parent):
    import tkinter as tk
    from tkinter import messagebox, ttk

    bg, panel, text, muted, accent = "#101827", "#1e293b", "#f8fafc", "#b9c6d8", "#9fe3c7"
    window = tk.Toplevel(parent)
    window.title("هَماپ | جستجو و نصب از منبع WinGet")
    window.geometry("920x665")
    window.minsize(660, 480)
    window.configure(bg=bg)
    window.transient(parent)

    tk.Label(window, text="کاوش نرم‌افزارهای WinGet", bg=bg, fg=text,
             font=("Segoe UI", 20, "bold"), anchor="e").pack(fill="x", padx=22, pady=(17, 2))
    tk.Label(window, text="منبع ثالث مایکروسافت WinGet؛ این بسته‌ها ناشر تأییدشدهٔ هَماپ ندارند.",
             bg=bg, fg=muted, font=("Segoe UI", 10), anchor="e").pack(fill="x", padx=22)
    bar = tk.Frame(window, bg=bg)
    bar.pack(fill="x", padx=22, pady=11)
    query = tk.StringVar()
    entry = ttk.Entry(bar, textvariable=query, justify="right", font=("Segoe UI", 11))
    entry.pack(side="right", fill="x", expand=True, padx=(0, 12), ipady=7)

    style = ttk.Style(window)
    style.configure("HamApp.Treeview", rowheight=29, font=("Segoe UI", 10))
    style.configure("HamApp.Treeview.Heading", font=("Segoe UI", 10, "bold"))
    table = ttk.Treeview(window, columns=("name", "package", "version"),
                         show="headings", selectmode="browse", style="HamApp.Treeview",
                         height=8)
    for key, label, width in (("name", "نام", 275), ("package", "شناسهٔ دقیق WinGet", 295),
                               ("version", "نسخهٔ نمایشی", 135)):
        table.heading(key, text=label)
        table.column(key, width=width, anchor="w" if key != "name" else "e")
    table.pack(fill="both", expand=True, padx=22, pady=(3, 8))

    state = tk.Label(window, text="برای شروع، نام نرم‌افزار را جستجو کنید.",
                     bg=bg, fg=muted, anchor="e", justify="right")
    state.pack(fill="x", padx=22, pady=2)
    details = tk.Text(window, height=8, wrap="word", bg=panel, fg=text, bd=0,
                      font=("Consolas", 10), padx=11, pady=9)
    details.pack(fill="both", expand=True, padx=22, pady=(8, 8))
    details.insert("1.0", "اطلاعات رسمی بسته پیش از نصب از خود WinGet گرفته می‌شود.")
    details.config(state="disabled")

    footer = tk.Frame(window, bg=bg)
    footer.pack(fill="x", padx=22, pady=(0, 17))
    busy = False
    packages = {}
    selected_id = None
    verified_id = None

    def display(message):
        details.config(state="normal")
        details.delete("1.0", "end")
        details.insert("1.0", message)
        details.config(state="disabled")

    def update_controls():
        selectable = verified_id is not None and verified_id == selected_id
        install_btn.config(state="normal" if selectable and not busy else "disabled")
        upgrade_btn.config(state="normal" if selectable and not busy else "disabled")
        find_btn.config(state="normal" if not busy else "disabled")

    def job(fn, done):
        nonlocal busy
        if busy:
            return
        busy = True
        update_controls()
        def work():
            try:
                output, err = fn(), None
            except (winget_discovery.DiscoveryError, OSError, ValueError) as exc:
                output, err = None, str(exc)
            def complete():
                nonlocal busy
                if not window.winfo_exists():
                    return
                busy = False
                done(output, err)
                update_controls()
            try:
                window.after(0, complete)
            except RuntimeError:
                pass
        threading.Thread(target=work, daemon=True).start()

    def start_search(*_):
        nonlocal selected_id, verified_id
        if busy:
            return
        selected_id = None
        verified_id = None
        for row in table.get_children():
            table.delete(row)
        packages.clear()
        update_controls()
        state.config(text="جستجو در منبع اصلی winget؛ ممکن است به اینترنت نیاز داشته باشد...")
        def done(response, error):
            if error:
                state.config(text="جستجو ناموفق بود؛ منبع یا WinGet را بررسی کنید.")
                display(error)
                return
            for app in response["packages"]:
                packages[app["id"]] = app
                table.insert("", "end", iid=app["id"],
                             values=(app["name"], app["id"], app["version_label"]))
            if packages:
                state.config(text=f"{len(packages)} بستهٔ قابل‌انتخاب از منبع winget پیدا شد. انتخاب کنید تا جزئیات مستقل خوانده شود.")
            else:
                state.config(text="خروجی WinGet قابل تبدیل به شناسهٔ مطمئن نبود؛ نصب از این نتیجه غیرفعال است.")
            display(response["output"] or "پاسخی از WinGet دریافت نشد.")
        job(lambda: winget_discovery.search(query.get()), done)

    def show_selection(*_):
        nonlocal selected_id, verified_id
        if busy:
            return
        current = table.selection()
        selected_id = current[0] if current and current[0] in packages else None
        verified_id = None
        update_controls()
        if selected_id is None:
            return
        identity = selected_id
        state.config(text="در حال دریافت جزئیات دقیق از منبع WinGet...")
        def done(data, error):
            nonlocal verified_id
            if error:
                state.config(text="دریافت اطلاعات مستقل بسته ناموفق بود؛ نصب غیرفعال است.")
                display(error)
            elif selected_id == identity:
                verified_id = identity
                state.config(text="اطلاعات این بسته از WinGet دریافت شد؛ اجرا فقط با تأیید صریح شما انجام می‌شود.")
                display(data["details"])
        job(lambda: winget_discovery.show(identity), done)

    def perform(operation):
        identity = verified_id
        if busy or not identity or identity != selected_id:
            return
        prompt = (f"بستهٔ انتخاب‌شده: {identity}\nمنبع: winget (شخص ثالث)\n\n"
                  "این نرم‌افزار توسط هَماپ بررسی/امضا نشده است. "
                  "WinGet از منبع رسمی خودش فایل را می‌گیرد و ممکن است نصب‌کننده، "
                  "مجوز مدیر، قرارداد نرم‌افزار و پنجرهٔ جداگانه نشان دهد. "
                  "هَماپ هیچ‌یک را خودکار تأیید نمی‌کند.\n\n"
                  + ("نصب شود؟" if operation == "install" else "به‌روزرسانی شود؟"))
        if not messagebox.askyesno("رضایت آگاهانه برای بستهٔ ثالث", prompt, parent=window):
            return
        state.config(text="WinGet با پنجرهٔ تعاملی اجرا می‌شود؛ نتیجهٔ نصب جداگانه خوانده خواهد شد.")
        def done(receipt, error):
            if error:
                state.config(text="عملیات تأیید نشد.")
                messagebox.showerror("نتیجهٔ WinGet", error, parent=window)
            else:
                state.config(text="نسخهٔ ثبت‌شده از WinGet خوانده شد؛ امضای ناشر مستقلاً توسط هَماپ تأیید نشده است.")
                messagebox.showinfo(
                    "نتیجهٔ نصب", f"شناسه: {identity}\nنسخهٔ ثبت‌شده در WinGet: {receipt['installed_version_readback']}\n"
                    "این نتیجه اثبات اعتبار مستقل ناشر نیست.", parent=window)
        job(lambda: winget_discovery.execute_external(identity, operation), done)

    find_btn = tk.Button(bar, text="جستجو در WinGet", bg="#296e60", fg="white", bd=0,
                         padx=18, pady=7, command=start_search)
    find_btn.pack(side="left")
    install_btn = tk.Button(footer, text="نصب انتخابی", bg="#296e60", fg="white",
                            padx=20, pady=9, bd=0, command=lambda: perform("install"))
    install_btn.pack(side="right", padx=(7, 0))
    upgrade_btn = tk.Button(footer, text="به‌روزرسانی انتخابی", bg=panel, fg=text,
                            padx=16, pady=9, bd=0, command=lambda: perform("upgrade"))
    upgrade_btn.pack(side="right")
    tk.Button(footer, text="بستن", bg=panel, fg=text,
              padx=16, pady=9, bd=0, command=window.destroy).pack(side="left")
    table.bind("<<TreeviewSelect>>", show_selection)
    entry.bind("<Return>", start_search)
    update_controls()
    entry.focus_set()
    return window
