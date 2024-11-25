import subprocess
import socket
import time

class NetworkConfigurator:
    def __init__(self, interface, ip_address, subnet_mask, gateway, dns):
        self.interface = interface
        self.ip_address = ip_address
        self.subnet_mask = subnet_mask
        self.gateway = gateway
        self.dns = dns

    # Funzione per ottenere la configurazione attuale dell'interfaccia
    def get_current_ip_config(self):
        try:
            # Usa 'netsh' per ottenere la configurazione attuale dell'interfaccia
            result = subprocess.run(
                ['netsh', 'interface', 'ipv4', 'show', 'config', f'name={self.interface}'], 
                stdout=subprocess.PIPE, text=True, check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Errore durante l'ottenimento della configurazione attuale: {e}")
            return ""

    # Funzione per verificare se la configurazione corrente è già quella desiderata
    def is_ip_config_same(self, current_config):
        return (self.ip_address in current_config and 
                self.subnet_mask in current_config and 
                self.gateway in current_config and 
                self.dns in current_config)

    # Funzione per impostare l'indirizzo IP statico
    def set_static_ip(self):
        current_config = self.get_current_ip_config()
        
        # Controlla se la configurazione attuale corrisponde a quella desiderata
        if self.is_ip_config_same(current_config):
            print(f"La configurazione IP per {self.interface} è già impostata correttamente. Nessuna modifica necessaria.")
            return
        
        try:
            # Imposta l'indirizzo IP statico
            subprocess.run(
                [
                    'netsh', 'interface', 'ipv4', 'set', 'address', 
                    f'name={self.interface}', 
                    'source=static', 
                    f'addr={self.ip_address}', 
                    f'mask={self.subnet_mask}', 
                    f'gateway={self.gateway}'
                ], 
                check=True
            )
            
            # Imposta il DNS statico
            subprocess.run(
                [
                    'netsh', 'interface', 'ipv4', 'set', 'dns', 
                    f'name={self.interface}', 
                    f'source=static', 
                    f'addr={self.dns}', 
                    'register=primary'
                ], 
                check=True
            )

            print(f"Indirizzo IP statico {self.ip_address} assegnato con successo a {self.interface}")
            
        except subprocess.CalledProcessError as e:
            print(f"Errore durante l'assegnazione dell'IP statico: {e}")

    # Funzione per verificare se c'è una connessione a Internet
    def is_connected(self):
        try:
            socket.create_connection(("www.google.com", 80), 2)
            return True
        except OSError:
            return False

    # Funzione per ottenere lo stato dell'interfaccia di rete
    def get_interface_status(self):
        try:
            result = subprocess.run(f'netsh interface show interface "{self.interface}"', shell=True, capture_output=True, text=True)
            if "Enabled" in result.stdout:
                return "enabled"
            elif "Disabled" in result.stdout:
                return "disabled"
            else:
                return None
        except Exception as e:
            print(f"Errore durante il controllo dello stato dell'interfaccia {self.interface}: {e}")
            return None

    # Funzione per riavviare tutte le schede di rete
    def restart_all_adapters(self):
        try:
            print("Riavvio tutte le schede di rete con PowerShell...")
            subprocess.run('powershell -Command "Get-NetAdapter | Restart-NetAdapter -Confirm:$false"', shell=True)
        except Exception as e:
            print(f"Errore durante il riavvio delle schede di rete: {e}")

    # Funzione per disabilitare e riabilitare una scheda di rete specifica
    def toggle_network_windows(self, disable_duration=2):
        try:
            status = self.get_interface_status()
            if status == "disabled":
                print(f"{self.interface} è già disabilitata. La riabilito...")
                subprocess.run(f"netsh interface set interface name=\"{self.interface}\" admin=enable", shell=True)
            elif status == "enabled":
                print(f"Disabilito {self.interface}...")
                subprocess.run(f"netsh interface set interface name=\"{self.interface}\" admin=disable", shell=True)
                time.sleep(disable_duration)
                print(f"Riabilito {self.interface}...")
                subprocess.run(f"netsh interface set interface name=\"{self.interface}\" admin=enable", shell=True)
            else:
                print(f"Impossibile ottenere lo stato di {self.interface}. Riavvio tutte le schede di rete...")
                self.restart_all_adapters()
        except Exception as e:
            print(f"Errore durante l'operazione su {self.interface}: {e}")

    # Funzione per verificare e gestire la connessione Ethernet e Wi-Fi
    def eth_restore(self):
        if self.is_connected():
            print("Connesso a Internet")
        else:
            print("Non connesso a Internet. Verifico e gestisco le schede di rete...")
            self.toggle_network_windows()
            self.toggle_network_windows()

# Esempio di utilizzo della classe
if __name__ == "__main__":
    # Configurazione dell'IP statico
    interface_name = "Ethernet"  # Puoi usare "Wi-Fi" o il nome della tua connessione di rete
    ip_address = "192.168.1.110"  # L'indirizzo IP statico che vuoi assegnare
    subnet_mask = "255.255.255.0"  # La subnet mask
    gateway = "192.168.1.1"  # L'indirizzo del gateway predefinito (router)
    dns = "8.8.8.8"  # L'indirizzo del server DNS (puoi usare DNS di Google)

    network_config = NetworkConfigurator(interface_name, ip_address, subnet_mask, gateway, dns)

    # Ripristina la connessione se non c'è Internet
    network_config.eth_restore()

    # Assegna l'IP statico
    network_config.set_static_ip()

    

