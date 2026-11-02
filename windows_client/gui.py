"""Native Tkinter Windows client: Persian RTL catalogue; owner-approved winget actions."""
import subprocess
import sys

from windows_client.core import ClientError, load_manifest, command_for


def main():
    if sys.platform != "win32":
        raise SystemExit("HamApp Windows desktop preview runs only on Windows")
    try:
        import tkinter as tk
        from tkinter import messagebox, ttk
    except ImportError as exc:
        raise SystemExit("Tkinter unavailable in this Windows build") from exc

    root = tk.Tk()
    root.title("هَماپ | فروشگاه ویندوز")
    root.geometry("880x610")
    root.minsize(670, 470)
    root.configure(bg="#111827")
    try:
        store = load_manifest()
        apps = store["apps"]
        failed = None
    except (OSError, ValueError) as exc:
        apps = []
        failed = str(exc)

    bg, surface, text, muted, accent = "#111827", "#1e293b", "#f8fafc", "#aab9ca", "#93e4c0"
    top = tk.Frame(root, bg=bg)
    top.pack(fill="x", padx=20, pady=(18, 9))
    tk.Label(top, text="هَماپ", bg=bg, fg=text, font=("Segoe UI", 25, "bold"), anchor="e").pack(fill="x")
    tk.Label(top, text="فروشگاه نرم‌افزارهای ویندوز | نسخهٔ آزمایشی", bg=bg, fg=muted,
             font=("Segoe UI", 10), anchor="e").pack(fill="x")
    query = tk.StringVar()
    search = ttk.Entry(root, textvariable=query, justify="right")
    search.pack(fill="x", padx=20, pady=8, ipady=6)
    search.insert(0, "")
    pane = tk.PanedWindow(root, orient="horizontal", bg=bg, bd=0, sashwidth=7)
    pane.pack(expand=True, fill="both", padx=20, pady=10)
    sidebar = tk.Frame(pane, bg=surface)
    details = tk.Frame(pane, bg=surface)
    pane.add(sidebar, minsize=220, width=320)
    pane.add(details, minsize=270)
    listbox = tk.Listbox(sidebar, font=("Segoe UI", 11), bg=surface, fg=text,
                         selectbackground="#256c60", selectforeground=text, relief="flat",
                         activestyle="none", highlightthickness=0)
    listbox.pack(expand=True, fill="both", padx=12, pady=12)
    title = tk.Label(details, text="", font=("Segoe UI", 17, "bold"), fg=text, bg=surface,
                     anchor="e", justify="right", wraplength=420)
    title.pack(fill="x", padx=18, pady=(22, 6))
    description = tk.Label(details, text="", font=("Segoe UI", 10), fg=muted, bg=surface,
                           anchor="e", justify="right", wraplength=420)
    description.pack(fill="x", padx=18, pady=(0, 8))
    state = tk.Label(details, text="", font=("Segoe UI", 10), fg=accent, bg=surface,
                     anchor="e", justify="right")
    state.pack(fill="x", padx=18, pady=(8, 12))
    actions = tk.Frame(details, bg=surface)
    actions.pack(fill="x", padx=18, pady=6)
    visible = []

    def selected():
        if not listbox.curselection():
            return None
        idx = listbox.curselection()[0]
        return visible[idx] if idx < len(visible) else None

    def launch(op):
        app = selected()
        if app is None:
            return
        try:
            cmd = command_for(app, op)
        except ClientError as exc:
            messagebox.showerror("هَماپ", str(exc))
            return
        prompt = (f"برنامه: {app['name_fa']}\n"
                  f"بستهٔ winget: {app['winget_id']}\nنسخه: {app['version']}\n\n"
                  "این عملیات توسط مدیر بستهٔ ویندوز انجام می‌شود؛ هَماپ کنترل امضای مستقل "
                  "نصب‌کننده را در این مرحله اثبات نمی‌کند.\n\nاجرا شود؟")
        if not messagebox.askyesno("تأیید عملیات", prompt, parent=root):
            return
        try:
            subprocess.Popen(cmd, shell=False, creationflags=subprocess.CREATE_NEW_CONSOLE)
        except OSError as exc:
            messagebox.showerror("هَماپ", f"اجرا ممکن نشد: {exc}", parent=root)

    buttons = []
    for label, op in (("اطلاعات بسته", "show"), ("نصب", "install"), ("به‌روزرسانی", "upgrade")):
        btn = tk.Button(actions, text=label, command=lambda action=op: launch(action),
                        bg="#276b60", fg="white", font=("Segoe UI", 10), bd=0,
                        padx=8, pady=9, activebackground="#348d7d")
        btn.pack(side="right", padx=(0, 8), pady=4)
        buttons.append(btn)
    disclaimer = tk.Label(root, text="فقط بسته‌های دارای تأیید قبلی | نصب با رضایت کاربر | بدون دورزدن UAC",
                          bg=bg, fg=muted, font=("Segoe UI", 9), anchor="e")
    disclaimer.pack(fill="x", padx=21, pady=(0, 12))

    def render_details(*_):
        app = selected()
        if app is None:
            title.config(text="برنامه‌ای انتخاب نشده")
            description.config(text="برای مشاهدهٔ اطلاعات، یک برنامه انتخاب کنید.")
            state.config(text="")
            enabled = False
        else:
            title.config(text=app["name_fa"])
            description.config(text=app["description"])
            enabled = app["status"] == "available"
            state.config(text=("نسخهٔ تأییدشده: " + app["version"]) if enabled else "هنوز قابل نصب نیست")
        for button in buttons:
            button.config(state="normal" if enabled else "disabled")

    def filter_apps(*_):
        term = query.get().strip().lower()
        visible.clear()
        listbox.delete(0, tk.END)
        for app in apps:
            if term in (app["name_fa"] + " " + app["description"]).lower():
                visible.append(app)
                listbox.insert(tk.END, app["name_fa"] + ("  •  آماده" if app["status"] == "available" else "  •  در توسعه"))
        if visible:
            listbox.selection_set(0)
        render_details()

    listbox.bind("<<ListboxSelect>>", render_details)
    query.trace_add("write", filter_apps)
    filter_apps()
    if failed:
        messagebox.showerror("خطای اعتبارسنجی کاتالوگ", failed, parent=root)
    root.mainloop()


if __name__ == "__main__":
    main()
