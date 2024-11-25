import socket
import os
import win32print
import win32ui
from PIL import Image, ImageWin
import time
import psutil
import subprocess


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

class FilePrinter:
    def __init__(self):
        self.printer_name = win32print.GetDefaultPrinter()  # Ottieni il nome della stampante predefinita

    def print_image(self, image_path):
        """Stampa un'immagine su un foglio A4 mantenendo le proporzioni."""
        try:
            # Apri l'immagine
            image = Image.open(image_path)

            # Crea un contesto di dispositivo per la stampante
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(self.printer_name)

            # Inizia il documento e la pagina
            hdc.StartDoc("Image Print")
            hdc.StartPage()

            # Converti l'immagine in modalità RGB se necessario
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Dimensioni del foglio A4 in pixel (risoluzione standard 300 DPI)
            a4_width = int(8.27 * 300)  # circa 2480 pixel
            a4_height = int(11.69 * 300)  # circa 3508 pixel

            # Calcola il fattore di scala per mantenere le proporzioni
            scale = min(a4_width / image.width, a4_height / image.height)
            new_size = (int(image.width * scale), int(image.height * scale))

            # Ridimensiona l'immagine per mantenere le proporzioni
            image = image.resize(new_size, Image.LANCZOS)

            # Crea un DIB (Device Independent Bitmap) dall'immagine
            dib = ImageWin.Dib(image)

            # Disegna il DIB sul contesto del dispositivo
            dst = (0, 0, new_size[0], new_size[1])
            dib.draw(hdc.GetHandleOutput(), dst)

            # Termina la pagina e il documento
            hdc.EndPage()
            hdc.EndDoc()

            # Pulizia
            hdc.DeleteDC()
            win32print.ClosePrinter(win32print.OpenPrinter(self.printer_name))

        except Exception as e:
            print(f"Errore durante la stampa dell'immagine {image_path}: {e}")

    def print_file(self, file_path):
        """Stampa un file, immagine o documento, se è supportato dal sistema."""
        try:
            # Verifica se il file è un'immagine
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                self.print_image(file_path)  # Stampa l'immagine
            else:
                os.startfile(file_path, "print")  # Per Windows, per i documenti
        except OSError as e:
            if e.winerror == 1155:  # WinError 1155: No application is associated with the specified file
                self.handle_print_error(file_path)
            else:
                print(f"Errore durante la stampa del file {os.path.basename(file_path)}: {e}")

    def handle_print_error(self, file_path):
        """Gestisce gli errori di stampa legati all'associazione del file."""
        file_extension = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)

        message = f"Nessuna applicazione installata per il formato del file: {file_name}"

        # Consigli in base al tipo di file
        if file_extension == '.pdf':
            message += ". Si consiglia di installare Adobe Acrobat."
        elif file_extension == '.py':
            message += ". Si consiglia di installare Python."
        elif file_extension in {'.dwg', '.dxf'}:
            message += ". Si consiglia di installare AutoCAD."
        elif file_extension == '.csv':
            message += ". Si consiglia di installare Microsoft Office."

        print(message)

    @staticmethod
    def is_printable_file(file_name):
        """Verifica se il file è stampabile, evitando formati audio/video."""
        non_printable_extensions = {'.mp3', '.wav', '.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flac', '.aac', '.m4a', '.ogg'}
        return not any(file_name.lower().endswith(ext) for ext in non_printable_extensions)

    @staticmethod
    def kill_process_on_port(port):
        """Termina il processo che sta usando la porta specificata."""
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in psutil.net_connections(kind='inet'):
                    if conn.laddr.port == port and proc.pid == conn.pid:
                        proc.terminate()  # Termina il processo
                        proc.wait(timeout=5)  # Attende la terminazione
                        print(f"Processo terminato sulla porta {port}: PID {proc.pid}")
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass


class PrintServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.documents_path = os.path.expanduser("~/Documents")
        self.server_print_path = os.path.join(self.documents_path, "server_stampa")
        self.printer = FilePrinter()  # Oggetto FilePrinter per gestire la stampa

        # Crea la cartella di stampa se non esiste
        if not os.path.exists(self.server_print_path):
            os.makedirs(self.server_print_path)
            print(f"Creata la cartella: {self.server_print_path}")
        else:
            print(f"La cartella esiste già: {self.server_print_path}")

    def start_server(self):
        """Avvia il server per ricevere file e stampare."""
        # Prova a chiudere qualsiasi processo che sta usando la porta
        FilePrinter.kill_process_on_port(self.port)

        # Configura il socket per il server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)
            print(f"Server in ascolto su {self.host}:{self.port}...")

            # Accetta connessioni
            conn, addr = server_socket.accept()
            with conn:
                print(f"Connessione da {addr}")

                # Invia IP e porta al client
                conn.sendall(f"{self.host}:{self.port}".encode('utf-8'))

                # Ricevi il nome del file
                file_name = conn.recv(1024).decode('utf-8')
                print(f"Ricevuto file: {file_name}")

                # Crea il percorso completo per il file salvato
                save_path = os.path.join(self.server_print_path, file_name)

                # Ricevi i dati del file e salvalo
                with open(save_path, 'wb') as file:
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        file.write(data)

                print('File ricevuto e salvato in:', save_path)

                # Verifica se il file è stampabile
                if self.printer.is_printable_file(save_path):
                    # Stampa il file
                    self.printer.print_file(save_path)
                else:
                    print("File non stampabile (audio/video). Ignorato.")

# Configurazione dell'IP statico
interface_name = "Ethernet"  # Puoi usare "Wi-Fi" o il nome della tua connessione di rete
ip_address = "192.168.1.110"  # L'indirizzo IP statico che vuoi assegnare
subnet_mask = "255.255.255.0"  # La subnet mask
gateway = "192.168.1.1"  # L'indirizzo del gateway predefinito (router)
dns = "8.8.8.8"  # L'indirizzo del server DNS (puoi usare DNS di Google)



while True:
    network_config = NetworkConfigurator(interface_name, ip_address, subnet_mask, gateway, dns)

    # Ripristina la connessione se non c'è Internet
    network_config.eth_restore()

    # Assegna l'IP statico
    network_config.set_static_ip()
    time.sleep(1)
    # Creiamo il server di stampa
    server = PrintServer(host='0.0.0.0', port=5000)
    # Avviamo il server
    server.start_server()
