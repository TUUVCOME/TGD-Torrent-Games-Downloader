import requests
from bs4 import BeautifulSoup
import os
import webbrowser
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import threading

# Сайты
SITES = {
    "FitGirl": "https://fitgirl-repacks.site",
    "Dodi": "https://dodi-repacks.site",
}

FREEP_URL = "https://freetp.org/"

def search_site(site_name, query, max_pages=1, progress_callback=None):
    results = []

    if site_name in ["FitGirl", "Dodi"]:
        url = SITES[site_name] + f"/?s={query}"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")

        if site_name == "FitGirl":
            for post in soup.select("h1.entry-title a"):
                results.append((post.text.strip(), post["href"], site_name))
        elif site_name == "Dodi":
            for post in soup.select("h2.entry-title a"):
                results.append((post.text.strip(), post["href"], site_name))

    elif site_name == "FreeTP":
        for page in range(1, max_pages+1):
            url = f"{FREEP_URL}page/{page}/"
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            for post in soup.select("h2.entry-title a"):
                title = post.text.strip()
                href = post['href']
                if query.lower() in title.lower():
                    results.append((title, href, "FreeTP"))
            if progress_callback:
                progress_callback(page)

    return results

def get_download_links(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    torrents, magnets = [], []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".torrent"):
            torrents.append(href)
        if href.startswith("magnet:?"):
            magnets.append(href)
    return torrents, magnets

class TorrentGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Torrent Search GUI")
        self.root.geometry("720x600")
        self.root.configure(bg="#1e1e1e")

        header_font = ("Segoe UI", 12, "bold")
        entry_font = ("Segoe UI", 11)

        tk.Label(root, text="Введите название игры:", fg="#ffffff", bg="#1e1e1e", font=header_font).pack(pady=8)
        self.query_entry = tk.Entry(root, width=50, font=entry_font, bg="#2e2e2e", fg="#ffffff", insertbackground="white")
        self.query_entry.pack(pady=5)

        tk.Label(root, text="Выберите сайты:", fg="#ffffff", bg="#1e1e1e", font=header_font).pack(pady=8)
        self.site_vars = {}
        sites_frame = tk.Frame(root, bg="#1e1e1e")
        sites_frame.pack()
        for site in list(SITES.keys()) + ["FreeTP"]:
            var = tk.BooleanVar(value=True)
            tk.Checkbutton(sites_frame, text=site, variable=var, bg="#1e1e1e", fg="#ffffff", selectcolor="#3e3e3e", font=entry_font).pack(side=tk.LEFT, padx=10)
            self.site_vars[site] = var

        tk.Label(root, text="Количество страниц для сканирования FreeTP (1-309):", fg="#ffffff", bg="#1e1e1e", font=entry_font).pack(pady=5)
        self.freetp_pages_entry = tk.Entry(root, width=10, font=entry_font, bg="#2e2e2e", fg="#ffffff", insertbackground="white")
        self.freetp_pages_entry.insert(0, "5")
        self.freetp_pages_entry.pack(pady=5)

        # Скрытый прогрессбар под стилистику
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Custom.Horizontal.TProgressbar", troughcolor='#2e2e2e', background='#3e8ef7', bordercolor='#1e1e1e', lightcolor='#3e8ef7', darkcolor='#3e8ef7')
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, maximum=100, variable=self.progress_var, style="Custom.Horizontal.TProgressbar")
        self.progress_bar.pack(pady=5, fill=tk.X, padx=20)
        self.progress_bar.pack_forget()  # Скрываем по умолчанию

        tk.Button(root, text="Искать", command=self.start_search_thread, bg="#3e8ef7", fg="#ffffff", font=header_font, relief=tk.FLAT).pack(pady=10)

        self.results_box = tk.Listbox(root, width=100, bg="#2e2e2e", fg="#ffffff", selectbackground="#3e8ef7", font=entry_font)
        self.results_box.pack(pady=10, fill=tk.BOTH, expand=True)

        tk.Button(root, text="Скачать / открыть", command=self.download_selected, bg="#3e8ef7", fg="#ffffff", font=header_font, relief=tk.FLAT).pack(pady=10)

        self.results = []

    def update_progress(self, page):
        max_pages = int(self.freetp_pages_entry.get())
        percent = (page / max_pages) * 100
        self.progress_var.set(percent)

    def start_search_thread(self):
        thread = threading.Thread(target=self.search)
        thread.start()

    def search(self):
        query = self.query_entry.get().strip()
        if not query:
            messagebox.showwarning("Внимание", "Введите название игры")
            return

        freetp_pages = 5
        show_progress = False
        if self.site_vars.get("FreeTP", tk.BooleanVar()).get():
            try:
                freetp_pages = int(self.freetp_pages_entry.get())
                if freetp_pages < 1 or freetp_pages > 309:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Ошибка", "Введите число от 1 до 309 для FreeTP")
                return
            show_progress = True
            if freetp_pages > 10:
                messagebox.showinfo("Внимание", "Сканирование большого количества страниц может занять время")

        self.results_box.delete(0, tk.END)
        self.results = []

        if show_progress:
            self.progress_bar.pack(pady=5, fill=tk.X, padx=20)
            self.progress_var.set(0)

        for site, var in self.site_vars.items():
            if var.get():
                pages = freetp_pages if site == "FreeTP" else 1
                site_results = search_site(site, query, max_pages=pages, progress_callback=self.update_progress if site=="FreeTP" else None)
                for title, link, source in site_results:
                    display = f"{title} ({source})"
                    self.results_box.insert(tk.END, display)
                    self.results.append((title, link, source))

        if show_progress:
            self.progress_bar.pack_forget()

        if not self.results:
            messagebox.showinfo("Результат", "Ничего не найдено")

    def download_selected(self):
        sel = self.results_box.curselection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите релиз")
            return
        idx = sel[0]
        title, link, source = self.results[idx]

        torrents, magnets = get_download_links(link)
        if not torrents and not magnets:
            messagebox.showerror("Ошибка", "Ссылки не найдены")
            return

        options = []
        for t in torrents:
            options.append(("torrent", t))
        for m in magnets:
            options.append(("magnet", m))

        choice_str = "\n".join([f"{i+1}: {t[1][:70]}..." for i, t in enumerate(options)])
        choice_num = simpledialog.askinteger("Выбор ссылки", f"Выберите ссылку для загрузки/открытия:\n{choice_str}")
        if choice_num is None or choice_num < 1 or choice_num > len(options):
            return
        ctype, url = options[choice_num-1]

        if ctype == "torrent":
            fname = os.path.basename(url.split("?")[0])
            try:
                r = requests.get(url)
                with open(fname, "wb") as f:
                    f.write(r.content)
                messagebox.showinfo("Готово", f"Скачано как {fname}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось скачать: {e}")
        else:
            webbrowser.open(url)
            messagebox.showinfo("Открыто", "Magnet ссылка открыта в торрент-клиенте")

if __name__ == "__main__":
    root = tk.Tk()
    app = TorrentGUI(root)
    root.mainloop()