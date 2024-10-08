import socket
import os
import win32print
import win32ui
from PIL import Image, ImageWin
from internet_check import eth_restore
import time

def print_image(image_path):
    # Apri l'immagine
    image = Image.open(image_path)

    # Ottieni il nome della stampante predefinita
    printer_name = win32print.GetDefaultPrinter()

    # Crea un contesto di dispositivo per la stampante
    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(printer_name)

    # Inizia il documento e la pagina
    hdc.StartDoc("Image Print")
    hdc.StartPage()

    # Converti l'immagine in modalità RGB se non è già in quella modalità
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Dimensioni del foglio A4 in pixel (con risoluzione standard 300 DPI)
    a4_width = int(8.27 * 300)  # circa 2480 pixel
    a4_height = int(11.69 * 300)  # circa 3508 pixel

    # Calcola il fattore di scala per mantenere le proporzioni
    scale = min(a4_width / image.width, a4_height / image.height)
    new_size = (int(image.width * scale), int(image.height * scale))

    # Ridimensiona l'immagine per mantenere le proporzioni
    image = image.resize(new_size, Image.LANCZOS)  # Usa Image.LANCZOS per la qualità

    # Crea un DIB (Device Independent Bitmap) dall'immagine
    dib = ImageWin.Dib(image)

    # Disegna il DIB sul contesto del dispositivo
    # Specifica il rettangolo di destinazione (sinistra, sopra, destra, sotto)
    dst = (0, 0, image.width, image.height)  # Usa le dimensioni dell'immagine ridimensionata
    dib.draw(hdc.GetHandleOutput(), dst)

    # Termina la pagina e il documento
    hdc.EndPage()
    hdc.EndDoc()

    # Pulizia
    hdc.DeleteDC()
    win32print.ClosePrinter(win32print.OpenPrinter(printer_name))

def print_file(file_path):
    try:
        # Verifica se il file è un'immagine
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            print_image(file_path)  # Stampa l'immagine
        else:
            os.startfile(file_path, "print")  # Per Windows, per i documenti
    except OSError as e:
        if e.winerror == 1155:  # WinError 1155: No application is associated with the specified file
            file_extension = os.path.splitext(file_path)[1].lower()  # Ottieni l'estensione del file
            file_name = os.path.basename(file_path)

            # Messaggio di errore di default
            message = f"Nessuna applicazione installata per il formato del file ricevuto: {file_name}"

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
        else:
            # Gestisci eventuali altri errori
            print(f"Errore durante la stampa del file {os.path.basename(file_path)}: {e}")



def is_printable_file(file_name):
    # Elenco delle estensioni dei file audio e video da evitare
    non_printable_extensions = {'.mp3', '.wav', '.mp4', '.avi', '.mov', '.wmv', '.mkv', '.flac', '.aac', '.m4a', '.ogg'}
    # Controlla se l'estensione del file è in quell'elenco
    return not any(file_name.lower().endswith(ext) for ext in non_printable_extensions)

def start_server(host='0.0.0.0', port=5000):
    # Percorso della cartella "server_stampa" nella directory "Documents"
    documents_path = os.path.expanduser("~/Documents")
    server_print_path = os.path.join(documents_path, "server_stampa")

    # Crea la cartella solo se non esiste
    if not os.path.exists(server_print_path):
        os.makedirs(server_print_path)
        print(f"Creata la cartella: {server_print_path}")
    else:
        print(f"La cartella esiste già: {server_print_path}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"Server in ascolto su {host}:{port}...")

        conn, addr = server_socket.accept()
        with conn:
            print(f"Connessione da {addr}")
            # Invia IP e porta al client
            conn.sendall(f"{host}:{port}".encode('utf-8'))

            # Ricevi il nome del file
            file_name = conn.recv(1024).decode('utf-8')
            print(f"Ricevuto file: {file_name}")

            # Creare il percorso completo per il file da salvare
            save_path = os.path.join(server_print_path, file_name)

            # Ricevi i dati del file e salvalo
            with open(save_path, 'wb') as file:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    file.write(data)

            print('File ricevuto e salvato in:', save_path)

            # Controlla se il file è stampabile
            if is_printable_file(save_path):
                # Stampa il file
                print_file(save_path)
            else:
                print("File non stampabile (audio/video). Ignorato.")

while True:
    eth_restore()
    time.sleep(2)
    start_server()  # Avvia il server
