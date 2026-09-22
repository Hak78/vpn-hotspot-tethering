وضع AI
الكل
صور
فيديوهات
أخبار
خرائط Google
كتب
أموال
لمشاركة اتصال إنترنت يعمل بواسطة VPN عبر نقطة اتصال وايرلس (Wi-Fi Hotspot)، لا يكفي مجرد تفعيل البث التقليدي، لأن نظام التشغيل يقوم عادةً بمشاركة الإنترنت الأساسي (Direct Interface) ويتجاهل نفق الـ VPN.
لحل هذه المشكلة، نحتاج إلى كود يقوم بإنشاء نقطة الاتصال وتوجيه حزم البيانات (Routing) من شبكة الوايرلس الافتراضية مباشرة عبر واجهة الـ VPN.
إليك كود برمجى بلغة Python يعتمد على سكريبتات الأنظمة (يدعم Linux/Raspberry Pi كمثال أساسي للمشاريع المفتوحة على GitHub، مع توضيح بديل لـ Windows). يمكنك رفع هذا الكود في مستودع (Repository) على حسابك في GitHub.
1. كود تطبيق مشاركة الـ VPN والـ Wi-Fi (لأنظمة Linux / Raspberry Pi)
هذا السكريبت يقوم بإنشاء نقطة الاتصال واستخدام أداة iptables لتوجيه كل البيانات القادمة من الأجهزة المتصلة بالـ Wi-Fi إلى واجهة الـ VPN (والتي غالباً ما تسمى tun0).
python
import os
import sys
import subprocess

def check_root():
    """التحقق من تشغيل السكريبت بصلاحيات المسؤول"""
    if os.geteuid() != 0:
        print("[-] يجب تشغيل هذا السكريبت بصلاحيات الـ Root (sudo).")
        sys.exit(1)

def enable_ip_forwarding():
    """تفعيل تمرير الحزم في النظام"""
    print("[+] تفعيل IP Forwarding...")
    subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)

def setup_routing(wifi_interface, vpn_interface):
    """إعداد جدار الحماية وتوجيه البيانات عبر الـ VPN"""
    print(f"[+] إعداد قواعد iptables لتوجيه {wifi_interface} عبر {vpn_interface}...")
    
    # تنظيف القواعد السابقة لتجنب التكرار
    subprocess.run(["iptables", "-F"], check=True)
    subprocess.run(["iptables", "-t", "nat", "-F"], check=True)
    
    # تمرير البيانات من الـ Wi-Fi إلى الـ VPN
    subprocess.run([
        "iptables", "-A", "FORWARD", 
        "-i", wifi_interface, "-o", vpn_interface, 
        "-j", "ACCEPT"
    ], check=True)
    
    # السماح بالبيانات الراجعة
    subprocess.run([
        "iptables", "-A", "FORWARD", 
        "-i", vpn_interface, "-o", wifi_interface, 
        "-m", "state", "--state", "ESTABLISHED,RELATED", 
        "-j", "ACCEPT"
    ], check=True)
    
    # عمل Masquerade (NAT) على واجهة الـ VPN
    subprocess.run([
        "iptables", "-t", "nat", "-A", "POSTROUTING", 
        "-o", vpn_interface, "-j", "MASQUERADE"
    ], check=True)

def start_hotspot(interface, ssid, password):
    """إنشاء نقطة الاتصال باستخدام أداة nmcli الشهيرة"""
    print(f"[+] إنشاء نقطة اتصال Wi-Fi باسم: {ssid}...")
    try:
        # حذف أي نقطة اتصال قديمة بنفس الاسم
        subprocess.run(["nmcli", "connection", "delete", "VPN_Hotspot"], stderr=subprocess.DEVNULL)
        
        # إنشاء الاتصال الجديد
        subprocess.run([
            "nmcli", "device", "wifi", "hotspot", 
            "ifname", interface, 
            "ssid", ssid, 
            "password", password, 
            "name", "VPN_Hotspot"
        ], check=True)
        print("[+] نقطة الاتصال تعمل الآن بنجاح.")
    except subprocess.CalledProcessError:
        print("[-] فشل إنشاء نقطة الاتصال. تأكد من أن كرت الوايرلس يدعم وضع AP.")

