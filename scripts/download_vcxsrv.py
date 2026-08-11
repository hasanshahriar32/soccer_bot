import urllib.request
import os

url = "https://github.com/marchaesen/vcxsrv/releases/download/21.1.16.1/vcxsrv-64.21.1.16.1.installer.exe"
dest = r"C:\Users\jatin\Downloads\VcXsrv_Setup.exe"

print(f"Downloading VcXsrv installer to: {dest} ...")
try:
    urllib.request.urlretrieve(url, dest)
    size_mb = os.path.getsize(dest) / (1024 * 1024)
    print(f"[SUCCESS] Downloaded VcXsrv installer ({size_mb:.1f} MB) to {dest}!")
except Exception as e:
    print(f"[ERROR] Download failed: {e}")
