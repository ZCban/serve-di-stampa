import socket
import subprocess
import time

def is_connected():
    try:
        socket.create_connection(("www.google.com", 80), 2)
        return True
    except OSError:
        return False

def get_interface_status(interface_name):
    try:
        result = subprocess.run(f'netsh interface show interface "{interface_name}"', shell=True, capture_output=True, text=True)
        if "Enabled" in result.stdout:
            return "enabled"
        elif "Disabled" in result.stdout:
            return "disabled"
        else:
            return None
    except Exception as e:
        print(f"Errore durante il controllo dello stato dell'interfaccia {interface_name}: {e}")
        return None

def restart_all_adapters():
    try:
        # Esegui il comando PowerShell per riavviare tutte le schede di rete
        print("Riavvio tutte le schede di rete con PowerShell...")
        subprocess.run('powershell -Command "Get-NetAdapter | Restart-NetAdapter -Confirm:$false"', shell=True)
    except Exception as e:
        print(f"Errore durante il riavvio delle schede di rete: {e}")

def toggle_network_windows(interface_name, disable_duration=2):
    try:
        status = get_interface_status(interface_name)
        if status == "disabled":
            print(f"{interface_name} è già disabilitata. La riabilito...")
            subprocess.run(f"netsh interface set interface name=\"{interface_name}\" admin=enable", shell=True)
        elif status == "enabled":
            print(f"Disabilito {interface_name}...")
            subprocess.run(f"netsh interface set interface name=\"{interface_name}\" admin=disable", shell=True)
            time.sleep(disable_duration)
            print(f"Riabilito {interface_name}...")
            subprocess.run(f"netsh interface set interface name=\"{interface_name}\" admin=enable", shell=True)
        else:
            print(f"Impossibile ottenere lo stato di {interface_name}. Riavvio tutte le schede di rete...")
            restart_all_adapters()
    except Exception as e:
        print(f"Errore durante l'operazione su {interface_name}: {e}")

def eth_restore():
    # Uso della funzione
    if is_connected():
        print("Connesso a Internet")
    else:
        print("Non connesso a Internet. Verifico e gestisco le schede di rete...")
        toggle_network_windows("Ethernet")
        toggle_network_windows("Wi-Fi")

