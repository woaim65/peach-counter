#!/usr/bin/env python3
"""
桃数统计 v6 — 单张 + 批量双模式
双击 run.bat 启动（Windows），或 python peach_counter.py 直接运行
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
import os
import sys
import subprocess
import threading

# ====== 核心计数（同V5，不动） ======

def count_peaches(img_bgr, mode="ripe"):
    h, w = img_bgr.shape[:2]
    scale = 1200 / max(h, w)
    if scale < 1:
        new_w, new_h = int(w * scale), int(h * scale)
        img = cv2.resize(img_bgr, (new_w, new_h))
    else:
        img = img_bgr.copy()

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    if mode == "ripe":
        lower1 = np.array([0, 30, 40])
        upper1 = np.array([25, 255, 255])
        lower2 = np.array([35, 40, 40])
        upper2 = np.array([85, 255, 255])
        lower3 = np.array([10, 20, 20])
        upper3 = np.array([35, 150, 150])
        area_min, circ_min = 150, 0.3
    elif mode == "green":
        lower1 = np.array([0, 20, 20])
        upper1 = np.array([30, 255, 255])
        lower2 = np.array([20, 20, 20])
        upper2 = np.array([95, 200, 255])
        lower3 = np.array([5, 10, 10])
        upper3 = np.array([40, 100, 130])
        area_min, circ_min = 80, 0.25
    else:
        # auto ≡ ripe（实际测试 ripe 模式表现最稳）
        mode = "ripe"
        lower1 = np.array([0, 30, 40])
        upper1 = np.array([25, 255, 255])
        lower2 = np.array([35, 40, 40])
        upper2 = np.array([85, 255, 255])
        lower3 = np.array([10, 20, 20])
        upper3 = np.array([35, 150, 150])
        area_min, circ_min = 150, 0.3

    mask = (cv2.inRange(hsv, lower1, upper1) |
            cv2.inRange(hsv, lower2, upper2) |
            cv2.inRange(hsv, lower3, upper3))

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    fruits = []
    for c in contours:
        area = cv2.contourArea(c)
        if not (area_min < area < 30000):
            continue
        perimeter = cv2.arcLength(c, True)
        if perimeter == 0:
            continue
        if 4 * np.pi * area / (perimeter * perimeter) < circ_min:
            continue
        xb, yb, wb, hb = cv2.boundingRect(c)
        if min(wb, hb) / max(wb, hb) < 0.5:
            continue
        fruits.append(c)

    seen = set()
    unique = []
    for c in fruits:
        xb, yb, wb, hb = cv2.boundingRect(c)
        center = ((xb + wb // 2) % 10000, (yb + hb // 2) % 10000)
        if center not in seen:
            seen.add(center)
            unique.append(c)
    return _draw_result(img, unique)

def _count_auto(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_all = np.array([0, 10, 10])
    upper_all = np.array([95, 255, 255])
    mask = cv2.inRange(hsv, lower_all, upper_all)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    fruits = []
    for c in contours:
        area = cv2.contourArea(c)
        if not (60 < area < 30000):
            continue
        perimeter = cv2.arcLength(c, True)
        if perimeter == 0:
            continue
        if 4 * np.pi * area / (perimeter * perimeter) < 0.2:
            continue
        xb, yb, wb, hb = cv2.boundingRect(c)
        if min(wb, hb) / max(wb, hb) < 0.4:
            continue
        fruits.append(c)
    seen = set()
    unique = []
    for c in fruits:
        xb, yb, wb, hb = cv2.boundingRect(c)
        center = ((xb + wb // 2) % 10000, (yb + hb // 2) % 10000)
        if center not in seen:
            seen.add(center)
            unique.append(c)
    return _draw_result(img, unique)

def _draw_result(img, contours):
    result = img.copy()
    for i, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(result, str(i + 1), (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    return len(contours), result

# ====== 支持的图片格式 ======

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

# ====== UI ======

class PeachCounterApp:
    def __init__(self, root):
        self.root = root
        root.title("桃数统计")
        root.geometry("620x580")
        root.minsize(580, 480)

        # 标题
        tk.Label(root, text="桃数统计", font=("Arial", 18, "bold")).pack(pady=(12, 4))

        # 模式
        frame_mode = tk.Frame(root)
        frame_mode.pack(pady=4)
        tk.Label(frame_mode, text="桃子类型：").pack(side=tk.LEFT, padx=4)
        self.mode_var = tk.StringVar(value="auto")
        for text, val in [("熟桃", "ripe"), ("青桃", "green"), ("自动", "auto")]:
            tk.Radiobutton(frame_mode, text=text, variable=self.mode_var, value=val).pack(side=tk.LEFT, padx=4)

        # 按钮行
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=6)
        tk.Button(btn_frame, text="单张选图", command=self.select_single,
                  bg="#4CAF50", fg="white", width=12).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="批量选文件夹", command=self.select_batch,
                  bg="#2196F3", fg="white", width=14).pack(side=tk.LEFT, padx=6)

        # 进度条
        self.progress = ttk.Progressbar(root, length=500, mode="determinate")
        self.progress.pack(pady=4, padx=20, fill=tk.X)

        # 结果表格（批量模式用）
        cols = ("文件名", "个数", "状态")
        self.tree = ttk.Treeview(root, columns=cols, show="headings",
                                  height=12, selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center" if c != "文件名" else "w",
                             width=300 if c == "文件名" else 120)
        vsb = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(pady=6, padx=20, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<Double-1>", self.open_result)

        # 统计栏
        self.summary_frame = tk.Frame(root)
        self.summary_frame.pack(pady=4, fill=tk.X, padx=20)
        self.lbl_total = tk.Label(self.summary_frame, text="总数：--", font=("Arial", 12))
        self.lbl_total.pack(side=tk.LEFT)
        self.lbl_count = tk.Label(self.summary_frame, text="图片：--", font=("Arial", 12))
        self.lbl_count.pack(side=tk.RIGHT)

        # 状态栏
        self.lbl_status = tk.Label(root, text="就绪", fg="gray", anchor="w", font=("Arial", 8))
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=2)

        # 内部状态
        self.batch_dir = None

    def set_status(self, text):
        self.lbl_status.config(text=text)
        self.root.update()

    # ---- 单张 ----

    def select_single(self):
        path = filedialog.askopenfilename(
            title="选一张果园照片",
            filetypes=[("图片", "*.jpg *.jpeg *.png")]
        )
        if not path:
            return
        self.set_status(f"处理: {os.path.basename(path)}")
        try:
            img = cv2.imread(path)
            if img is None:
                messagebox.showerror("错误", "无法读取图片")
                return
            n, result_img = count_peaches(img, self.mode_var.get())
            out = os.path.splitext(path)[0] + "_result.jpg"
            cv2.imwrite(out, result_img)

            # 表格里加一行
            self.tree.delete(*self.tree.get_children())
            self.tree.insert("", "end", values=(os.path.basename(path), n, "OK"),
                             tags=(out,))

            # 更新表格可见
            self.lbl_total.config(text=f"总数：{n}")
            self.lbl_count.config(text="图片：1")

            messagebox.showinfo("单张完成", f"数到 {n} 个桃子\n结果图：{os.path.basename(out)}")
            self.set_status("完成")
        except Exception as e:
            messagebox.showerror("错误", str(e))
            self.set_status("出错")

    # ---- 批量 ----

    def select_batch(self):
        folder = filedialog.askdirectory(title="选一个文件夹，跑里面所有图片")
        if not folder:
            return
        self.batch_dir = folder
        self.run_batch(folder)

    def run_batch(self, folder):
        # 找图
        images = [f for f in os.listdir(folder)
                  if os.path.splitext(f)[1].lower() in IMAGE_EXTS]
        if not images:
            messagebox.showinfo("提示", f"文件夹里没有图片\n{folder}")
            return
        images.sort()

        self.tree.delete(*self.tree.get_children())
        self.progress["value"] = 0
        self.progress["maximum"] = len(images) * 2  # 读+写各算一次
        self.set_status(f"开始批量：{len(images)} 张图片")

        total_count = 0
        error_count = 0

        for i, fname in enumerate(images):
            path = os.path.join(folder, fname)
            self.progress["value"] = i * 2 + 1
            self.set_status(f"[{i+1}/{len(images)}] {fname}")

            try:
                img = cv2.imread(path)
                if img is None:
                    self.tree.insert("", "end", values=(fname, "?", "读图失败"),
                                     tags=("",))
                    error_count += 1
                    continue

                n, result_img = count_peaches(img, self.mode_var.get())
                out = os.path.splitext(path)[0] + "_result.jpg"
                cv2.imwrite(out, result_img)
                total_count += n
                self.progress["value"] = i * 2 + 2
                self.tree.insert("", "end", values=(fname, n, "OK"),
                                 tags=(out,))
            except Exception as e:
                self.tree.insert("", "end", values=(fname, "?", str(e)[:20]),
                                 tags=("",))
                error_count += 1

        # 更新摘要
        self.lbl_total.config(text=f"总落果数：{total_count}")
        self.lbl_count.config(text=f"图片：{len(images)}  | 出错：{error_count}")

        self.progress["value"] = self.progress["maximum"]
        msg = f"批量处理完成\n{len(images)} 张图，共 {total_count} 个桃子"
        if error_count:
            msg += f"\n{error_count} 张出错（表格里标着）"
        messagebox.showinfo("批量完成", msg)
        self.set_status(f"完成：{len(images)} 张，共 {total_count} 个桃子")

    def open_result(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        tags = self.tree.item(sel[0], "tags")
        if not tags or not tags[0]:
            return
        path = tags[0]
        if os.path.exists(path):
            if sys.platform == "darwin":
                subprocess.run(["open", path])
            elif sys.platform == "win32":
                os.startfile(path)

if __name__ == "__main__":
    root = tk.Tk()
    PeachCounterApp(root)
    root.mainloop()