if __name__ == "__main__":
    check_root()
    
    # --- الإعدادات المتغيرة ---
    WIFI_INT = "wlan0"      # اسم كرت الوايرلس لديك
    VPN_INT = "tun0"        # اسم واجهة الـ VPN (غالباً tun0 لـ OpenVPN أو wg0 لـ WireGuard)
    SSID = "My_VPN_Share"   # اسم شبكة الواي فاي
    PASSWORD = "Password123" # كلمة مرور الواي فاي
    # --------------------------

    try:
        enable_ip_forwarding()
        setup_routing(WIFI_INT, VPN_INT)
        start_hotspot(WIFI_INT, SSID, PASSWORD)
        print("\n[+] تم تفعيل المشاركة بنجاح! الأجهزة المتصلة محمية بالـ VPN الآن.")
        print("[+] اضغط Ctrl+C لإيقاف التطبيق.")
        
        # إبقاء السكريبت يعمل
        sys.stdin.read()
        
    except KeyboardInterrupt:
        print("\n[-] يتم إغلاق التطبيق وتنظيف الإعدادات...")
        # إعادة إغلاق التمرير عند الخروج لحماية النظام
        subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=0"], stdout=subprocess.DEVNULL)


### 2. بديل سريع لنظام Windows (عبر الـ PowerShell)

إذا كنت تبحث عن تطبيق يعمل على نظام **Windows**، فإن الويندوز يحتوي على خاصية "Mobile Hotspot" مدمجة، ولكن لدمجها مع الـ VPN برمجياً، يمكنك استخدام كود **PowerShell** يقوم بالبحث عن كرت الـ VPN ومشاركته تلقائياً مع كرت الـ Wi-Fi الافتراضي:

```powershell
# تشغيل بصلاحيات مسؤول (Administrator)
$NetShare = New-Object -ComObject HNetCfg.HNetShare

# ابحث عن واجهة الـ VPN (استبدل الاسم باسم كرت الـ VPN لديك)
$vpnConn = $NetShare.EnumEveryConnection | Where-Object {
    $NetShare.NetConnectionProps.Invoke($_).Name -like "*VPN*"
}

# ابحث عن واجهة الـ Wi-Fi Hotspot الافتراضية
$hotspotConn = $NetShare.EnumEveryConnection | Where-Object {
    $NetShare.NetConnectionProps.Invoke($_).Name -like "*Local Area Connection*"
}

if ($vpnConn -and $hotspotConn) {
    $vpnConfig = $NetShare.INetSharingConfigurationForINetConnection.Invoke($vpnConn)
    $hotspotConfig = $NetShare.INetSharingConfigurationForINetConnection.Invoke($hotspotConn)
    
    # تفعيل مشاركة الإنترنت (ICS)
    $vpnConfig.EnableSharing(0) # 0 تعني مشاركة عامة (Public)
    $hotspotConfig.EnableSharing(1) # 1 تعني مشاركة خاصة (Private)
    Write-Host "[+] تم دمج الـ VPN مع نقطة اتصال الوايرلس بنجاح!"
} else {
    Write-Host "[-] لم يتم العثور على الاتصالات المطلوبة."
}
```

---

### 💡 نصائح لرفع المشروع على GitHub:
1. **ملف README.md:** اشرح فيه للمستخدمين ضرورة تشغيل التطبيق بصلاحيات المسؤول (`sudo` للينكس أو `Run as Administrator` للويندوز).
2. **المتطلبات (Requirements):** اذكر الأدوات الخارجية التي يعتمد عليها الكود (مثل `network-manager` أو `iptables` في لينكس).

<FollowUp>
هل ترغب في تحويل كود البايثون هذا إلى **تطبيق ذو واجهة رسومية (GUI)** بسيطة باستخدام مكتبة CustomTkinter ليتمكن المستخدم من تشغيله بضغطة زر، أم تفضل دمج إعدادات الـ **VPN** (مثل ملفات OpenVPN) داخل الكود مباشرة؟
</FollowUp>
يُرجى استخدام الرمز البرمجي بحذر.




