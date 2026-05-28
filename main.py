import csv
import os
import tkinter as tk
from tkinter import messagebox, ttk
import matplotlib.pyplot as plt

TARIFFS = {
    "Standard": {"fixed": 50.0, "call_min": 1.0, "gb": 5.0, "sms": 0.5},
    "Unlimited": {"fixed": 200.0, "call_min": 0.0, "gb": 0.0, "sms": 0.0},
    "Student": {"fixed": 80.0, "call_min": 0.5, "gb": 2.0, "sms": 0.2}
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_subscribers(filename):
    subs = {}
    if not os.path.exists(filename):
        return subs
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            try:
                phone = row['phone'].strip()
                if not phone:
                    continue
                subs[phone] = {
                    "name": row['name'].strip(),
                    "tariff": row['tariff'].strip(),
                    "balance": float(row['balance'].strip())
                }
            except:
                pass
    return subs


def load_usage_logs(filename):
    logs = []
    if not os.path.exists(filename):
        return logs
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=',')
        for row in reader:
            try:
                phone = row['phone'].strip()
                if not phone:
                    continue
                logs.append({
                    "phone": phone,
                    "type": row['type'].strip().lower(),
                    "amount": float(row['amount'].strip())
                })
            except:
                pass
    return logs


def calculate_billing(subscribers, logs):
    for phone, data in subscribers.items():
        t_type = data['tariff']
        if t_type in TARIFFS:
            data['balance'] -= TARIFFS[t_type]['fixed']
            data['total_spent'] = TARIFFS[t_type]['fixed']
        else:
            data['total_spent'] = 0.0

    for log in logs:
        phone = log['phone']
        if phone not in subscribers:
            continue
        sub = subscribers[phone]
        tariff_rules = TARIFFS.get(sub['tariff'])
        if not tariff_rules:
            continue

        cost = 0.0
        p_type = log['type']
        amount = log['amount']

        if sub['tariff'] == "Unlimited":
            cost = 0.0
        elif sub['tariff'] in ["Standard", "Student"]:
            if p_type == "call":
                cost = amount * tariff_rules['call_min']
            elif p_type == "internet":
                if sub['tariff'] == "Student" and amount > tariff_rules['gb']:
                    cost = (amount - tariff_rules['gb']) * 15.0
                elif sub['tariff'] == "Standard":
                    cost = amount * tariff_rules['gb']
            elif p_type == "sms":
                cost = amount * tariff_rules['sms']

        sub['balance'] -= cost
        sub['total_spent'] += cost
    return subscribers


class BillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Курсова робота - Білінг")
        self.root.geometry("800x450")
        self.subscribers = {}

        tk.Label(self.root, text="Список абонентів", font=("Arial", 12, "bold")).pack(pady=10)

        table_frame = tk.Frame(self.root)
        table_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        columns = ("phone", "name", "tariff", "spent", "balance")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("phone", text="Номер")
        self.tree.heading("name", text="ПІБ")
        self.tree.heading("tariff", text="Тариф")
        self.tree.heading("spent", text="Витрачено")
        self.tree.heading("balance", text="Баланс")
        self.tree.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="Показати графік", command=self.show_visualization).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Вихід", command=self.root.quit).pack(side=tk.LEFT, padx=10)

        self.run_billing_process()

    def run_billing_process(self):
        subs_file = os.path.join(BASE_DIR, "subscribers.csv")
        logs_file = os.path.join(BASE_DIR, "usage_logs.csv")
        report_file = os.path.join(BASE_DIR, "billing_report.txt")

        raw_subs = load_subscribers(subs_file)
        logs = load_usage_logs(logs_file)

        if not raw_subs:
            messagebox.showerror("Помилка", "Файл subscribers.csv не знайдено")
            return

        self.subscribers = calculate_billing(raw_subs, logs)

        with open(report_file, mode='w', encoding='utf-8') as f:
            f.write("ЗВІТ БІЛІНГУ\n")
            for p, d in self.subscribers.items():
                f.write(f"{p} | {d['name']} | {d['tariff']} | {d['total_spent']:.2f} | {d['balance']:.2f}\n")

        for phone, data in self.subscribers.items():
            self.tree.insert("", tk.END, values=(phone, data['name'], data['tariff'], f"{data['total_spent']:.2f}",
                                                 f"{data['balance']:.2f}"))

    def show_visualization(self):
        if not self.subscribers:
            return
        names = [data['name'] for data in self.subscribers.values()]
        expenses = [data['total_spent'] for data in self.subscribers.values()]

        plt.figure(figsize=(6, 4))
        bars = plt.bar(names, expenses, color='blue', width=0.4)
        plt.title("Витрати абонентів")
        plt.xlabel("Абоненти")
        plt.ylabel("Грн")

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, yval + 1, f"{yval:.2f}", ha='center', va='bottom')

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = BillingApp(root)
    root.mainloop()