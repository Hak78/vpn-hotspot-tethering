#!/usr/bin/env python3
import os
import sys
import subprocess
import time

def check_root():
    """التحقق من تشغيل السكريبت بصلاحيات المسؤول الضرورية للتحكم بالشبكة"""
    if os.geteuid() != 0:
        print("\033[91m[-] خطأ: يجب تشغيل هذا التطبيق بصلاحيات الـ Root (استخدم sudo).\033[0m")
        sys.exit(1)

def enable_ip_forwarding():
    """تفعيل تمرير حزم البيانات داخل نواة النظام"""
    print("[+] جاري تفعيل IP Forwarding...")
    try:
        subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        print(f"[-] فشل تفعيل IP Forwarding: {e}")
        sys.exit(1)

def setup_routing(wifi_interface, vpn_interface):
    """إعداد جدار الحماية (iptables) لتوجيه حركة مرور الـ Wi-Fi عبر نفق الـ VPN"""
    print(f"[+] جاري إعداد قواعد التوجيه: {wifi_interface} ===> {vpn_interface}")
    try:
        # تنظيف الجداول السابقة لتفادي التضارب
        subprocess.run(["iptables", "-F"], check=True)
        subprocess.run(["iptables", "-t", "nat", "-F"], check=True)
        
        # السماح بتمرير البيانات من الوايرلس إلى الـ VPN
        subprocess.run(["iptables", "-A", "FORWARD", "-i", wifi_interface, "-o", vpn_interface, "-j", "ACCEPT"], check=True)
        
        # السماح بالبيانات العائدة (المستقرة والمرتبطة)
        subprocess.run(["iptables", "-A", "FORWARD", "-i", vpn_interface, "-o", wifi_interface, "-m", "state", "--state", "ESTABLISHED,RELATED", "-j", "ACCEPT"], check=True)
        
        # تفعيل تقنية الـ NAT (Masquerade) على واجهة الـ VPN
        subprocess.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", vpn_interface, "-j", "MASQUERADE"], check=True)
        print("\033[92m[+] تم إعداد جدار الحماية بنجاح.\033[0m")
    except subprocess.CalledProcessError as e:
        print(f"[-] خطأ أثناء إعداد iptables: {e}")
        sys.exit(1)

def start_hotspot(interface, ssid, password):
    """إنشاء وبث شبكة الـ Wi-Fi باستخدام NetworkManager"""
    print(f"[+] جاري إنشاء نقطة البث اللاسلكي باسم (SSID): {ssid}...")
    try:
        # حذف أي إعداد قديم لنفس النقطة تجنباً للتكرار
        subprocess.run(["nmcli", "connection", "delete", "GitHub_VPN_Hotspot"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        
        # أمر إنشاء شبكة الوايرلس وبثها فوراً
        subprocess.run([
            "nmcli", "device", "wifi", "hotspot", 
            "ifname", interface, 
            "ssid", ssid, 
            "password", password, 
            "name", "GitHub_VPN_Hotspot"
        ], check=True, stdout=subprocess.DEVNULL)
        
        print("\033[92m[+] نقطة اتصال الـ Wi-Fi تعمل الآن ونشطة!\033[0m")
    except subprocess.CalledProcessError:
        print("\033[91m[-] فشل إنشاء نقطة البث. تأكد من أن كرت الشبكة يدعم وضع الـ AP (Access Point) وأن خدمة NetworkManager تعمل.\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    check_root()
    
    print("="*60)
    print("      تطبيق مشاركة إنترنت الـ VPN عبر الـ Wi-Fi (GitHub Project)      ")
    print("="*60)
    
    # --- إعدادات الشبكة (يمكن للمستخدم تعديلها هنا) ---
    WIFI_INTERFACE = "wlan0"       # اسم كرت الوايرلس (تأكد منه عبر أمر ip link)
    VPN_INTERFACE = "tun0"         # اسم كرت الـ VPN (غالباً tun0 أو wg0)
    WIFI_SSID = "VPN_Shared_WiFi"  # اسم شبكة الواي فاي التي ستظهر للأجهزة الأخرى
    WIFI_PASSWORD = "SharedPassword123" # كلمة المرور (8 خانات أو أكثر)
    # --------------------------------------------------

    try:
        enable_ip_forwarding()
        setup_routing(WIFI_INTERFACE, VPN_INTERFACE)
        start_hotspot(WIFI_INTERFACE, WIFI_SSID, WIFI_PASSWORD)
        
        print("\n\033[94m[*] التطبيق يعمل بكفاءة. اتصل الآن بالشبكة واستمتع بالـ VPN المجاني!\033[0m")
        print("[*] للخروج وإيقاف البث، اضغط على: Ctrl + C")
        
        # الحفاظ على السكريبت حياً
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n[-] يتم الآن إيقاف التطبيق وإعادة إعدادات النظام الافتراضية...")
        # تنظيف اختياري: إيقاف تمرير الحزم لحماية النظام بعد القفل
        subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=0"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["nmcli", "connection", "down", "GitHub_VPN_Hotspot"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] تم الإغلاق بنجاح. شكراً لك!")
