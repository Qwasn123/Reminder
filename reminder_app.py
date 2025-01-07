import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar
import json
import os

class ReminderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("桌面提醒软件")
        self.root.geometry("1000x700")
        
        self.events = {}
        self.load_events()
        
        self.current_date = datetime.now()
        self.selected_date = self.current_date
        
        self.reminded_events = set()  # 添加已提醒事件的集合
        self.create_widgets()
        self.update_clock()
        self.check_reminders()

    def create_widgets(self):
        # 设置主题颜色
        self.style = ttk.Style()
        self.style.configure('Calendar.TFrame', background='#ffffff')
        self.style.configure('Nav.TButton', padding=5)
        self.style.configure('CalendarDay.TButton', padding=5)
        self.style.configure('Clock.TLabel', font=('Arial', 36))
        
        # 主框架分为左右两部分
        self.main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧日历部分
        self.calendar_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.calendar_frame)

        # 日历导航
        nav_frame = ttk.Frame(self.calendar_frame)
        nav_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(nav_frame, text="<", command=self.prev_month, width=3).pack(side=tk.LEFT, padx=5)
        self.month_label = ttk.Label(nav_frame, font=('Arial', 12, 'bold'))
        self.month_label.pack(side=tk.LEFT, padx=50)
        ttk.Button(nav_frame, text=">", command=self.next_month, width=3).pack(side=tk.LEFT)

        # 星期标签
        weekday_frame = ttk.Frame(self.calendar_frame)
        weekday_frame.pack(fill=tk.X, padx=5)
        weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        for i, day in enumerate(weekdays):
            label = ttk.Label(weekday_frame, text=day, width=12)
            label.grid(row=0, column=i, padx=2, pady=5)
            if day in ['周六', '周日']:
                label.configure(foreground='red')
            weekday_frame.grid_columnconfigure(i, weight=1)

        # 日历网格
        self.calendar_grid = ttk.Frame(self.calendar_frame)
        self.calendar_grid.pack(fill=tk.BOTH, expand=True, padx=5)

        # 右侧事件显示和时钟部分
        self.right_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.right_frame)

        # 时钟显示
        self.time_label = ttk.Label(self.right_frame, font=('Arial', 36))
        self.time_label.pack(pady=10)

        # 选中日期显示
        self.selected_date_label = ttk.Label(self.right_frame, font=('Arial', 12))
        self.selected_date_label.pack(pady=5)

        # 事件列表区域
        self.date_frame = ttk.LabelFrame(self.right_frame, text="事件列表")
        self.date_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.date_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.event_listbox = tk.Listbox(self.date_frame, font=('Arial', 10),
                                       yscrollcommand=scrollbar.set)
        self.event_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.config(command=self.event_listbox.yview)

        # 按钮区域
        button_frame = ttk.Frame(self.right_frame)
        button_frame.pack(fill=tk.X, pady=5, padx=5)
        ttk.Button(button_frame, text="添加事件", command=self.show_add_event_dialog,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除事件", command=self.delete_event,
                   style='Action.TButton').pack(side=tk.LEFT, padx=5)

        self.update_calendar()

    def update_calendar(self):
        # 清除现有日历网格
        for widget in self.calendar_grid.winfo_children():
            widget.destroy()

        # 更新月份标签
        self.month_label.config(text=f"{self.current_date.year}年 {self.current_date.month}月")

        # 获取当月日历
        year = self.current_date.year
        month = self.current_date.month
        cal = calendar.monthcalendar(year, month)

        # 配置网格列的权重，使其均匀分布
        for i in range(7):
            self.calendar_grid.grid_columnconfigure(i, weight=1)

        # 设置固定的按钮大小
        btn_width = 8
        btn_height = 2

        # 创建日历网格
        for week_num, week in enumerate(cal):
            self.calendar_grid.grid_rowconfigure(week_num, weight=1)
            for day_num, day in enumerate(week):
                frame = ttk.Frame(self.calendar_grid, width=100, height=80)
                frame.grid(row=week_num, column=day_num, sticky='nsew', padx=1, pady=1)
                frame.grid_propagate(False)
                
                if day != 0:
                    date = datetime(year, month, day)
                    btn = ttk.Button(frame, text=str(day),
                                   command=lambda d=date: self.select_date(d))
                    btn.place(relx=0, rely=0, relwidth=1, relheight=1)
                    
                    # 标记当前日期
                    if date.date() == datetime.now().date():
                        btn.configure(style='Current.TButton')
                    
                    # 标记周末
                    if day_num >= 5:
                        btn.configure(style='Weekend.TButton')
                    
                    # 标记选中日期
                    if date.date() == self.selected_date.date():
                        btn.configure(style='Selected.TButton')
                else:
                    # 空白日期占位符
                    placeholder = ttk.Frame(frame)
                    placeholder.place(relx=0, rely=0, relwidth=1, relheight=1)

    def select_date(self, date):
        """选择日期时更新显示"""
        self.selected_date = date
        self.selected_date_label.config(
            text=f"选中日期: {date.strftime('%Y年%m月%d日 %A')}")
        self.update_event_list()

    def show_add_event_dialog(self):
        """显示添加事件对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加事件")
        dialog.geometry("300x200")  # 减小对话框大小
        dialog.transient(self.root)
        
        # 设置对话框位置为主窗口中心
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50))
        
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 日期输入
        ttk.Label(frame, text="日期:").pack(pady=5)
        date_entry = ttk.Entry(frame)
        date_entry.pack(fill=tk.X, padx=5)
        date_entry.insert(0, self.selected_date.strftime("%Y-%m-%d"))
        date_entry.configure(state='readonly')  # 设置为只读
        
        # 事件内容输入
        ttk.Label(frame, text="事件内容:").pack(pady=5)
        event_entry = ttk.Entry(frame)
        event_entry.pack(fill=tk.X, padx=5)
        
        # 时间输入
        ttk.Label(frame, text="时间 (HH:MM):").pack(pady=5)
        time_entry = ttk.Entry(frame)
        time_entry.pack(fill=tk.X, padx=5)
        time_entry.insert(0, datetime.now().strftime("%H:%M"))
        
        # 按钮区域
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def add():
            description = event_entry.get()
            time = time_entry.get()
            
            if not description:
                messagebox.showerror("错误", "请输入事件内容！")
                return
            
            try:
                datetime.strptime(time, "%H:%M")
            except ValueError:
                messagebox.showerror("错误", "请输入正确的时间格式（HH:MM）！")
                return
            
            self.add_event(description, time)
            dialog.destroy()
        
        # 修改按钮布局
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        ok_button = ttk.Button(button_frame, text="确定", command=add)
        ok_button.grid(row=0, column=0, padx=5, sticky='e')
        
        cancel_button = ttk.Button(button_frame, text="取消", command=dialog.destroy)
        cancel_button.grid(row=0, column=1, padx=5, sticky='w')
        
        # 绑定回车键到确定按钮
        dialog.bind('<Return>', lambda e: add())
        # 绑定 Escape 键到取消按钮
        dialog.bind('<Escape>', lambda e: dialog.destroy())
        
        # 设置焦点到事件输入框
        event_entry.focus_set()
        
        # 使对话框模态
        dialog.grab_set()
        dialog.wait_window()

    def add_event(self, description, time, date=None):
        """添加事件"""
        if not description or not time:
            messagebox.showerror("错误", "请填写完整信息！")
            return
            
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            messagebox.showerror("错误", "请输入正确的时间格式（HH:MM）！")
            return
            
        if date is None:
            date = self.selected_date
        
        date_str = date.strftime("%Y-%m-%d")
        if date_str not in self.events:
            self.events[date_str] = []
            
        self.events[date_str].append({
            "time": time,
            "description": description
        })
        
        # 添加新事件时，确保不在已提醒集合中
        event_id = f"{date_str}_{time}_{description}"
        self.reminded_events.discard(event_id)
        
        messagebox.showinfo("成功", "事件添加成功！")
        self.save_events()
        self.update_event_list()
        self.update_calendar()

    def delete_event(self):
        """删除选中的事件"""
        selection = self.event_listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的事件！")
            return
            
        date_str = self.selected_date.strftime("%Y-%m-%d")  # 使用选中的日期
        if date_str in self.events:
            del self.events[date_str][selection[0]]
            self.save_events()
            self.update_event_list()
            messagebox.showinfo("成功", "事件已删除！")

    def update_event_list(self):
        """更新事件列表显示"""
        self.event_listbox.delete(0, tk.END)
        date_str = self.selected_date.strftime("%Y-%m-%d")
        
        if date_str in self.events:
            # 按时间排序显示事件
            sorted_events = sorted(self.events[date_str], key=lambda x: x['time'])
            for event in sorted_events:
                self.event_listbox.insert(tk.END, 
                    f"{event['time']} - {event['description']}")

    def check_reminders(self):
        """检查是否有需要提醒的事件"""
        current_time = datetime.now()
        current_date = current_time.strftime("%Y-%m-%d")
        current_time_str = current_time.strftime("%H:%M")
        
        if current_date in self.events:
            for event in self.events[current_date]:
                # 创建唯一标识符
                event_id = f"{current_date}_{event['time']}_{event['description']}"
                
                # 检查是否在当前分钟且未提醒过
                if (event['time'] == current_time_str and 
                    current_time.second == 0 and 
                    event_id not in self.reminded_events):
                    
                    messagebox.showinfo("提醒", f"到点提醒：{event['description']}")
                    self.reminded_events.add(event_id)  # 添加到已提醒集合
        
        # 每天零点清除前一天的提醒记录
        if current_time.hour == 0 and current_time.minute == 0 and current_time.second == 0:
            self.reminded_events.clear()
        
        self.root.after(1000, self.check_reminders)

    def save_events(self):
        """保存事件到文件"""
        with open('events.json', 'w', encoding='utf-8') as f:
            json.dump(self.events, f, ensure_ascii=False)

    def load_events(self):
        """从文件加载事件"""
        if os.path.exists('events.json'):
            with open('events.json', 'r', encoding='utf-8') as f:
                self.events = json.load(f)

    def prev_month(self):
        self.current_date = self.current_date.replace(day=1) - timedelta(days=1)
        self.current_date = self.current_date.replace(day=1)
        self.update_calendar()

    def next_month(self):
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        self.update_calendar()

    def update_clock(self):
        """更新时钟显示"""
        current_time = datetime.now()
        self.time_label.config(text=current_time.strftime("%H:%M:%S"))
        self.root.after(1000, self.update_clock)

if __name__ == "__main__":
    root = tk.Tk()
    
    # 创建自定义样式
    style = ttk.Style()
    style.theme_use('clam')  # 使用 clam 主题作为基础
    
    # 配置通用样式
    style.configure('TButton', padding=3)
    style.configure('Current.TButton', background='#e6f3ff')
    style.configure('Weekend.TButton', foreground='red')
    style.configure('Selected.TButton', background='#cce8ff')
    style.configure('TLabel', padding=2)
    style.configure('TLabelframe', padding=5)
    
    app = ReminderApp(root)
    root.mainloop() 