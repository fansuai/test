import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import os
import threading

# =============== 你 APP 的信息（已经适配你的验证网址）===============
REDIRECT_URI = "https://fansuai.github.io/test/"
SCOPE = "user.info.basic,video.publish"
PRIVACY_LEVEL = "PRIVATE_TO_ME"  # 审核通过改成 PUBLIC_TO_EVERYONE
# ==================================================================

def get_auth_url(client_key):
    return f"https://www.tiktok.com/v2/auth/authorize?client_key={client_key}&scope={SCOPE}&response_type=code&redirect_uri={REDIRECT_URI}"

def get_token(client_key, client_secret, code):
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }
    resp = requests.post(url, data=data)
    return resp.json()

def upload_single_video(access_token, path, title, log_box):
    try:
        log_box.insert(tk.END, f"正在发布：{os.path.basename(path)}\n")
        log_box.see(tk.END)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "post_info": {
                "title": title,
                "privacy_level": PRIVACY_LEVEL,
                "disable_comment": False
            },
            "source": "FILE_UPLOAD"
        }

        init_resp = requests.post("https://open.tiktokapis.com/v2/post/publish/video/init/", headers=headers, json=payload)
        data = init_resp.json()

        if "data" not in data:
            log_box.insert(tk.END, f"失败：{data}\n")
            return

        upload_url = data["data"]["upload_url"]
        publish_id = data["data"]["publish_id"]

        with open(path, "rb") as f:
            requests.put(upload_url, data=f)

        status_resp = requests.post("https://open.tiktokapis.com/v2/post/publish/status/fetch/", headers=headers, json={"publish_id": publish_id})
        log_box.insert(tk.END, f"完成：{status_resp.json()}\n\n")
        log_box.see(tk.END)
    except Exception as e:
        log_box.insert(tk.END, f"异常：{str(e)}\n")

def start_batch():
    client_key = entry_key.get()
    client_secret = entry_secret.get()
    code = entry_code.get()
    folder = entry_folder.get()

    if not all([client_key, client_secret, code, folder]):
        messagebox.showwarning("提示", "请填完所有信息")
        return

    def run():
        token_resp = get_token(client_key, client_secret, code)
        if "access_token" not in token_resp:
            messagebox.showerror("错误", f"获取Token失败：{token_resp}")
            return

        access_token = token_resp["access_token"]
        videos = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(('.mp4', '.mov'))]

        for i, video in enumerate(videos):
            upload_single_video(access_token, video, f"批量发布 {i+1}", log_box)

        messagebox.showinfo("完成", "全部视频发布完毕！")

    threading.Thread(target=run, daemon=True).start()

# ==================== GUI 界面 ====================
root = tk.Tk()
root.title("TikTok 批量发布工具 GUI")
root.geometry("650x550")

frame = ttk.Frame(root, padding=15)
frame.pack(fill=tk.BOTH, expand=True)

ttk.Label(frame, text="Client Key").grid(row=0, column=0, sticky="w")
entry_key = ttk.Entry(frame, width=50)
entry_key.grid(row=0, column=1, pady=5)

ttk.Label(frame, text="Client Secret").grid(row=1, column=0, sticky="w")
entry_secret = ttk.Entry(frame, width=50)
entry_secret.grid(row=1, column=1, pady=5)

ttk.Label(frame, text="授权 Code").grid(row=2, column=0, sticky="w")
entry_code = ttk.Entry(frame, width=50)
entry_code.grid(row=2, column=1, pady=5)

def open_auth():
    key = entry_key.get()
    if not key:
        messagebox.showwarning("提示", "先填 Client Key")
        return
    url = get_auth_url(key)
    os.startfile(url)

ttk.Button(frame, text="1. 打开授权链接", command=open_auth).grid(row=3, column=0, pady=5)

def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        entry_folder.delete(0, tk.END)
        entry_folder.insert(0, folder)

ttk.Button(frame, text="2. 选择视频文件夹", command=select_folder).grid(row=3, column=1, pady=5)

entry_folder = ttk.Entry(frame, width=50)
entry_folder.grid(row=4, column=1, pady=5)

ttk.Button(frame, text="3. 开始批量发布", command=start_batch).grid(row=5, column=1, pady=10)

log_box = tk.Listbox(frame, height=15, width=70)
log_box.grid(row=6, column=0, columnspan=2, pady=10)

root.mainloop()
