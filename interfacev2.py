import tkinter as tk
from tkinter import ttk
import socket
import threading

# Classe pour gérer l'interface
class PlanningPokerApp:
    def __init__(self):
        self.main = tk.Tk()
        self.main.title("Planning Poker")
        self.main.geometry("1080x720")
        self.PORT = 16383
        self.setup_main_menu()
        self.main.mainloop()

    def setup_main_menu(self):
        self.clear_window()
        tk.Label(self.main, text="Bienvenue dans Planning Poker!").pack(pady=10)
        tk.Button(self.main, text="Jouer en LAN", command=self.setup_lan_menu).pack(pady=5)
        tk.Button(self.main, text="Jouer en Local", command=self.setup_local_menu).pack(pady=5)

    def setup_lan_menu(self):
        self.clear_window()
        tk.Button(self.main, text="Héberger une Partie", command=HostGame).pack(pady=10)
        tk.Button(self.main, text="Rejoindre une Partie", command=ClientGame).pack(pady=10)

    def setup_local_menu(self):
        self.clear_window()
        tk.Label(self.main, text="Mode Local en cours de développement").pack(pady=10)

    def clear_window(self):
        for widget in self.main.winfo_children():
            widget.destroy()

# Classe pour héberger une partie
class HostGame:
    def __init__(self):
        self.clients = []
        self.pseudo_list = []
        self.started = False
        self.IP = self.get_ip_address()
        self.window = tk.Toplevel()
        self.window.title("Hôte - Planning Poker")
        self.setup_host_interface()
        self.start_server_thread()
    
    # Recuperer l'ip de l'hôte
    def get_ip_address(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
        except:
            return "127.0.0.1"
        finally:
            s.close()

    # Interface de l'hôte pour inviter d'autres joueurs
    def setup_host_interface(self):
        tk.Label(self.window, text=f"Votre IP : {self.IP}").pack(pady=5)
        tk.Label(self.window, text="Communiquez votre IP aux joueurs pour rejoindre.").pack(pady=5)
        self.table = ttk.Treeview(self.window, columns=("Pseudo"), show="headings")
        self.table.heading("Pseudo", text="Pseudos")
        self.table.pack(pady=5)
        tk.Button(self.window, text="Lancer la Partie", command=self.start_game).pack(pady=10)

    def start_server_thread(self):
        threading.Thread(target=self.listen_for_clients, daemon=True).start()

    # Ecoute des connexions entrantes
    def listen_for_clients(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((self.IP, 16383))
            server.listen()
            print(f"Serveur en écoute sur {self.IP}:{16383}")
            while not self.started:
                conn, addr = server.accept()
                threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    # Ajout du client
    def handle_client(self, conn):
        pseudo = conn.recv(1024).decode()
        self.clients.append(conn)
        self.pseudo_list.append(pseudo)
        self.update_table()
        self.broadcast_pseudos()

    # Mettre à jour la table du client
    def update_table(self):
        self.table.delete(*self.table.get_children())
        for pseudo in self.pseudo_list:
            self.table.insert('', 'end', values=(pseudo))

    # Diffuser tous les pseudos à tous les clients connectés (Pour qu'ils puissent mettre à jour leurs table)
    def broadcast_pseudos(self):
        data = ';'.join(self.pseudo_list)
        for client in self.clients:
            client.sendall(data.encode())

    # Lancer la partie
    def start_game(self):
        self.started = True
        # Envoi du signal à tous les joueurs
        for client in self.clients:
            client.sendall("@@START@@".encode())
        print("Partie lancée!")
        self.window.destroy()
        self.start_game_loop()
        # Future implementation: Launch the game loop here.

    def start_game_loop(self):
        # Interface principale pour la partie
        game_window = tk.Toplevel()
        game_window.title("Planning Poker - Partie en cours")

        # Exemple d'affichage d'une question
        tk.Label(game_window, text="Question : Estimez la tâche suivante ?").pack(pady=10)

        # Zone pour votes des joueurs
        self.vote_result = tk.StringVar(value="En attente des votes...")
        tk.Label(game_window, textvariable=self.vote_result).pack(pady=10)

        # Logique simple pour collecter les votes
        self.collect_votes(game_window)

    def collect_votes(self, window):
        # Exemple : Simuler l'attente des votes des clients
        def wait_for_votes():
            while True:
                votes = []
                for client in self.clients:
                    try:
                        vote = client.recv(1024).decode()
                        votes.append(vote)
                    except:
                        pass
                if len(votes) == len(self.clients):  # Si tous les votes sont reçus
                    self.vote_result.set(f"Votes reçus : {', '.join(votes)}")
                    break

        threading.Thread(target=wait_for_votes, daemon=True).start()

# Classe pour rejoindre une partie
class ClientGame:
    def __init__(self):
        self.window = tk.Toplevel()
        self.window.title("Client - Planning Poker")
        self.conn = None
        self.setup_client_interface()

    # Interface du client pour se connecter
    def setup_client_interface(self):
        tk.Label(self.window, text="IP du Serveur:").grid(row=0, column=0, padx=10, pady=5)
        self.entry_ip = tk.Entry(self.window)
        self.entry_ip.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(self.window, text="Votre Pseudo:").grid(row=1, column=0, padx=10, pady=5)
        self.entry_pseudo = tk.Entry(self.window)
        self.entry_pseudo.grid(row=1, column=1, padx=10, pady=5)

        tk.Button(self.window, text="Se Connecter", command=self.connect_to_server).grid(row=2, column=1, pady=10)

    # Connection au serveur
    def connect_to_server(self):
        server_ip = self.entry_ip.get()
        pseudo = self.entry_pseudo.get()
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((server_ip, 16383))
            self.conn.sendall(pseudo.encode())
            self.setup_waiting_interface()
            threading.Thread(target=self.listen_to_server, daemon=True).start()
        except Exception as e:
            tk.Label(self.window, text=f"Erreur: {e}").grid(row=3, column=0, columnspan=2)

    # Interface attente du démarrage de la partie
    def setup_waiting_interface(self):
        self.clear_window()
        tk.Label(self.window, text="En attente du démarrage de la partie...").pack(pady=10)
        self.table = ttk.Treeview(self.window, columns=("Pseudo"), show="headings")
        self.table.heading("Pseudo", text="Pseudos")
        self.table.pack(pady=5)

    # Ecoute du signal de lancement du server
    def listen_to_server(self):
        while True:
            data = self.conn.recv(1024).decode()
            if data == "@@START@@": 
                print("Partie lancée!")
                self.window.destroy()
                self.start_game_loop()
                break
            else:
                self.update_table(data.split(';'))

    # Lancement de la partie 
    def start_game_loop(self):
        # Interface principale pour la partie
        game_window = tk.Toplevel()
        game_window.title("Planning Poker - Partie en cours")

        # Exemple d'affichage d'une question
        tk.Label(game_window, text="Question : Estimez la tâche suivante ?").pack(pady=10)

        # Zone pour voter
        tk.Label(game_window, text="Votre Vote :").pack(pady=5)
        self.vote_entry = tk.Entry(game_window)
        self.vote_entry.pack(pady=5)

        tk.Button(game_window, text="Envoyer", command=self.send_vote).pack(pady=10)

    # Envoyer le vote au server 
    def send_vote(self):
        vote = self.vote_entry.get()
        try:
            self.conn.sendall(vote.encode())
            print("Vote envoyé :", vote)
        except Exception as e:
            print("Erreur lors de l'envoi du vote :", e)

    # Mettre a jour la table
    def update_table(self, pseudos):
        self.table.delete(*self.table.get_children())
        for pseudo in pseudos:
            self.table.insert('', 'end', values=(pseudo))
    
    # Reinisialiser l'interface
    def clear_window(self):
        for widget in self.window.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    PlanningPokerApp()
