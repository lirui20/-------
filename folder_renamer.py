"""
文件批量重命名工具
功能：批量重命名文件，支持多种重命名模式

"""

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import json


class FileRenamer:
    def __init__(self, root):

        """
        初始化文件重命名工具
        :param root: tkinter窗口对象
        """
        self.root = root  # 主窗口
        self.root.title("文件批量重命名工具")  # 设置窗口标题
        self.root.geometry("950x750")  # 设置窗口初始大小
        self.root.minsize(850, 650)  # 设置窗口最小尺寸

        # 数据存储
        self.current_path = tk.StringVar()  # 当前路径变量
        self.files = []  # 原始文件列表
        self.preview_data = []  # 预览数据 [(原名, 新名), ...]
        self.history = []  # 操作历史，用于撤销

        # 重命名模式
        self.rename_mode = tk.StringVar(value="prefix")  # 默认为前缀模式

        # 扩展名处理选项
        self.keep_extension = tk.BooleanVar(value=True)  # 默认保留扩展名

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建主界面"""
        # 顶部：路径选择区
        self.create_path_frame()

        # 中部：主内容区（左右分栏）
        self.create_main_frame()

        # 底部：操作按钮区
        self.create_button_frame()

    def create_path_frame(self):
        """创建路径选择区"""
        path_frame = ttk.LabelFrame(self.root, text="选择目标文件夹", padding=10)
        path_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Entry(path_frame, textvariable=self.current_path, width=70).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(path_frame, text="浏览...", command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(path_frame, text="刷新", command=self.refresh_file_list).pack(side=tk.LEFT, padx=5)

    def create_main_frame(self):
        """创建主内容区"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 左侧：重命名设置
        self.create_settings_frame(main_frame)

        # 右侧：预览列表
        self.create_preview_frame(main_frame)

    def create_settings_frame(self, parent):
        """创建设置面板"""
        # 创建带滚动条的设置面板
        settings_container = ttk.Frame(parent)
        settings_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # 创建Canvas和滚动条
        canvas = tk.Canvas(settings_container, width=280, highlightthickness=0)
        scrollbar = ttk.Scrollbar(settings_container, orient="vertical", command=canvas.yview)
        settings_frame = ttk.Frame(canvas)

        settings_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=settings_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 重命名模式选择
        mode_frame = ttk.LabelFrame(settings_frame, text="重命名模式", padding=10)
        mode_frame.pack(fill=tk.X, pady=5, padx=5)

        modes = [
            ("添加前缀", "prefix"),
            ("添加后缀", "suffix"),
            ("查找替换", "replace"),
            ("序号重命名", "number"),
            ("正则替换", "regex"),
            ("大小写转换", "case"),
            ("删除字符", "remove")
        ]

        for text, value in modes:
            ttk.Radiobutton(mode_frame, text=text, variable=self.rename_mode,
                          value=value, command=self.on_mode_change).pack(anchor=tk.W)

        # 扩展名选项
        ext_frame = ttk.LabelFrame(settings_frame, text="扩展名处理", padding=10)
        ext_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Checkbutton(ext_frame, text="保留原扩展名不变",
                       variable=self.keep_extension).pack(anchor=tk.W)

        ttk.Label(ext_frame, text="新扩展名 (留空则不改):").pack(anchor=tk.W, pady=(5, 0))
        self.new_extension = ttk.Entry(ext_frame, width=25)
        self.new_extension.pack(fill=tk.X, pady=2)

        # 参数输入区
        self.params_frame = ttk.LabelFrame(settings_frame, text="参数设置", padding=10)
        self.params_frame.pack(fill=tk.X, pady=5, padx=5)

        # 初始化参数输入框
        self.param_entries = {}
        self.create_param_inputs()

        # 筛选条件
        filter_frame = ttk.LabelFrame(settings_frame, text="筛选条件", padding=10)
        filter_frame.pack(fill=tk.X, pady=5, padx=5)

        ttk.Label(filter_frame, text="文件名包含:").pack(anchor=tk.W)
        self.filter_include = ttk.Entry(filter_frame, width=25)
        self.filter_include.pack(fill=tk.X, pady=2)

        ttk.Label(filter_frame, text="文件名排除:").pack(anchor=tk.W)
        self.filter_exclude = ttk.Entry(filter_frame, width=25)
        self.filter_exclude.pack(fill=tk.X, pady=2)

        ttk.Label(filter_frame, text="扩展名筛选 (如: .jpg,.png):").pack(anchor=tk.W)
        self.filter_extension = ttk.Entry(filter_frame, width=25)
        self.filter_extension.pack(fill=tk.X, pady=2)

        self.filter_hidden = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="包含隐藏文件",
                       variable=self.filter_hidden).pack(anchor=tk.W, pady=5)

        self.include_folders = tk.BooleanVar(value=False)
        ttk.Checkbutton(filter_frame, text="同时包含文件夹",
                       variable=self.include_folders).pack(anchor=tk.W)

        # 预览按钮
        ttk.Button(settings_frame, text="生成预览",
                  command=self.generate_preview).pack(fill=tk.X, pady=10, padx=5)

    def create_param_inputs(self):
        """根据模式创建参数输入框"""
        # 清除旧的输入框
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        self.param_entries.clear()

        mode = self.rename_mode.get()

        if mode == "prefix":
            ttk.Label(self.params_frame, text="前缀文本:").pack(anchor=tk.W)
            entry = ttk.Entry(self.params_frame, width=25)
            entry.pack(fill=tk.X, pady=2)
            self.param_entries["prefix"] = entry

        elif mode == "suffix":
            ttk.Label(self.params_frame, text="后缀文本:").pack(anchor=tk.W)
            ttk.Label(self.params_frame, text="(添加在扩展名之前)",
                     font=("", 8)).pack(anchor=tk.W)
            entry = ttk.Entry(self.params_frame, width=25)
            entry.pack(fill=tk.X, pady=2)
            self.param_entries["suffix"] = entry

        elif mode == "replace":
            ttk.Label(self.params_frame, text="查找文本:").pack(anchor=tk.W)
            entry1 = ttk.Entry(self.params_frame, width=25)
            entry1.pack(fill=tk.X, pady=2)
            self.param_entries["find"] = entry1

            ttk.Label(self.params_frame, text="替换为:").pack(anchor=tk.W)
            entry2 = ttk.Entry(self.params_frame, width=25)
            entry2.pack(fill=tk.X, pady=2)
            self.param_entries["replace"] = entry2

        elif mode == "number":
            ttk.Label(self.params_frame, text="命名模板:").pack(anchor=tk.W)
            ttk.Label(self.params_frame, text="{n}=序号 {name}=原名 {ext}=扩展名",
                     font=("", 8)).pack(anchor=tk.W)
            entry1 = ttk.Entry(self.params_frame, width=25)
            entry1.insert(0, "{n}_{name}")
            entry1.pack(fill=tk.X, pady=2)
            self.param_entries["template"] = entry1

            ttk.Label(self.params_frame, text="起始序号:").pack(anchor=tk.W)
            entry2 = ttk.Entry(self.params_frame, width=25)
            entry2.insert(0, "1")
            entry2.pack(fill=tk.X, pady=2)
            self.param_entries["start"] = entry2

            ttk.Label(self.params_frame, text="序号位数:").pack(anchor=tk.W)
            entry3 = ttk.Entry(self.params_frame, width=25)
            entry3.insert(0, "2")
            entry3.pack(fill=tk.X, pady=2)
            self.param_entries["digits"] = entry3

        elif mode == "regex":
            ttk.Label(self.params_frame, text="正则表达式:").pack(anchor=tk.W)
            entry1 = ttk.Entry(self.params_frame, width=25)
            entry1.pack(fill=tk.X, pady=2)
            self.param_entries["pattern"] = entry1

            ttk.Label(self.params_frame, text="替换为:").pack(anchor=tk.W)
            ttk.Label(self.params_frame, text="(支持 \\1, \\2 等反向引用)",
                     font=("", 8)).pack(anchor=tk.W)
            entry2 = ttk.Entry(self.params_frame, width=25)
            entry2.pack(fill=tk.X, pady=2)
            self.param_entries["replacement"] = entry2

        elif mode == "case":
            ttk.Label(self.params_frame, text="转换类型:").pack(anchor=tk.W)
            self.case_type = tk.StringVar(value="lower")
            case_options = [
                ("全部小写", "lower"),
                ("全部大写", "upper"),
                ("首字母大写", "title"),
                ("单词首字母大写", "capitalize")
            ]
            for text, value in case_options:
                ttk.Radiobutton(self.params_frame, text=text,
                              variable=self.case_type, value=value).pack(anchor=tk.W)
            self.param_entries["case_type"] = self.case_type

        elif mode == "remove":
            ttk.Label(self.params_frame, text="删除方式:").pack(anchor=tk.W)
            self.remove_type = tk.StringVar(value="chars")
            remove_options = [
                ("删除指定字符", "chars"),
                ("删除前N个字符", "start"),
                ("删除后N个字符", "end"),
                ("删除数字", "digits"),
                ("删除空格", "spaces"),
                ("删除括号及内容", "brackets")
            ]
            for text, value in remove_options:
                ttk.Radiobutton(self.params_frame, text=text,
                              variable=self.remove_type, value=value).pack(anchor=tk.W)
            self.param_entries["remove_type"] = self.remove_type

            ttk.Label(self.params_frame, text="参数值:").pack(anchor=tk.W)
            entry = ttk.Entry(self.params_frame, width=25)
            entry.pack(fill=tk.X, pady=2)
            self.param_entries["remove_value"] = entry

    def create_preview_frame(self, parent):
        """创建预览面板"""
        preview_frame = ttk.LabelFrame(parent, text="预览", padding=10)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 创建Treeview显示预览
        columns = ("original", "new", "status")
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show="headings")

        self.preview_tree.heading("original", text="原文件名")
        self.preview_tree.heading("new", text="新文件名")
        self.preview_tree.heading("status", text="状态")

        self.preview_tree.column("original", width=220)
        self.preview_tree.column("new", width=220)
        self.preview_tree.column("status", width=80)

        # 滚动条
        scrollbar_y = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL,
                                   command=self.preview_tree.yview)
        scrollbar_x = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL,
                                   command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=scrollbar_y.set,
                                   xscrollcommand=scrollbar_x.set)

        # 布局
        self.preview_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 统计信息
        self.stats_label = ttk.Label(preview_frame, text="共 0 个文件")
        self.stats_label.pack(side=tk.BOTTOM, anchor=tk.W)

    def create_button_frame(self):
        """创建底部按钮区"""
        button_frame = ttk.Frame(self.root, padding=10)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(button_frame, text="执行重命名",
                  command=self.execute_rename).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="撤销上次操作",
                  command=self.undo_rename).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出日志",
                  command=self.export_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空预览",
                  command=self.clear_preview).pack(side=tk.LEFT, padx=5)

        # 右侧显示历史记录数
        self.history_label = ttk.Label(button_frame, text="可撤销操作: 0")
        self.history_label.pack(side=tk.RIGHT, padx=10)

    def browse_folder(self):
        """浏览选择文件夹"""
        folder = filedialog.askdirectory(title="选择包含要重命名文件的目录")
        if folder:
            self.current_path.set(folder)
            self.refresh_file_list()

    def refresh_file_list(self):
        """刷新文件列表"""
        path = self.current_path.get()
        if not path or not os.path.isdir(path):
            messagebox.showwarning("警告", "请先选择有效的文件夹路径")
            return

        self.files = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)

                # 检查是否隐藏文件
                if not self.filter_hidden.get() and item.startswith('.'):
                    continue

                # 判断是文件还是文件夹
                is_file = os.path.isfile(item_path)
                is_folder = os.path.isdir(item_path)

                if is_file:
                    self.files.append(item)
                elif is_folder and self.include_folders.get():
                    self.files.append(item)

            self.files.sort()
            self.generate_preview()
        except PermissionError:
            messagebox.showerror("错误", "没有权限访问该文件夹")
        except Exception as e:
            messagebox.showerror("错误", f"读取文件夹失败: {str(e)}")

    def on_mode_change(self):
        """重命名模式改变时的回调"""
        self.create_param_inputs()

    def apply_filter(self, files):
        """应用筛选条件"""
        include_text = self.filter_include.get().strip()
        exclude_text = self.filter_exclude.get().strip()
        ext_filter = self.filter_extension.get().strip()

        # 解析扩展名筛选
        allowed_exts = []
        if ext_filter:
            allowed_exts = [e.strip().lower() for e in ext_filter.split(',')]
            # 确保扩展名以点开头
            allowed_exts = [e if e.startswith('.') else '.' + e for e in allowed_exts]

        filtered = []
        for file in files:
            name, ext = os.path.splitext(file)

            # 扩展名筛选
            if allowed_exts and ext.lower() not in allowed_exts:
                continue

            # 包含筛选
            if include_text and include_text not in file:
                continue

            # 排除筛选
            if exclude_text and exclude_text in file:
                continue

            filtered.append(file)
        return filtered

    def generate_new_name(self, original, index):
        """根据当前模式生成新名称"""
        mode = self.rename_mode.get()

        # 分离文件名和扩展名
        name, ext = os.path.splitext(original)
        new_name = name
        new_ext = ext

        # 处理新扩展名设置
        custom_ext = self.new_extension.get().strip()
        if custom_ext:
            new_ext = custom_ext if custom_ext.startswith('.') else '.' + custom_ext

        try:
            if mode == "prefix":
                prefix = self.param_entries.get("prefix")
                if prefix:
                    new_name = prefix.get() + name

            elif mode == "suffix":
                suffix = self.param_entries.get("suffix")
                if suffix:
                    new_name = name + suffix.get()

            elif mode == "replace":
                find = self.param_entries.get("find")
                replace = self.param_entries.get("replace")
                if find:
                    replace_text = replace.get() if replace else ""
                    if self.keep_extension.get():
                        new_name = name.replace(find.get(), replace_text)
                    else:
                        full = original.replace(find.get(), replace_text)
                        new_name, new_ext = os.path.splitext(full)

            elif mode == "number":
                template = self.param_entries.get("template")
                start = self.param_entries.get("start")
                digits = self.param_entries.get("digits")
                if template and start and digits:
                    try:
                        start_num = int(start.get())
                        digit_count = int(digits.get())
                        num = str(index + start_num).zfill(digit_count)
                        new_name = template.get().replace("{n}", num).replace("{name}", name).replace("{ext}", ext)
                        # 如果模板中包含 {ext}，则不再添加扩展名
                        if "{ext}" in template.get():
                            return new_name
                    except ValueError:
                        pass

            elif mode == "regex":
                pattern = self.param_entries.get("pattern")
                replacement = self.param_entries.get("replacement")
                if pattern:
                    try:
                        replace_text = replacement.get() if replacement else ""
                        if self.keep_extension.get():
                            new_name = re.sub(pattern.get(), replace_text, name)
                        else:
                            full = re.sub(pattern.get(), replace_text, original)
                            new_name, new_ext = os.path.splitext(full)
                    except re.error:
                        pass

            elif mode == "case":
                case_type = self.param_entries.get("case_type")
                if case_type:
                    ct = case_type.get()
                    if ct == "lower":
                        new_name = name.lower()
                    elif ct == "upper":
                        new_name = name.upper()
                    elif ct == "title":
                        new_name = name.title()
                    elif ct == "capitalize":
                        new_name = name.capitalize()

            elif mode == "remove":
                remove_type = self.param_entries.get("remove_type")
                remove_value = self.param_entries.get("remove_value")
                if remove_type:
                    rt = remove_type.get()
                    if rt == "chars" and remove_value:
                        for char in remove_value.get():
                            new_name = new_name.replace(char, "")
                    elif rt == "start" and remove_value:
                        try:
                            n = int(remove_value.get())
                            new_name = name[n:]
                        except ValueError:
                            pass
                    elif rt == "end" and remove_value:
                        try:
                            n = int(remove_value.get())
                            new_name = name[:-n] if n > 0 else name
                        except ValueError:
                            pass
                    elif rt == "digits":
                        new_name = re.sub(r'\d', '', name)
                    elif rt == "spaces":
                        new_name = name.replace(" ", "")
                    elif rt == "brackets":
                        # 删除各种括号及其内容
                        new_name = re.sub(r'\([^)]*\)', '', name)
                        new_name = re.sub(r'\[[^\]]*\]', '', new_name)
                        new_name = re.sub(r'\{[^}]*\}', '', new_name)
                        new_name = re.sub(r'（[^）]*）', '', new_name)
                        new_name = re.sub(r'【[^】]*】', '', new_name)
                        new_name = new_name.strip()

        except Exception:
            pass

        # 组合文件名和扩展名
        if self.keep_extension.get():
            return new_name + ext
        else:
            return new_name + new_ext

    def generate_preview(self):
        """生成预览"""
        # 清空现有预览
        self.clear_preview()

        # 应用筛选
        filtered_files = self.apply_filter(self.files)

        # 生成预览数据
        self.preview_data = []
        new_names_set = set()  # 用于检测重名

        for index, file in enumerate(filtered_files):
            new_name = self.generate_new_name(file, index)

            # 检查状态
            if new_name == file:
                status = "无变化"
            elif not new_name or new_name == os.path.splitext(file)[1]:
                status = "名称为空"
            elif new_name.lower() in [n.lower() for n in new_names_set]:
                status = "重名冲突"
            elif self.has_invalid_chars(new_name):
                status = "非法字符"
            else:
                status = "待执行"

            new_names_set.add(new_name)
            self.preview_data.append((file, new_name, status))

            # 添加到树形视图
            self.preview_tree.insert("", tk.END, values=(file, new_name, status))

        # 更新统计
        total = len(self.preview_data)
        pending = sum(1 for _, _, s in self.preview_data if s == "待执行")
        self.stats_label.config(text=f"共 {total} 个文件，{pending} 个待重命名")
 
    def has_invalid_chars(self, name):
        """检查是否包含非法字符"""
        invalid_chars = '<>:"/\\|?*'
        # 允许反斜杠用于路径，但检查文件名部分
        filename = os.path.basename(name)
        return any(c in filename for c in invalid_chars.replace('\\', '').replace('/', ''))

    def clear_preview(self):
        """清空预览"""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        self.preview_data = []
        self.stats_label.config(text="共 0 个文件")

    def execute_rename(self):
        """执行重命名"""
        if not self.preview_data:
            messagebox.showwarning("警告", "没有可执行的重命名操作")
            return

        # 获取待执行的项目
        to_rename = [(old, new) for old, new, status in self.preview_data
                     if status == "待执行"]

        if not to_rename:
            messagebox.showinfo("提示", "没有需要重命名的文件")
            return

        # 确认执行
        if not messagebox.askyesno("确认", f"确定要重命名 {len(to_rename)} 个文件吗？"):
            return

        path = self.current_path.get()
        success_count = 0
        failed = []
        history_entry = []

        for old_name, new_name in to_rename:
            old_path = os.path.join(path, old_name)
            new_path = os.path.join(path, new_name)

            try:
                os.rename(old_path, new_path)
                success_count += 1
                history_entry.append((new_name, old_name))  # 存储反向操作
            except Exception as e:
                failed.append((old_name, str(e)))

        # 保存历史记录
        if history_entry:
            self.history.append({
                "path": path,
                "operations": history_entry,
                "timestamp": datetime.now().isoformat()
            })
            self.history_label.config(text=f"可撤销操作: {len(self.history)}")

        # 显示结果
        msg = f"成功重命名 {success_count} 个文件"
        if failed:
            msg += f"\n失败 {len(failed)} 个:\n"
            msg += "\n".join([f"{name}: {err}" for name, err in failed[:5]])
            if len(failed) > 5:
                msg += f"\n...还有 {len(failed) - 5} 个失败"

        messagebox.showinfo("完成", msg)

        # 刷新列表
        self.refresh_file_list()

    def undo_rename(self):
        """撤销上次操作"""
        if not self.history:
            messagebox.showinfo("提示", "没有可撤销的操作")
            return

        last_op = self.history[-1]
        path = last_op["path"]
        operations = last_op["operations"]

        if not messagebox.askyesno("确认",
                                   f"确定要撤销 {len(operations)} 个重命名操作吗？"):
            return

        success_count = 0
        failed = []

        for current_name, original_name in operations:
            current_path = os.path.join(path, current_name)
            original_path = os.path.join(path, original_name)

            try:
                if os.path.exists(current_path):
                    os.rename(current_path, original_path)
                    success_count += 1
                else:
                    failed.append((current_name, "文件不存在"))
            except Exception as e:
                failed.append((current_name, str(e)))

        # 移除历史记录
        self.history.pop()
        self.history_label.config(text=f"可撤销操作: {len(self.history)}")

        # 显示结果
        msg = f"成功撤销 {success_count} 个重命名"
        if failed:
            msg += f"\n失败 {len(failed)} 个"

        messagebox.showinfo("完成", msg)

        # 刷新列表
        if self.current_path.get() == path:
            self.refresh_file_list()

    def export_log(self):
        """导出操作日志"""
        if not self.history:
            messagebox.showinfo("提示", "没有操作记录可导出")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存日志文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt")]
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.history, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"日志已导出到:\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {str(e)}")


def main():
    root = tk.Tk()

    # 设置样式
    style = ttk.Style()
    try:
        style.theme_use('vista')  # Windows风格
    except:
        style.theme_use('clam')  # 备选主题

    app = FileRenamer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
