import tkinter as tk
from tkinter import ttk, filedialog
import socket
import threading
import json
from collections import Counter

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

        tk.Label(self.window, text="Mode de jeu :")
        options = ['Moyenne','Mediane','Majorité absolue','Majorité relative']

        self.choix_var = tk.StringVar(self.window)
        self.choix_var.set(options[0])
        self.choix = tk.OptionMenu(self.window, self.choix_var, *options)
        self.choix.pack(pady=20)

        tk.Button(self.window, text="Parcourir backlog", command=self.parcourir).pack(pady=10)

    def parcourir(self):
        path = filedialog.askopenfilename(
            title="Sélectionnez un fichier JSON",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if path:
            with open(path, "r", encoding="utf-8") as file:
                print('fichier chargé')
                self.backlog = json.load(file)
                tk.Button(self.window, text="Lancer la Partie", command=self.start_game).pack(pady=10)
                result = tk.Label(self.window, text="Fichier chargé avec succès")
                self.window.lift()
        else:
            result = tk.Label(self.window, text="Aucun fichier chargé.")
        result.pack()

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
        self.mode = self.choix_var.get()
        print(self.mode)

        game_window = tk.Toplevel()
        game_window.title("Planning Poker - Partie en cours")

        # On parcourt toutes les questions dans le backlog
        for key, value in self.backlog.items():
            question = value

            # Interface principale pour la partie

            print(question)

            condition = False
            while not condition:
                tk.Label(game_window, text=f"Estimez la tâche suivante : {question}").pack()       
                tk.Label(game_window, text=f"En attente des votes... ").pack()

                game_window.update()

                # Démarre la collecte des votes
                self.collect_votes(game_window)

                match self.mode:
                    case 'Moyenne':

                        lst = list(map(float, self.votes))
                        avg = sum(lst) / len(lst)
                        # Anticiper la sauvegarde du resultat dans un fichier de sortie (avg)
                        tk.Label(game_window, text=f"Moyenne : {avg}").pack()

                        condition = True

                    case 'Mediane':

                        lst = sorted(map(float, self.votes))  # Convertir en nombres et trier
                        n = len(lst)
                        milieu = n // 2

                        if n % 2 == 0:
                            med = (lst[milieu - 1] + lst[milieu]) / 2
                        else:
                            med = lst[milieu]
        
                        tk.Label(game_window, text=f"Mediane : {med}").pack()
                        condition = True

                    case 'Majorité absolue':

                        if len(set(self.votes)) == 1:
                            # Anticiper la sauvegarde du resultat dans un fichier de sortie (self.votes[0])
                            tk.Label(game_window, text=f"Majorité absolue ! : {self.votes[0]}").pack()   
                            condition = True
                        else:
                            tk.Label(game_window, text=f"Pas de majorité absolue..").pack()   

                    case 'Majorité relative':

                        count = Counter(self.votes)
                        most_common = count.most_common(1)
                        if most_common:
                            value, freq = most_common[0]
                            if freq > len(self.votes) / 2:
                                # Anticiper la sauvegarde du resultat dans un fichier de sortie (value)
                                tk.Label(game_window, text=f"Majorité relative ! : {value}").pack()
                                condition = True

                        tk.Label(game_window, text=f"Pas de majorité relative..").pack()


                game_window.update()

        # fin de la partie enregistrement des tâches

    def collect_votes(self, game_window):
        self.votes = []  # Liste pour stocker les votes
        
        while len(self.votes) < len(self.clients):  
            # On essaie de recevoir les votes de chaque client
            for client in self.clients:
                try:
                    vote = client.recv(1024).decode()  # Recevoir un vote
                    self.votes.append(vote)

                    ## Envoyer un signal à l'interface du client concerné pour desactiver son interface

                except:
                    continue

        # Si tous les votes sont reçus, afficher les résultats
        tk.Label(game_window, text=f"Votes reçus : {', '.join(self.votes)}").pack()
        print(self.votes)  # Affiche les votes reçus

    def clear_window(self):
        for widget in self.window.winfo_children():
            widget.destroy()
    

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
