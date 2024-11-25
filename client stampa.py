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

def try_connecting_to_server(port_range):
    """
    Prova a connettersi su tutte le porte nel range specificato (5000-5005).
    Restituisce il socket connesso e le informazioni del server (IP e porta).
    """
    for port in port_range:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                # Prova a connettersi alla porta corrente nel range
                client_socket.connect(('0.0.0.0', port))  # Si connette all'IP locale generico
                # Riceve l'IP e la porta reali dal server
                server_info = client_socket.recv(1024).decode('utf-8')
                server_ip, server_port = server_info.split(':')
                server_port = int(server_port)
                print(f"Connessione trovata su {server_ip}:{server_port}")
                return server_ip, server_port  # Restituisce IP e porta corretti

            except (ConnectionRefusedError, socket.timeout):
                print(f"Porta {port} non disponibile, provo con la successiva...")
            except Exception as e:
                print(f"Errore durante la connessione alla porta {port}: {e}")
    
    # Se nessuna porta risponde, restituisce None
    return None, None

def send_file(file_path):
    # Prova a connettersi su tutte le porte nel range 5000-5005
    server_ip, server_port = try_connecting_to_server(range(5000, 5006))

    if server_ip and server_port:
        # Ora che abbiamo IP e porta corretti, apriamo una connessione per inviare il file
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as new_socket:
            try:
                new_socket.connect((server_ip, server_port))

                # Invia il nome del file
                file_name = file_path.split('/')[-1]  # Estrai il nome del file
                new_socket.sendall(file_name.encode('utf-8'))

                # Invia i dati del file
                with open(file_path, 'rb') as file:
                    data = file.read(1024)
                    while data:
                        new_socket.sendall(data)
                        data = file.read(1024)

                print('File inviato!')

            except ConnectionRefusedError:
                print("Impossibile stabilire la connessione al server.")
            except Exception as e:
                print(f"Si è verificato un errore durante l'invio del file: {e}")
    else:
        print("Impossibile trovare il server su nessuna delle porte specificate.")

if __name__ == '__main__':
    eth_restore()
    time.sleep(2)
    choose_file()  # Apri il dialogo per scegliere il file
