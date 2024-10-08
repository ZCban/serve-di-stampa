import socket
import tkinter as tk
from tkinter import filedialog
from internet_check import eth_restore
import time

def choose_file():
    root = tk.Tk()
    root.withdraw()  # Nascondi la finestra principale
    file_path = filedialog.askopenfilename()  # Apri il dialogo di selezione file
    if file_path:  # Se l'utente ha selezionato un file
        send_file(file_path)

def send_file(file_path, server_ip='192.168.1.105', server_port=5000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            # Connessione al server sulla porta predefinita
            client_socket.connect((server_ip, server_port))

            # Ricevi IP e porta dal server
            server_info = client_socket.recv(1024).decode('utf-8')
            server_ip, server_port = server_info.split(':')
            print(f"Connessione stabilita con il server: {server_ip}:{server_port}")

            # Invia il nome del file
            file_name = file_path.split('/')[-1]  # Estrai il nome del file
            client_socket.sendall(file_name.encode('utf-8'))

            # Invia i dati del file
            with open(file_path, 'rb') as file:
                data = file.read(1024)
                while data:
                    client_socket.sendall(data)
                    data = file.read(1024)

            print('File inviato!')

        except ConnectionRefusedError:
            print("Impossibile stabilire la connessione. Assicurati che il server sia in esecuzione.")
        except Exception as e:
            print(f"Si è verificato un errore: {e}")

if __name__ == '__main__':
    eth_restore()
    time.sleep(2)
    choose_file()  # Apri il dialogo per scegliere il file