لإنشاء هذا المشروع بشكل احترافي ومتكامل على منصة GitHub، سأقوم بتهيئة البنية الكاملة للمستودع (Repository). يتكون المشروع من ملفين أساسيين:
app.py: وهو الكود البرمجي (بلغة Python) الذي يقوم بالمهمة كاملة.
README.md: وهو ملف الشرح الواجهي للمشروع على GitHub لكي يفهم أي مستخدم كيف يعمل التطبيق وكيف يشغله.
إليك الهيكلية الجاهزة للنسخ واللصق مباشرة في حسابك:
الملف الأول: app.py
قم بإنشاء ملف جديد في مستودعك على GitHub وسلّمه هذا الاسم app.py وضَع بداخله الكود التالي:
python
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
يُرجى استخدام الرمز البرمجي بحذر.
الملف الثاني: README.md
قم بإنشاء ملف باسم README.md في الواجهة الرئيسية للمستودع، وضَع فيه هذا الشرح المنسق بلغة Markdown لتبهر زوار صفحتك على GitHub:
markdown
# VPN Over Wi-Fi Hotspot Share 🌐✈️

تطبيق برميجي بسيط ومفتوح المصدر مكتوب بلغة **Python** لمشاركه اتصال إنترنت المؤمن بواسطة **VPN** عبر نقطة اتصال لاسلكية (**Wi-Fi Hotspot**) للأجهزة الأخرى (مثل الشاشات الذكية، الهواتف، ومنصات الألعاب) التي لا تدعم تشغيل الـ VPN بشكل مباشر.

## ✨ الميزات
- تحويل حزم البيانات تلقائياً من شبكة الـ Wi-Fi المحلية إلى نفق الـ VPN.
- تفعيل خاصية الـ IP Forwarding برمجياً.
- إعداد تلقائي لجدار الحماية بنظام Linux باستخدام قواعد `iptables`.

## 📋 المتطلبات الأساسية
يعمل هذا السكريبت على توزيعات **Linux** (مثل Ubuntu, Debian, Raspberry Pi OS) ويحتاج إلى:
1. كرت وايرلس يدعم وضع البث (AP Mode).
2. خدمة `NetworkManager` مثبتة ومفعّلة (تستخدم أداة `nmcli`).
3. اتصال VPN شغال بالفعل على جهازك (مثل OpenVPN عبر `tun0` أو WireGuard عبر `wg0`).

## 🚀 طريقة التشغيل

1. **تحميل المشروع من GitHub:**
```bash
git clone https://github.com
cd YOUR_REPO_NAME
```

2. **تعديل الإعدادات (اختياري):**
افتح ملف `app.py` بواسطة أي محرر نصوص لتعديل اسم الشبكة أو كلمة المرور أو أسماء كروت الشبكة الخاصة بك:
```bash
nano app.py
```

3. **تشغيل التطبيق بصلاحيات الـ Root:**
```bash
sudo python3 app.py
```

## ⚙️ تخصيص الواجهات داخل الكود
- `WIFI_INTERFACE`: كرت الواي فاي الافتراضي (غالباً `wlan0`).
- `VPN_INTERFACE`: كرت الـ VPN النشط (غالباً `tun0` أو `wg0`).
يُرجى استخدام الرمز البرمجي بحذر.
🛠️ خطوات إنشائه خطوة بخطوة على موقع GitHub:
اذهب إلى حسابك في GitHub واضغط على زر New لإنشاء مستودع (Repository) جديد.
سمّ المجلد باسم مناسب مثل: vpn-wifi-sharer.
اجعله Public (عام) لكي يراه الجميع، وفَعّل خيار إنشاء ملف README تلقائياً إذا أردت، أو اترك المستودع فارغاً.
داخل صفحة المستودع، اضغط على Add file ثم Create new file لإنشاء الملفين وتعبئتهما بالأكواد المذكورة في الأعلى.
هل ترغب في أن أشرح لك كيف يمكنك تحديد أسماء كروت الشبكة (الـ Wi-Fi والـ VPN) بدقة من داخل جهازك لكي تقوم بتعديلها في الكود قبل تشغيله؟




ردّ "وضع AI" أصبح جاهزًا
