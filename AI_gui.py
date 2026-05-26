"""
DeepSeek 聊天助手 - Tkinter 版
一个简洁美观的 AI 对话桌面应用
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
from openai import OpenAI
import os

# ==================== 配置区域 ====================
API_KEY = "API key"  # 在这里填入你的 DeepSeek API Key
# =================================================


class DeepSeekApp:
    """主应用类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek · 智能助手")
        self.root.geometry("620x720")
        self.root.minsize(500, 600)
        self.root.configure(bg='#f5f7fa')
        
        # 初始化 API 客户端
        self.client = OpenAI(
            api_key=API_KEY,
            base_url="https://api.deepseek.com"
        )
        
        # 对话记忆
        self.messages = [
            {"role": "system", "content": "你是 DeepSeek，一个友好的智能助手。"}
        ]
        
        # 构建界面
        self._build_ui()
        
        # 绑定快捷键
        self.input_text.bind('<Return>', lambda e: self.send())
        
        # 显示欢迎语
        self._show_welcome()
    
    # ==================== 界面构建 ====================
    
    def _build_ui(self):
        """搭建所有界面组件"""
        # 顶部栏
        header = tk.Frame(self.root, bg='#2c3e50', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="🤖 DeepSeek", font=('微软雅黑', 20, 'bold'),
                 fg='white', bg='#2c3e50').pack(expand=True)
        tk.Label(header, text="深度思考 · 智能对话", font=('微软雅黑', 10),
                 fg='#bdc3c7', bg='#2c3e50').pack()
        
        # 聊天区域
        self.chat_area = scrolledtext.ScrolledText(
            self.root, wrap='word', font=('微软雅黑', 11),
            bg='white', fg='#2c3e50', padx=15, pady=12,
            state='disabled', relief='flat'
        )
        self.chat_area.pack(padx=15, pady=(15, 10), fill='both', expand=True)
        
        # 配置消息样式
        self.chat_area.tag_config('user', foreground='#3498db', font=('微软雅黑', 11, 'bold'))
        self.chat_area.tag_config('ai', foreground='#27ae60', font=('微软雅黑', 11))
        self.chat_area.tag_config('system', foreground='#e67e22', font=('微软雅黑', 10, 'italic'))
        
        # 底部输入区
        bottom = tk.Frame(self.root, bg='#f5f7fa')
        bottom.pack(padx=15, pady=(0, 15), fill='x')
        
        self.input_text = tk.Text(bottom, height=4, font=('微软雅黑', 11),
                                   wrap='word', padx=12, pady=10,
                                   relief='groove', borderwidth=1)
        self.input_text.pack(fill='x', pady=(0, 10))
        
        # 按钮栏
        btn_frame = tk.Frame(bottom, bg='#f5f7fa')
        btn_frame.pack(fill='x')
        
        tk.Button(btn_frame, text="📤 发送", command=self.send,
                  bg='#3498db', fg='white', font=('微软雅黑', 10, 'bold'),
                  padx=20, pady=6, relief='flat', cursor='hand2').pack(side='right', padx=(10, 0))
        
        tk.Button(btn_frame, text="🗑 清空", command=self.clear,
                  bg='#95a5a6', fg='white', font=('微软雅黑', 10),
                  padx=20, pady=6, relief='flat', cursor='hand2').pack(side='right')
        
        # 状态栏
        self.status = tk.Label(self.root, text="✅ 就绪", font=('微软雅黑', 9),
                               bg='#ecf0f1', fg='#7f8c8d', anchor='w', padx=15)
        self.status.pack(fill='x', side='bottom')
    
    def _show_welcome(self):
        """欢迎消息"""
        welcome = "✨ 欢迎使用 DeepSeek 智能助手！\n\n💡 提示：\n• 支持多轮对话，AI 会记住上下文\n• 按回车键快速发送\n\n开始聊天吧～"
        self._append_message(welcome, 'system')
    
    def _append_message(self, text, role):
        """在聊天框显示消息"""
        self.chat_area.config(state='normal')
        prefix = "👤 你：" if role == 'user' else "🤖 DeepSeek：" if role == 'ai' else "💡 提示："
        tag = 'user' if role == 'user' else 'ai' if role == 'ai' else 'system'
        
        self.chat_area.insert('end', f"{prefix}\n", tag)
        self.chat_area.insert('end', f"{text}\n\n")
        self.chat_area.see('end')
        self.chat_area.config(state='disabled')
    
    # ==================== 核心功能 ====================
    
    def send(self):
        """发送消息"""
        user_input = self.input_text.get('1.0', 'end-1c').strip()
        if not user_input:
            return
        
        # 显示用户消息
        self._append_message(user_input, 'user')
        self.input_text.delete('1.0', 'end')
        self.status.config(text="⏳ AI 思考中...")
        self.send_btn.config(state='disabled')
        
        # 保存到记忆
        self.messages.append({"role": "user", "content": user_input})
        
        # 开线程请求 API（避免界面卡死）
        threading.Thread(target=self._get_ai_reply, daemon=True).start()
    
    def _get_ai_reply(self):
        """调用 DeepSeek API"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",  # 或 deepseek-v4-pro
                messages=self.messages,
                stream=False
            )
            reply = response.choices[0].message.content
            
            # 更新界面（需在主线程）
            self.root.after(0, lambda: self._on_reply(reply))
            
        except Exception as e:
            self.root.after(0, lambda: self._on_error(str(e)))
    
    def _on_reply(self, reply):
        """收到回复后的处理"""
        self._append_message(reply, 'ai')
        self.messages.append({"role": "assistant", "content": reply})
        self.status.config(text="✅ 就绪")
        self.send_btn.config(state='normal')
    
    def _on_error(self, error):
        """错误处理"""
        self._append_message(f"出错了：{error}\n请检查 API Key 或网络。", 'system')
        self.status.config(text="❌ 出错")
        self.send_btn.config(state='normal')
    
    def clear(self):
        """清空对话"""
        if messagebox.askyesno("确认", "清空所有对话记录？"):
            self.messages = [{"role": "system", "content": "你是 DeepSeek，一个友好的智能助手。"}]
            self.chat_area.config(state='normal')
            self.chat_area.delete('1.0', 'end')
            self.chat_area.config(state='disabled')
            self._show_welcome()
            self.status.config(text="✅ 已清空")
    
    @property
    def send_btn(self):
        return self.root.nametowidget(self.root.children['!frame3'].children['!frame'].children['!button'])


# ==================== 启动程序 ====================
if __name__ == "__main__":
    root = tk.Tk()
    app = DeepSeekApp(root)
    root.mainloop()