#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import select
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.utils import get_color_from_hex

class VPNShareProxyApp(App):
    def build(self):
        # إعدادات البروكسي الداخلية
        self.PROXY_HOST = "0.0.0.0"
        self.PROXY_PORT = 8080
        self.is_running = False
        self.server_socket = None

        # تصميم الواجهة الرسومية للتطبيق (Layout)
        self.title = "VPN Wi-Fi Hotspot Sharer"
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # عنوان التطبيق الرئيسي
        self.status_label = Label(
            text="🔴 الخادم متوقف حالياً",
            font_size='20sp',
            color=get_color_from_hex("#FF5252"),
            bold=True
        )
        
        # نص إرشادي للمستخدم داخل الواجهة
        self.info_label = Label(
            text="قم بتشغيل الـ VPN ونقطة الاتصال أولاً، ثم اضغط تشغيل.\nالمنفذ: 8080 | البروكسي: 192.168.43.1",
            font_size='14sp',
            halign='center',
            color=get_color_from_hex("#B0BEC5")
        )

        # زر التحكم بالتشغيل والإيقاف
        self.action_btn = Button(
            text="🚀 بدء تشغيل خادم المشاركة",
            font_size='18sp',
            background_color=get_color_from_hex("#2E7D32"),
            background_normal=''
        )
        self.action_btn.bind(on_press=self.toggle_proxy)

        # إضافة العناصر إلى الواجهة
        layout.add_widget(self.status_label)
        layout.add_widget(self.info_label)
        layout.add_widget(self.action_btn)

        return layout

    def toggle_proxy(self, instance):
        if not self.is_running:
            # بدء خادم التوجيه في خيط منفصل لتجنب تجمد الواجهة
            self.is_running = True
            threading.Thread(target=self.start_server_logic, daemon=True).start()
            self.status_label.text = "🟢 الخادم يعمل الآن بنجاح!"
            self.status_label.color = get_color_from_hex("#4CAF50")
            self.action_btn.text = "🛑 إيقاف الخادم"
            self.action_btn.background_color = get_color_from_hex("#C62828")
        else:
            # إيقاف الخادم
            self.is_running = False
            if self.server_socket:
                self.server_socket.close()
            self.status_label.text = "🔴 الخادم متوقف حالياً"
            self.status_label.color = get_color_from_hex("#FF5252")
            self.action_btn.text = "🚀 بدء تشغيل خادم المشاركة"
            self.action_btn.background_color = get_color_from_hex("#2E7D32")

    def start_server_logic(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_socket.bind((self.PROXY_HOST, self.PROXY_PORT))
            self.server_socket.listen(100)
            
            while self.is_running:
                try:
                    client_sock, _ = self.server_socket.accept()
                    threading.Thread(target=self.handle_client_traffic, args=(client_sock,), daemon=True).start()
                except Exception:
                    break
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status_error(str(e)))
        finally:
            self.server_socket.close()

    def update_status_error(self, error_msg):
        self.status_label.text = f"❌ خطأ أثناء التشغيل: {error_msg}"
        self.status_label.color = get_color_from_hex("#FF1744")
        self.is_running = False

    def handle_client_traffic(self, client_socket):
        try:
            request = client_socket.recv(4096)
            if not request:
                client_socket.close()
                return

            first_line = request.decode('utf-8', errors='ignore').split('\n')[0]
            url = first_line.split(' ')[1]
            
            if "://" in url:
                url = url.split("://")[1]
            
            if ":" in url:
                target_host, target_port = url.split(":")[:2]
                target_port = int(target_port)
            else:
                target_host = url
                target_port = 80 if first_line.startswith("GET") else 443

            remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_socket.connect((target_host, target_port))

            if first_line.startswith("CONNECT"):
                client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            else:
                remote_socket.sendall(request)

            connected_sockets = [client_socket, remote_socket]
            while self.is_running:
                ready_to_read, _, _ = select.select(connected_sockets, [], [])
                if client_socket in ready_to_read:
                    data = client_socket.recv(4096)
                    if not data: break
                    remote_socket.sendall(data)
                if remote_socket in ready_to_read:
                    data = remote_socket.recv(4096)
                    if not data: break
                    client_socket.sendall(data)

        except Exception:
            pass
        finally:
            client_socket.close()

    def on_stop(self):
        # تنظيف الاتصالات البرمجية عند إغلاق التطبيق تماماً
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()

if __name__ == "__main__":
    VPNShareProxyApp().run()
