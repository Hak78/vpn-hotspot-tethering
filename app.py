#!/usr/bin/env python3
import socket
import select
import threading
import sys

# إعدادات البروكسي
HOST = "0.0.0.0"  # لكي يسمح بمرور البيانات من جميع الأجهزة المتصلة بالـ Wi-Fi
PORT = 8080       # المنفذ الذي ستتصل به الأجهزة الأخرى

def handle_client(client_socket):
    """معالجة حزم البيانات وتوجيهها بين جهازك والإنترنت (عبر الـ VPN النشط)"""
    try:
        # قراءة السطر الأول من طلب العميل لمعرفة الوجهة
        request = client_socket.recv(4096)
        if not request:
            client_socket.close()
            return

        # استخراج عنوان الموقع والمنفذ المستهدف
        first_line = request.decode('utf-8', errors='ignore').split('\n')[0]
        url = first_line.split(' ')[1]
        
        # التعامل مع طلبات HTTPS (CONNECT) أو HTTP العادية
        if "://" in url:
            url = url.split("://")[1]
        
        if ":" in url:
            target_host, target_port = url.split(":")[:2]
            target_port = int(target_port)
        else:
            target_host = url
            target_port = 80 if first_line.startswith("GET") else 443

        # إنشاء اتصال مع الموقع المستهدف (سيمر تلقائياً عبر الـ VPN المفتوح في هاتفك)
        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        remote_socket.connect((target_host, target_port))

        # إذا كان الطلب HTTPS، نرسل رد نجاح للعميل لفتح النفق المشفر
        if first_line.startswith("CONNECT"):
            client_socket.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
        else:
            remote_socket.sendall(request)

        # نقل البيانات في الاتجاهين بشكل متوازٍ ومستمر
        sockets = [client_socket, remote_socket]
        while True:
            readable, _, _ = select.select(sockets, [], [])
            if client_socket in readable:
                data = client_socket.recv(4096)
                if not data: break
                remote_socket.sendall(data)
            if remote_socket in readable:
                data = remote_socket.recv(4096)
                if not data: break
                client_socket.sendall(data)

    except Exception as e:
        pass
    finally:
        client_socket.close()

def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((HOST, PORT))
        server.listen(100)
        print("="*60)
        print("    🚀 مشروع GitHub: مشاركة الـ VPN بدون Root (HTTP Proxy)   ")
        print("="*60)
        print(f"[+] خادم المشاركة يعمل الآن بنجاح على المنفذ: {PORT}")
        print("[+] متاح لجميع الأجهزة المتصلة بنقطة اتصال جهازك الحالي.")
        print("[*] لإيقاف التطبيق اضغط: Ctrl + C")
    except Exception as e:
        print(f"[-] فشل بدء الخادم: {e}")
        sys.exit(1)

    try:
        while True:
            client_sock, addr = server.accept()
            # تشغيل خيط (Thread) منفصل لكل جهاز يتصل بالبروكسي لتفادي البطء
            threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[-] تم إيقاف خادم مشاركة الإنترنت.")
    finally:
        server.close()

if __name__ == "__main__":
    start_proxy()
