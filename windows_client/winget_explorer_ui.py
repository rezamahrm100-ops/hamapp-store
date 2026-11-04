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
        uninstall_btn.config(state="normal" if selectable and not busy else "disabled")
        find_btn.config(state="normal" if not busy else "disabled")
        installed_btn.config(state="normal" if not busy else "disabled")

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

    def view_installed():
        nonlocal selected_id, verified_id
        if busy:
            return
        selected_id = None
        verified_id = None
        table.delete(*table.get_children())
        packages.clear()
        update_controls()
        state.config(text="خواندن محلی برنامه‌های نصب‌شده از منبع WinGet...")
        def done(data, error):
            if error:
                state.config(text="خواندن فهرست نصب‌شده‌ها ناموفق بود؛ عملیاتی مجاز نیست.")
                display(error)
                return
            for item in data["packages"]:
                packages[item["id"]] = dict(item, name=item["id"], version_label=item["version"])
                table.insert("", "end", iid=item["id"],
                             values=(item["id"], item["id"], item["version"]))
            state.config(text=f"{len(packages)} برنامه از منبع WinGet در این دستگاه یافت شد.")
            display("فهرست فقط از رایانهٔ شما خوانده می‌شود و ارسال نمی‌شود. برای مدیریت بسته، ابتدا آن را انتخاب و اطلاعات را بررسی کنید.")
        job(lambda: winget_discovery.installed_packages(), done)

    def show_selection(*_):
        nonlocal selected_id, verified_id
        if busy:
            # Invalidate the previous inspected package when selection changes
            # during an asynchronous WinGet show; never enable the wrong ID.
            selected_id = None
            verified_id = None
            update_controls()
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
            elif selected_id == identity and table.selection() == (identity,):
                verified_id = identity
                state.config(text="اطلاعات این بسته از WinGet دریافت شد؛ اجرا فقط با تأیید صریح شما انجام می‌شود.")
                display(data["details"])
        job(lambda: winget_discovery.show(identity), done)

    def perform(operation):
        identity = verified_id
        if busy or not identity or identity != selected_id or table.selection() != (identity,):
            return
        prompt = (f"بستهٔ انتخاب‌شده: {identity}\nمنبع: winget (شخص ثالث)\n\n"
                  "این نرم‌افزار توسط هَماپ بررسی/امضا نشده است. "
                  "WinGet از منبع رسمی خودش فایل را می‌گیرد و ممکن است نصب‌کننده، "
                  "مجوز مدیر، قرارداد نرم‌افزار و پنجرهٔ جداگانه نشان دهد. "
                  "هَماپ هیچ‌یک را خودکار تأیید نمی‌کند.\n\n"
                  + ("نصب شود؟" if operation == "install" else
                     "به‌روزرسانی شود؟" if operation == "upgrade" else
                     "این برنامه حذف شود؟ ممکن است داده‌های برنامه نیز پاک شوند."))
        if not messagebox.askyesno("رضایت آگاهانه برای بستهٔ ثالث", prompt, parent=window):
            return
        state.config(text="WinGet با پنجرهٔ تعاملی اجرا می‌شود؛ نتیجهٔ نصب جداگانه خوانده خواهد شد.")
        def done(receipt, error):
            if error:
                state.config(text="عملیات تأیید نشد.")
                messagebox.showerror("نتیجهٔ WinGet", error, parent=window)
            elif operation == "uninstall":
                state.config(text="عدم ثبت بسته در فهرست WinGet پس از حذف تأیید شد.")
                messagebox.showinfo("نتیجهٔ حذف",
                    f"شناسه: {identity}\nبسته دیگر در فهرست WinGet ثبت نیست.",
                    parent=window)
            else:
                state.config(text="نسخهٔ نصب‌شده از WinGet خوانده شد؛ امضای ناشر مستقلاً توسط هَماپ بررسی نشده است.")
                messagebox.showinfo("نتیجهٔ WinGet",
                    f"شناسه: {identity}\nنسخهٔ ثبت‌شده: {receipt['installed_version_readback']}\n"
                    "این نتیجه اثبات مستقل اصالت ناشر نیست.", parent=window)
        job(lambda: winget_discovery.execute_external(identity, operation), done)

    find_btn = ttk.Button(bar, text="جستجو در WinGet", style="HamApp.Primary.TButton",
                          command=start_search)
    find_btn.pack(side="left")
    installed_btn = ttk.Button(bar, text="نصب‌شده‌ها", style="HamApp.Secondary.TButton",
                               command=view_installed)
    installed_btn.pack(side="left", padx=(7, 0))
    install_btn = ttk.Button(footer, text="نصب انتخابی", style="HamApp.Primary.TButton",
                             command=lambda: perform("install"))
    install_btn.pack(side="right", padx=(7, 0))
    upgrade_btn = ttk.Button(footer, text="به‌روزرسانی انتخابی",
                             style="HamApp.Secondary.TButton", command=lambda: perform("upgrade"))
    upgrade_btn.pack(side="right")
    uninstall_btn = ttk.Button(footer, text="حذف انتخابی",
                               style="HamApp.Secondary.TButton", command=lambda: perform("uninstall"))
    uninstall_btn.pack(side="right", padx=(7, 0))
    ttk.Button(footer, text="بستن", style="HamApp.Secondary.TButton",
               command=window.destroy).pack(side="left")
    table.bind("<<TreeviewSelect>>", show_selection)
    entry.bind("<Return>", start_search)
    update_controls()
    entry.focus_set()
    return window
