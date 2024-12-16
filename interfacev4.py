import tkinter as tk
from tkinter import ttk, filedialog
import socket
import threading
import json
from collections import Counter
import time

class Exit(Exception):
    pass

# Classe pour gérer l'interface
class PlanningPokerApp:
    def __init__(self):
        self.main = tk.Tk()
        self.main.title("Planning Poker")
        self.main.geometry("1080x720")
        self.PORT = 16383
        self.setup_lan_menu()
        self.main.mainloop()

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
        self.server_socket = None
        self.server_thread = None
        self.stop_server = threading.Event()  # Nouvel attribut pour contrôler l'arrêt du serveur

        self.IP = self.get_ip_address()
        self.window = tk.Toplevel()
        self.window.title("Hôte - Planning Poker")
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)  # Gestion de la fermeture de la fenêtre
        self.setup_host_interface()
        self.start_server_thread()

    def on_window_close(self):
        # Méthode pour fermer proprement la fenêtre et le serveur
        self.stop_server.set()
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self.window.destroy()

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
        # Afficher l'IP
        tk.Label(self.window, text=f"Votre IP : {self.IP}").pack(pady=5)
        tk.Label(self.window, text="Communiquez votre IP aux joueurs pour rejoindre.").pack(pady=5)

        # Tableau pour afficher les pseudos
        self.table = ttk.Treeview(self.window, columns=("Pseudo"), show="headings")
        self.table.heading("Pseudo", text="Pseudos")
        self.table.pack(pady=5)

        # Options pour le mode de jeu
        tk.Label(self.window, text="Mode de jeu :")
        options = ['Majorité absolue', 'Majorité relative', 'Moyenne', 'Médiane']

        self.choix_var = tk.StringVar(self.window)
        self.choix_var.set(options[0])
        self.choix = tk.OptionMenu(self.window, self.choix_var, *options)
        self.choix.pack(pady=20)

        # Bouton pour parcourir le backlog
        tk.Button(self.window, text="Parcourir backlog", command=self.parcourir).pack(pady=10)

        # Champs pour le temps de discussion
        tk.Label(self.window, text="Temps de discussion (secondes) :").pack(pady=2)
        self.time_discussion_var = tk.StringVar(self.window)
        self.time_discussion_var.set("5")  # Valeur par défaut
        self.time_discussion_entry = tk.Entry(self.window, textvariable=self.time_discussion_var)
        self.time_discussion_entry.pack(pady=2)

        # Champs pour le temps de vote
        tk.Label(self.window, text="Temps de vote (secondes) :").pack(pady=2)
        self.time_vote_var = tk.StringVar(self.window)
        self.time_vote_var.set("10")  # Valeur par défaut
        self.time_vote_entry = tk.Entry(self.window, textvariable=self.time_vote_var)
        self.time_vote_entry.pack(pady=2)

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
        # Réinitialisez les événements et les états
        self.stop_server.clear()
        self.started = False
        self.clients = []
        self.pseudo_list = []

        # Créez un nouveau thread pour écouter les clients
        self.server_thread = threading.Thread(target=self.listen_for_clients, daemon=True)
        self.server_thread.start()

    # Ecoute des connexions entrantes
    def listen_for_clients(self):
        try:
            # Créez un nouveau socket à chaque fois
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                # Activation de SO_REUSEADDR
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.settimeout(1.0)  # Timeout pour vérifier régulièrement stop_server
                
                # Stockez le serveur comme attribut de l'instance
                self.server_socket = server
                
                server.bind((self.IP, 16383))
                server.listen()
                print(f"Serveur en écoute sur {self.IP}:{16383}")
                
                while not self.stop_server.is_set() and not self.started:
                    try:
                        # Utilisez accept() avec timeout pour vérifier régulièrement stop_server
                        server.settimeout(1.0)
                        conn, addr = server.accept()
                        
                        # Créez un thread pour chaque client
                        client_thread = threading.Thread(
                            target=self.handle_client, 
                            args=(conn,), 
                            daemon=True
                        )
                        client_thread.start()
                    
                    except socket.timeout:
                        # Vérifiez si on doit s'arrêter
                        if self.stop_server.is_set():
                            break
                    except Exception as e:
                        print(f"Erreur de connexion : {e}")
                        break
        
        except Exception as e:
            print(f"Erreur du serveur : {e}")
        finally:
            # Assurez-vous que le socket est bien fermé
            if hasattr(self, 'server_socket'):
                try:
                    self.server_socket.close()
                except:
                    pass

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
        self.stop_server.set()  # Arrêtez l'écoute des nouveaux clients
        
        # Envoi du signal à tous les joueurs
        for client in self.clients:
            client.sendall("@@START@@".encode())
        print("Partie lancée!")
        self.window.destroy()
        self.start_game_loop()

    def start_game_loop(self):
        self.paused = False
        self.mode = self.choix_var.get()
        print(self.mode)

        self.resultat = []

        game_window = tk.Toplevel()
        game_window.title("Planning Poker - Partie en cours")

        for client in self.clients:
            client.sendall(str(self.time_vote_var.get()).encode()) # On transmet à tous les utilisateurs le temps des votes


        n=1
        # On parcourt toutes les questions dans le backlog
        try:
            for key, value in self.backlog.items():
            
                question = value
                for client in self.clients:
                    print('QUESTION')
                    client.sendall(question.encode())
                # Interface principale pour la partie

                print(question)

                condition = False
                nb_rounds = 0
                while not condition:
                    tk.Label(game_window, text=f"Estimez la tâche suivante : {question}").pack()       
                    tk.Label(game_window, text=f"En attente des votes... ").pack()

                    game_window.update()

                    # Démarre la collecte des votes
                    self.collect_votes(game_window)

                    for vote in self.votes:
                        if "cafe" in vote:
                            raise Exit
                            

                    if nb_rounds > 0:
                        match self.mode:
                            case 'Moyenne':

                                lst = [0 if int(x) == -1 else int(x) for x in self.votes]
                                print(lst)
                                avg = sum(lst) / len(lst) if lst else 0
                                self.resultat.append(avg)
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

                                self.resultat.append(med)
                
                                tk.Label(game_window, text=f"Mediane : {med}").pack()
                                condition = True

                            case 'Majorité absolue':

                                if len(set(self.votes)) == 1:
                                    self.resultat.append(int(self.votes[0]))
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
                                        self.resultat.append(int(value))
                                        tk.Label(game_window, text=f"Majorité relative ! : {value}").pack()
                                        condition = True

                                tk.Label(game_window, text=f"Pas de majorité relative..").pack()

                    else:
                        if len(set(self.votes)) == 1:
                            self.resultat.append(int(self.votes[0]))
                            tk.Label(game_window, text=f"Majorité absolue ! : {self.votes[0]}").pack()   
                            condition = True
                        else:
                            tk.Label(game_window, text=f"Pas de majorité absolue..").pack()


                    for client in self.clients: ## On fait un feedback à tous les clients
                        tag = '@@FEEDBACK@@'
                        print('FEEDBACK')
                        print(self.full_list)
                        client.sendall(tag.encode())

                        full_char = []
                        for el in self.full_list:
                            full_char.append(':'.join(el))

                        full_char = str(int(condition)) + ';'.join(full_char) # On transmet l'état de la condition de la question ainsi que la liste de tous les votes
                        print(full_char)
                        client.sendall(full_char.encode())
                    

                    if not condition:   # Temps de disccussion

                        countdown_time = int(self.time_discussion_var.get()) # On récupere les paramètres de la partie
                        countdown_label = tk.Label(game_window, text=f"Temps restant: {countdown_time}", font=("Helvetica", 16))
                        countdown_label.pack(pady=10)

                        while countdown_time > 0:
                            countdown_label.config(text=f"Temps restant: {countdown_time}")
                            game_window.update()  # Met à jour l'interface pour afficher le nouveau temps
                            time.sleep(1)  # Attendre 1 seconde
                            countdown_time -= 1  # Décrémenter le temps restant

                        countdown_label.config(text="Temps écoulé !") 

                    game_window.update()

                    for client in self.clients: ## On prévient les clients qu'on passe à l'étape suivante
                        tag = '@@NEW@@'
                        print('NEW')
                        client.sendall(tag.encode())

                    time.sleep(1)

                    if not condition:
                        for client in self.clients:
                            print('QUESTION')
                            client.sendall(question.encode())

                    nb_rounds += 1

            n += 1 # Incrémente le nb de questions 
        except Exit:
            print('Fin de partie prématurée')
            self.paused = True

        for client in self.clients:
            tag = '@@END@@'
            print('Fin de la partie')
            client.sendall(tag.encode())

        # fin de la partie enregistrement des tâches   

        if self.paused: # Si la partie s'est terminée correctement on enregistre un sousback log à la place de l'ancien

            new_backlog = {task: self.resultat[i] for i, task in enumerate(list(self.backlog.values())[:n])}
            sub_backlog = dict(list(self.backlog.items())[n:])  # Créer un sous-backlog à partir de n
            sub_backlog_indice = {i + 1: value for i, (key, value) in enumerate(sub_backlog.items())}

            with open('./backlog_output.json', 'w', encoding='utf-8') as f:
                json.dump(new_backlog, f, ensure_ascii=False, indent=4)

            
            with open('./backlog.json', 'w', encoding='utf-8') as f:
                json.dump(sub_backlog_indice, f, ensure_ascii=False, indent=4)

        else: 
            new_backlog = {task: self.resultat[i] for i, task in enumerate(self.backlog.values())}

            with open('./backlog_output.json', 'w', encoding='utf-8') as f:
                json.dump(new_backlog, f, ensure_ascii=False, indent=4)

        print('Fichier sauvegardé')

        tk.Label(game_window, text="Fin de la partie").pack()
        tk.Button(game_window, text="Quitter", command=lambda : self.fin_partie(game_window)).pack()

    def fin_partie(self, game_window):
        # Fermeture de tous les clients
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        game_window.destroy()
        
        # Réinitialisez pour une nouvelle partie
        self.stop_server.clear()
        self.started = False
        self.clients = []
        self.pseudo_list = []

    def collect_votes(self, game_window):
        self.full_list = []
        self.votes = []  # Liste pour stocker les votes
        
        while len(self.votes) < len(self.clients):  
            # On essaie de recevoir les votes de chaque client
            for client in self.clients:
                try:
                    vote = client.recv(1024).decode()  # Recevoir un vote
                    info = vote.split(';')
                    self.full_list.append(info) # Stocke le pseudo + le vote
                    self.votes.append(info[1]) # Stocke uniquement le vote pour les traitements
                
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
        self.pseudo = ''

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
        self.pseudo = self.entry_pseudo.get()
        try:
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((server_ip, 16383))
            self.conn.sendall(self.pseudo.encode())
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

        # Initialisation des paramètres de jeu
        self.server_time_vote = int(self.conn.recv(1024).decode())
        self.time_discussion_var = tk.StringVar(value="5")  # Temps de discussion par défaut

        # Création des widgets
        self.label_info = tk.Label(game_window, text="En attente des autres votes...")
        self.label_question = tk.Label(game_window, text="Question : ", font=("Helvetica", 14))
        self.label_vote = tk.Label(game_window, text="Votre Vote :")

        self.vote_entry = tk.Entry(game_window)

        self.frame_1 = tk.Frame(game_window)
        self.frame_2 = tk.Frame(game_window)


        self.image_0 = tk.PhotoImage(file='assets/cartes_0.png').subsample(2, 2)
        self.image_1 = tk.PhotoImage(file='assets/cartes_1.png').subsample(2, 2)
        self.image_2 = tk.PhotoImage(file='assets/cartes_2.png').subsample(2, 2)
        self.image_3 = tk.PhotoImage(file='assets/cartes_3.png').subsample(2, 2)
        self.image_5 = tk.PhotoImage(file='assets/cartes_5.png').subsample(2, 2)
        self.image_8 = tk.PhotoImage(file='assets/cartes_8.png').subsample(2, 2)
        self.image_13 = tk.PhotoImage(file='assets/cartes_13.png').subsample(2, 2)
        self.image_20 = tk.PhotoImage(file='assets/cartes_20.png').subsample(2, 2)
        self.image_40 = tk.PhotoImage(file='assets/cartes_40.png').subsample(2, 2)
        self.image_100 = tk.PhotoImage(file='assets/cartes_100.png').subsample(2, 2)
        self.image_cafe = tk.PhotoImage(file='assets/cartes_cafe.png').subsample(2, 2)
        self.image_interro = tk.PhotoImage(file='assets/cartes_interro.png').subsample(2, 2)

        self.button_0 = tk.Button(game_window, image=self.image_0, borderwidth=0)
        self.button_1 = tk.Button(game_window, image=self.image_1, borderwidth=0)
        self.button_2 = tk.Button(game_window, image=self.image_2, borderwidth=0)
        self.button_3 = tk.Button(game_window, image=self.image_3, borderwidth=0)
        self.button_5 = tk.Button(game_window, image=self.image_5, borderwidth=0)
        self.button_8 = tk.Button(game_window, image=self.image_8, borderwidth=0)
        self.button_13 = tk.Button(game_window, image=self.image_13, borderwidth=0)
        self.button_20 = tk.Button(game_window, image=self.image_20, borderwidth=0)
        self.button_40 = tk.Button(game_window, image=self.image_40, borderwidth=0)
        self.button_100 = tk.Button(game_window, image=self.image_100, borderwidth=0)
        self.button_cafe = tk.Button(game_window, image=self.image_cafe, borderwidth=0)
        self.button_interro = tk.Button(game_window, image=self.image_interro, borderwidth=0)

        self.time_vote_label = tk.Label(game_window, text="", font=("Helvetica", 16))
        self.countdown_label = tk.Label(game_window, text="", font=("Helvetica", 16))

        # Création de la table de feedback
        self.feedback_table = ttk.Treeview(game_window, columns=("Pseudo", "Vote"), show="headings")
        self.feedback_table.heading("Pseudo", text="Pseudo")
        self.feedback_table.heading("Vote", text="Vote")

        # Pack initial des widgets principaux
        self.label_question.pack(pady=10)

        # Variables de contrôle de jeu
        self.fin = False
        self.voted = False
        self.countdown_active = False
        self.vote_timer = None
        self.remaining_time = 0

        def update_countdown():
            """Mettre à jour le compte à rebours"""
            if not self.countdown_active:
                return

            if self.remaining_time > 0:
                # Mettre à jour le label de temps
                self.time_vote_label.config(text=f"Temps restant: {self.remaining_time}")
                self.remaining_time -= 1
                
                # Reprogrammer le décompte
                self.vote_timer = game_window.after(1000, update_countdown)
            else:
                # Temps écoulé
                self.time_vote_label.config(text="Temps écoulé !")
                self.time_vote_label.pack_forget()

                # Envoyer un vote automatique si pas déjà voté
                if not self.voted:
                    send_vote(by_timer=True)
                
                # Réinitialiser le décompte
                self.countdown_active = False
                if self.vote_timer:
                    game_window.after_cancel(self.vote_timer)

        def start_countdown():
            """Initialiser et démarrer le compte à rebours"""
            # Annuler le décompte précédent s'il existe
            if self.countdown_active and self.vote_timer:
                game_window.after_cancel(self.vote_timer)
            
            # Réinitialiser les états
            self.voted = False
            self.countdown_active = True
            self.remaining_time = self.server_time_vote

            # Réafficher les éléments de vote
            self.label_vote.pack()

            self.frame_1.pack()
            self.frame_2.pack()

            self.button_0.pack(side="left", padx=5, pady=5, in_=self.frame_1)
            self.button_1.pack(side="left", padx=5, pady=5, in_=self.frame_1)
            self.button_2.pack(side="left", padx=5, pady=5, in_=self.frame_1)
            self.button_3.pack(side="left", padx=5, pady=5, in_=self.frame_1)
            self.button_5.pack(side="left", padx=5, pady=5, in_=self.frame_1)
            self.button_8.pack(side="left", padx=5, pady=5, in_=self.frame_1)

            self.button_13.pack(side="left", padx=5, pady=5, in_=self.frame_2)
            self.button_20.pack(side="left", padx=5, pady=5, in_=self.frame_2)
            self.button_40.pack(side="left", padx=5, pady=5, in_=self.frame_2)
            self.button_100.pack(side="left", padx=5, pady=5, in_=self.frame_2)
            self.button_cafe.pack(side="left", padx=5, pady=5, in_=self.frame_2)
            self.button_interro.pack(side="left", padx=5, pady=5, in_=self.frame_2)


            self.time_vote_label.pack()

            # Lancer le décompte
            update_countdown()

        def send_vote(vote_value=0, by_timer=False):
            """Envoyer le vote au serveur"""
            self.voted = True

            # Détermine le vote (0 par défaut si temps écoulé)
            if by_timer:
                vote = f"{self.pseudo};0"
            else:
                vote = f"{self.pseudo};{vote_value}"

            try:
                # Envoi du vote
                self.conn.sendall(vote.encode())
                print("Vote envoyé :", vote)
                
                # Réinitialisation de l'interface
                self.vote_entry.delete(0, tk.END)
                self.time_vote_label.pack_forget()
                self.label_vote.pack_forget()

                self.frame_1.pack_forget()
                self.frame_2.pack_forget()

                self.button_0.pack_forget()
                self.button_1.pack_forget()
                self.button_2.pack_forget()
                self.button_3.pack_forget()
                self.button_5.pack_forget()
                self.button_8.pack_forget()
                self.button_13.pack_forget()
                self.button_20.pack_forget()
                self.button_40.pack_forget()
                self.button_100.pack_forget()
                self.button_cafe.pack_forget()
                self.button_interro.pack_forget()

                # Afficher le message d'attente
                self.label_info.pack()
                
            except Exception as e:
                print("Erreur lors de l'envoi du vote :", e)

        def modified_send_vote(vote):
            """Gestion de l'envoi manuel du vote"""
            if self.countdown_active:
                if self.vote_timer:
                    game_window.after_cancel(self.vote_timer)
                self.countdown_active = False
            
            send_vote(vote)

        # Configuration du bouton de vote        
        self.button_0.config(command=lambda: modified_send_vote("0"))
        self.button_1.config(command=lambda: modified_send_vote("1"))
        self.button_2.config(command=lambda: modified_send_vote("2"))
        self.button_3.config(command=lambda: modified_send_vote("3"))
        self.button_5.config(command=lambda: modified_send_vote("5"))
        self.button_8.config(command=lambda: modified_send_vote("8"))
        self.button_13.config(command=lambda: modified_send_vote("13"))
        self.button_20.config(command=lambda: modified_send_vote("20"))
        self.button_40.config(command=lambda: modified_send_vote("40"))
        self.button_100.config(command=lambda: modified_send_vote("100"))
        self.button_cafe.config(command=lambda: modified_send_vote("cafe"))
        self.button_interro.config(command=lambda: modified_send_vote("-1"))

        # Boucle principale de jeu
        while not self.fin:
            # Réception du message du serveur
            question = self.conn.recv(1024).decode()
            print(f"Reçu : {question}")

            if question == '@@NEW@@':
                # Nouvelle étape de jeu
                self.label_info.pack_forget()
                print('Nouvelle étape')
            
            elif question == '@@FEEDBACK@@':
                # Traitement du feedback
                feedback = self.conn.recv(1024).decode()
                
                # Analyse de la condition de la question
                condition = bool(int(feedback[0]))
                feedback = feedback[1:].split(';')
                
                # Préparation et affichage des votes
                self.feedback_table.delete(*self.feedback_table.get_children())
                for item in feedback:
                    pseudo, vote = item.split(':')
                    self.feedback_table.insert('', 'end', values=(pseudo, vote))
                
                self.feedback_table.pack(pady=20)

                # Gestion du temps de discussion si pas de majorité
                if not condition:
                    countdown_time = int(self.time_discussion_var.get())
                    self.countdown_label.config(text=f"Temps de discussion : {countdown_time}")
                    self.countdown_label.pack(pady=10)

                    while countdown_time > 0:
                        self.countdown_label.config(text=f"Temps de discussion : {countdown_time}")
                        game_window.update()
                        time.sleep(1)
                        countdown_time -= 1

                    self.countdown_label.pack_forget()
                
                self.feedback_table.pack_forget()
            
            elif question == '@@END@@':
                # Fin de la partie
                print('Fin de la partie')
                self.fin = True
            
            elif question:
                # Nouvelle question
                self.label_question.config(text=f"Question : {question}")
                print('Nouvelle question')
                start_countdown()

            # Mise à jour de la fenêtre
            game_window.update()

        for widget in game_window.winfo_children():
            widget.destroy()
        
        tk.Label(game_window, text="Fin de la partie").pack()
        tk.Button(game_window, text="Quitter", command=lambda : self.fin_partie(game_window)).pack()

    
    def fin_partie(self, game_window):
        game_window.destroy()
        self.conn.close()
        

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
