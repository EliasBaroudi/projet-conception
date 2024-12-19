import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import font as tkfont
import socket
import threading
import json
from collections import Counter
import time
import os
import sys

class Exit(Exception):
    """
    @brief Exception personnalisée pour signaler une sortie anticipée du jeu.
    
    Cette exception est utilisée pour terminer prématurément la session de jeu Planning Poker.
    """
    pass

# Classe pour gérer l'interface
class PlanningPokerApp:
    """
    @brief Classe principale de l'application Planning Poker.
    
    Cette classe initialise la fenêtre principale et configure le menu LAN 
    pour héberger ou rejoindre une partie.
    """

    def __init__(self):
        """
        @brief Constructeur de PlanningPokerApp.
        
        Crée la fenêtre principale de l'application et configure l'interface initiale.
        """

        main = tk.Tk()
        main.title("Planning Poker")
        main.geometry("300x420")
        main.resizable(False, False) 


        PORT = 16383
        self.setup_lan_menu(main)
        main.mainloop()

    def setup_lan_menu(self, main):

        """
        @brief Configure le menu de connexion LAN.
        
        Nettoie la fenêtre principale et ajoute les boutons pour héberger 
        ou rejoindre une partie.
        
        @param main La fenêtre Tkinter principale
        """

        for widget in main.winfo_children():
            widget.destroy()

        if sys.platform == "win32":
            # Windows : utiliser un fichier .ico
            main.iconbitmap('assets/icon.ico')
        else:
            # Linux et Mac : utiliser un fichier .png
            icon = tk.PhotoImage('assets/icon.png')
            main.tk.call('wm', 'iconphoto', main._w, icon)

        background = tk.PhotoImage(file='assets/background.png')
        img = tk.Label(main, image=background)
        img.place(x=0, y=0, relwidth=1, relheight=1)

        host_image = tk.PhotoImage(file='assets/host_button.png')
        join_image = tk.PhotoImage(file='assets/join_button.png')

        tk.Button(main, image=host_image, command=lambda: HostGame(main)).pack(pady=10)
        tk.Button(main, image=join_image, command=lambda: ClientGame(main)).pack(pady=10)

        main.mainloop()
        
    
    
# Classe pour héberger une partie
class HostGame:
    """
    @brief Classe gérant l'hôte d'une partie de Planning Poker.
    
    Gère la création du serveur, l'interface d'hébergement, et le 
    déroulement de la partie côté serveur.
    """

    def __init__(self, parent_window):
        """
        @brief Constructeur de HostGame.
        
        Initialise les paramètres du serveur, récupère l'adresse IP, 
        et configure l'interface d'hébergement.
        
        @param parent_window La fenêtre parente Tkinter
        """

        self.parent = parent_window
        self.parent.withdraw()

        self.PORT = 16383
        self.clients = []
        self.pseudo_list = []
        self.started = False
        self.server_socket = None
        self.stop_server = threading.Event()

        self.IP = self.get_ip_address()
        self.window = tk.Toplevel(parent_window)
        self.window.title("Hôte - Planning Poker")
        self.window.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.start_server_thread()
        self.setup_host_interface()

    def on_window_close(self):
        """
        @brief Gère la fermeture de la fenêtre d'hébergement.
        
        Arrête le serveur et ferme le socket en cours.
        """
        self.stop_server.set()
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self.window.destroy()

    # Recuperer l'ip de l'hôte
    def get_ip_address(self):
        """
        @brief Récupère l'adresse IP de l'hôte.
        
        Tente de récupérer l'adresse IP locale, avec un repli sur localhost.
        
        @return L'adresse IP de l'hôte
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"

    # Interface de l'hôte pour inviter d'autres joueurs
    def setup_host_interface(self):
        """
        @brief Configure l'interface utilisateur pour l'hôte.
        
        Crée les éléments graphiques pour :
        - Afficher l'adresse IP
        - Lister les pseudos des joueurs
        - Sélectionner le mode de jeu
        - Charger le backlog
        - Configurer les temps de discussion et de vote
        """

        # Display IP
        self.police = tkfont.Font(family="Cascadia Code", size=12, weight="bold")
        

        if sys.platform == "win32":
            # Windows : utiliser un fichier .ico
            self.window.iconbitmap('assets/icon.ico')
        else:
            # Linux et Mac : utiliser un fichier .png
            icon = tk.PhotoImage('assets/icon.png')
            self.window.tk.call('wm', 'iconphoto', self.window._w, icon)

        self.window.resizable(False, False) 

        background = tk.PhotoImage(file='assets/background2.png')
        img = tk.Label(self.window, image=background)
        img.place(x=0, y=0, relwidth=1, relheight=1)

        tk.Label(self.window, text=f"Votre IP : {self.IP}", bg="#0c5219", fg='white', font=self.police).pack(pady=5)
        tk.Label(self.window, text="Communiquez votre IP aux joueurs pour rejoindre.", bg="#0c5219", fg='white', font=self.police).pack(pady=5)

        # Pseudos table
        style = ttk.Style()
        style.theme_use("clam")
        style.configure('Treeview.Heading',
                        columns=("Pseudos",),
                        font = self.police,
                        background = "#061d0a",
                        foreground = "white",
                        rowheight = 30)

        style.configure('Treeview',
                        font = self.police,
                        background = "#white",
                        foreground = "black",
                        rowheight = 30)

        self.table = ttk.Treeview(self.window, columns=("Pseudos"), show="headings", style='Treeview')
        self.table.column("Pseudos", anchor=tk.CENTER)
        self.table.heading("Pseudos", text="Joueurs")
        self.table.pack(pady=5)

        # Game mode options
        self.mode_banner = tk.PhotoImage(file='assets/mode_banner.png')
        tk.Label(self.window, image=self.mode_banner).pack()
        options = ['Majorité absolue', 'Majorité relative', 'Moyenne', 'Médiane']

        self.choix_var = tk.StringVar(self.window)
        self.choix_var.set(options[0])
        self.choix = tk.OptionMenu(self.window, self.choix_var, *options)
        self.choix.pack(pady=20)

        # Backlog button

        backlog_button = tk.PhotoImage(file='assets/backlog_button.png')
        tk.Button(self.window, image=backlog_button, command=self.parcourir).pack(pady=10)

        # Discussion time
        tk.Label(self.window, text="Temps de discussion (secondes) :", bg="#0c5219", fg='white', font=self.police).pack(pady=2)
        self.time_discussion_var = tk.StringVar(self.window, value="60")
        self.time_discussion_entry = tk.Entry(self.window, textvariable=self.time_discussion_var)
        self.time_discussion_entry.pack(pady=2)

        # Vote time
        tk.Label(self.window, text="Temps de vote (secondes) :", bg="#0c5219", fg='white', font=self.police).pack(pady=2)
        self.time_vote_var = tk.StringVar(self.window, value="30")
        self.time_vote_entry = tk.Entry(self.window, textvariable=self.time_vote_var)
        self.time_vote_entry.pack(pady=2)

        self.window.mainloop()


    def parcourir(self):
        """
        @brief Ouvre un explorateur de fichier
        
        Permet à l'hôte de spécifier le chemin au backlog.json à l'aide de l'explorateur de fichiers
        """

        path = filedialog.askopenfilename(
            title="Sélectionnez un fichier JSON",
            initialdir=os.getcwd(),  # Spécifiez le répertoire initial
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if path:
            with open(path, "r", encoding="utf-8") as file:
                print('Fichier chargé')
                self.backlog = json.load(file)
                start_button = tk.PhotoImage(file='assets/start_button.png')
                tk.Button(self.window, image=start_button, command=self.start_game).pack(pady=10)
                result = tk.Label(self.window, text="Fichier chargé avec succès", bg="#0c5219", fg='lightgreen', font=self.police)
                self.window.lift()
        else:
            result = tk.Label(self.window, text="Aucun fichier chargé.", bg="#0c5219", fg='red', font=self.police)
        result.pack()

        self.window.mainloop()

    def start_server_thread(self):
        """
        @brief Lance une écoute sur la méthode d'écoute de connexions entrantes

        """

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
        """
        @brief Gère les connexions des utilisateurs

        - Ecoute sur le port de connexions entrantes
        - Verifie régulièrement si le processus n'est pas arreté afin de fermer correctement les connexions une fois que cela est demandé
        """

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
        """
        @brief Inscrit les clients dans une liste

        @param conn : La connexion lancée par le server au début de l'écoute
        """

        pseudo = conn.recv(1024).decode()
        self.clients.append(conn)
        self.pseudo_list.append(pseudo)
        self.update_table()
        self.broadcast_pseudos()

    # Mettre à jour la table du client
    def update_table(self):
        """
        @brief Envoie un tableau à tous les clients

        Actualisation de l'interface pour les anciens clients, affichage du tableau pour les nouveaux
        """
        self.table.delete(*self.table.get_children())
        for pseudo in self.pseudo_list:
            self.table.insert('', 'end', values=(pseudo))

    # Diffuser tous les pseudos à tous les clients connectés (Pour qu'ils puissent mettre à jour leurs table)
    def broadcast_pseudos(self):
        """
        @brief Envoi les pseudos à tous les clients

        Envoie des pseudos, processus nécessaire à l'actualisation de l'interface chez chaque utilisateurs
        """
        data = ';'.join(self.pseudo_list)
        for client in self.clients:
            client.sendall(data.encode())

    # Lancer la partie
    def start_game(self):
        """
        @brief Declancher le lancement de la partie

        Envoi à chaque utilisateurs le tag de lancement de partie
        """
        self.started = True
        self.stop_server.set()  # Arrêtez l'écoute des nouveaux clients
        
        # Envoi du signal à tous les joueurs
        for client in self.clients:
            client.sendall("@@START@@".encode())
        print("Partie lancée!")
        self.window.destroy()
        self.start_game_loop()

    def start_game_loop(self):
        """
        @brief Boucle principale de l'application

        """
        self.paused = False
        self.mode = self.choix_var.get()
        self.resultat = []

        
        game_window = tk.Toplevel()
        game_window.resizable(False, False) 
        game_window.title("Planning Poker - Partie en cours")
        game_window.configure(bg='black')

        if sys.platform == "win32":
            # Windows : utiliser un fichier .ico
            game_window.iconbitmap('assets/icon.ico')
        else:
            # Linux et Mac : utiliser un fichier .png
            icon = tk.PhotoImage('assets/icon.png')
            game_window.tk.call('wm', 'iconphoto', game_window._w, icon)

        

        for client in self.clients:
            client.sendall(str(self.time_vote_var.get()+':'+self.time_discussion_var.get()).encode()) # On transmet à tous les utilisateurs le temps des votes
        time.sleep(1)

        n=1
        # On parcourt toutes les questions dans le backlog
        try:
            for key, value in self.backlog.items():
            
                question = value
                for client in self.clients:
                    client.sendall(question.encode())
                # Interface principale pour la partie

                condition = False
                nb_rounds = 0
                while not condition:
                    tk.Label(game_window, text=f"Estimez la tâche suivante : {question}", bg="black", fg='white', font=self.police).pack(side="top")       
                    tk.Label(game_window, text=f"En attente des votes... ", bg="black", fg='white', font=self.police).pack(side="top")

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
                                avg = sum(lst) / len(lst) if lst else 0
                                self.resultat.append(avg)
                                tk.Label(game_window, text=f"Moyenne : {avg}", bg="black", fg='white', font=self.police).pack(side="top")

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
                
                                tk.Label(game_window, text=f"Mediane : {med}", bg="black", fg='white', font=self.police).pack(side="top")
                                condition = True

                            case 'Majorité absolue':

                                if len(set(self.votes)) == 1:
                                    self.resultat.append(int(self.votes[0]))
                                    tk.Label(game_window, text=f"Majorité absolue ! : {self.votes[0]}", bg="black", fg='white', font=self.police).pack(side="top")   
                                    condition = True
                                else:
                                    tk.Label(game_window, text=f"Pas de majorité absolue..", bg="black", fg='white', font=self.police).pack(side="top")   

                            case 'Majorité relative':

                                count = Counter(self.votes)
                                most_common = count.most_common(1)
                                if most_common:
                                    value, freq = most_common[0]
                                    if freq > len(self.votes) / 2:
                                        self.resultat.append(int(value))
                                        tk.Label(game_window, text=f"Majorité relative ! : {value}", bg="black", fg='white', font=self.police).pack(side="top")
                                        condition = True

                                tk.Label(game_window, text=f"Pas de majorité relative..", bg="black", fg='white', font=self.police).pack(side="top")

                    else:
                        if len(set(self.votes)) == 1:
                            self.resultat.append(int(self.votes[0]))
                            tk.Label(game_window, text=f"Majorité absolue ! : {self.votes[0]}", bg="black", fg='white', font=self.police).pack(side="top")   
                            condition = True
                        else:
                            tk.Label(game_window, text=f"Pas de majorité absolue..", bg="black", fg='white', font=self.police).pack(side="top")


                    for client in self.clients: ## On fait un feedback à tous les clients
                        tag = '@@FEEDBACK@@'
                        client.sendall(tag.encode())

                        full_char = []
                        for el in self.full_list:
                            full_char.append(':'.join(el))

                        full_char = str(int(condition)) + ';'.join(full_char) # On transmet l'état de la condition de la question ainsi que la liste de tous les votes
                        client.sendall(full_char.encode())
                    

                    if not condition:   # Temps de disccussion

                        countdown_time = int(self.time_discussion_var.get()) # On récupere les paramètres de la partie
                        countdown_label = tk.Label(game_window, text=f"Temps restant: {countdown_time}", bg="black", fg='white', font=self.police)
                        countdown_label.pack(side="top")

                        while countdown_time > 0:
                            countdown_label.config(text=f"Temps restant: {countdown_time}")
                            game_window.update()  # Met à jour l'interface pour afficher le nouveau temps
                            time.sleep(1)  # Attendre 1 seconde
                            countdown_time -= 1  # Décrémenter le temps restant

                        countdown_label.config(text="Temps écoulé !") 

                    game_window.update()

                    for client in self.clients: ## On prévient les clients qu'on passe à l'étape suivante
                        tag = '@@NEW@@'
                        client.sendall(tag.encode())

                    time.sleep(1)

                    if not condition:
                        for client in self.clients:
                            client.sendall(question.encode())

                    nb_rounds += 1

            n += 1 # Incrémente le nb de questions 
        except Exit:
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

        tk.Label(game_window, text="Fin de la partie", bg="black", fg='white', font=self.police).pack(side="top")

        quit_button = tk.PhotoImage(file='assets/quit_button.png')
        tk.Button(game_window, image=quit_button, command=lambda : self.fin_partie(game_window)).pack(padx=20, pady=20)

        ## ATTENTION
        game_window.mainloop()

    def fin_partie(self, game_window):
        """
        @brief Méthode permettant un arrêt propre de l'application

        @param game_window : Fenetre de jeu

        - Ferme les connexions avec tous les clients
        - Ferme la connexion du server
        - Reinisialise les variables
        """

        game_window.destroy()
        
        # Fermeture de tous les clients
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        # Réinitialisez pour une nouvelle partie
        self.stop_server.clear()
        self.started = False
        self.clients = []
        self.pseudo_list = []

        self.parent.deiconify() # On réaffiche la fenetre principale


    def collect_votes(self, game_window):
        """
        @brief Méthode permettant la récolte des votes

        @param game_window : Fenetre de jeu

        - Analyse continuelement un retour des clients
        - Une fois que tous les retours sont fais affichage des retours 
        """
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
        tk.Label(game_window, text=f"Votes reçus : {', '.join(self.votes)}", bg="black", fg='white', font=self.police).pack()

    def clear_window(self):
        """
        @brief Reinisialiser la fenêtre

        """
        for widget in self.window.winfo_children():
            widget.destroy()
    

# Classe pour rejoindre une partie
class ClientGame:
    """
    @brief Classe gérant le client d'une partie de Planning Poker.
    
    Gère la connexion au serveur, l'interface de connexion et de vote.
    """

    def __init__(self, parent_window):
        """
        @brief Constructeur de ClientGame.
        
        Initialise les paramètres de connexion, et l'interface
        
        @param parent_window La fenêtre parente Tkinter
        """

        self.parent = parent_window
        self.parent.withdraw()

        self.window = tk.Toplevel(parent_window)
        self.window.resizable(False, False) 
        self.window.title("Client - Planning Poker")

        if sys.platform == "win32":
            # Windows : utiliser un fichier .ico
            self.window.iconbitmap('assets/icon.ico')
        else:
            # Linux et Mac : utiliser un fichier .png
            icon = tk.PhotoImage('assets/icon2.png')
            self.window.tk.call('wm', 'iconphoto', self.window._w, icon)
        

        self.conn = None
        self.pseudo = ''
        self.setup_client_interface()

    # Interface du client pour se connecter
    def setup_client_interface(self):
        """
        @brief Intisialisation de l'interface client
        
        - Champ pour l'IP et pour le pseudo
        - Bouton 'Se connecter'
        """

        self.police = tkfont.Font(family="Cascadia Code", size=12, weight="bold")

        background = tk.PhotoImage(file='assets/background.png')
        img = tk.Label(self.window, image=background)
        img.place(x=0, y=0, relwidth=1, relheight=1)

        tk.Label(self.window, text="IP du Serveur:", bg="#0c5219", fg='white', font=self.police).grid(row=0, column=0, padx=10, pady=5)
        self.entry_ip = tk.Entry(self.window)
        self.entry_ip.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(self.window, text="Votre Pseudo:", bg="#0c5219", fg='white', font=self.police).grid(row=1, column=0, padx=10, pady=5)
        self.entry_pseudo = tk.Entry(self.window)
        self.entry_pseudo.grid(row=1, column=1, padx=10, pady=5)

        connect_button = tk.PhotoImage(file='assets/connect_button.png')
        tk.Button(self.window, image=connect_button, command=self.connect_to_server).grid(row=2, column=1, pady=15, padx=55)

        self.window.mainloop()

    # Connection au serveur
    def connect_to_server(self):
        """
        @brief Connexion au server
        
        Récupère les informations de l'interface précédente et initie la connexion au server
        """

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
        """
        @brief Attente du lancement de la partie
        
        Interface fixe, avec un texte 'Attente du lancement de la partie'
        """

        self.clear_window()

        self.window.config(bg='#0c5219')
        tk.Label(self.window, text="En attente du démarrage de la partie...", bg="#0c5219", fg='white', font=self.police).pack(pady=30, padx=30)

        # Pseudos table
        style = ttk.Style()
        style.theme_use("clam")
        style.configure('Treeview.Heading',
                        columns=("Pseudos",),
                        font = self.police,
                        background = "#061d0a",
                        foreground = "white",
                        rowheight = 30)

        style.configure('Treeview',
                        font = self.police,
                        background = "#white",
                        foreground = "black",
                        rowheight = 30)


        self.table = ttk.Treeview(self.window, columns=("Pseudo"), show="headings", style='Treeview')
        self.table.heading("Pseudo", text="Joueur")
        self.table.column("Pseudo", anchor=tk.CENTER)
        self.table.pack(pady=30, padx=30)

    # Mettre a jour la table des utilisateurs
    def update_table(self, pseudos):
        """
        @brief Afficher les pseudos dans le tableau

        @param pseudos : liste des pseudos recues par le server

        Insère les tableaux recus par le server dans le tableau indiquant la liste des joueurs
        """
        self.table.delete(*self.table.get_children())
        for pseudo in pseudos:
            self.table.insert('', 'end', values=(pseudo))

    # Ecoute du signal de lancement du server
    def listen_to_server(self):
        """
        @brief Ecoute d'un signal du server
        
        Ecoute constamment sur la connexion jusqu'a recevoir un signal @@START@@ signifiant le lancement de la partie
        """
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
        """
        @brief Boucle de jeu principale

        - Intialisation de la fenêtre (Question, temps de vote, temps de discussion, cartes...)
        - Suis le rythme du server à l'aide des tags suivants:
            - @@NEW@@ : Signifie une nouvelle question
            - @@FEEDBACK@ : Signifie un retour du server avec les votes des joueurs 
            - @@END@@ : Signifie la fin de la partie
        """
        # Interface principale pour la partie
 
        game_window = tk.Toplevel()
        game_window.resizable(False, False) 
        game_window.title("Planning Poker - Partie en cours")
        
        
        if sys.platform == "win32":
            # Windows : utiliser un fichier .ico
            game_window.iconbitmap('assets/icon.ico')
        else:
            # Linux et Mac : utiliser un fichier .png
            icon = tk.PhotoImage('assets/icon2.png')
            game_window.tk.call('wm', 'iconphoto', game_window._w, icon)

        game_window.config(bg='#0c5219')

        # Initialisation des paramètres de jeu
        data = str(self.conn.recv(1024).decode()).split(':')
        self.server_time_vote = int(data[0])
        self.time_discussion_var = int(data[1]) # Temps de discussion par défaut

        # Création des widgets
        self.label_info = tk.Label(game_window, text="En attente des autres votes...", bg="#0c5219", fg='white', font=self.police)
        self.label_question = tk.Label(game_window, text="Question : ", bg="#0c5219", fg='white', font=self.police)
        self.label_vote = tk.Label(game_window, text="Choisissez une carte :", bg="#0c5219", fg='white', font=self.police)

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

        style = ttk.Style()
        style.theme_use("clam")
        style.configure('Treeview.Heading',
                        font = self.police,
                        background = "#061d0a",
                        foreground = "white",
                        rowheight = 30)

        style.configure('Treeview',
                        font = self.police,
                        background = "#white",
                        foreground = "black",
                        rowheight = 30)

        # Création de la table de feedback
        self.feedback_table = ttk.Treeview(game_window, columns=("Pseudo", "Vote"), show="headings", style='Treeview')
        self.feedback_table.heading("Pseudo", text="Joueur")
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
            """
            @brief Mise à jour du décompte de vote

            Tant que le décompte n'est pas terminé, on modifie le label correspondant au décompte
            A la fin du décompte si l'utilisateur n'a toujours voté, on envoie un vote nul automatiquement
            """
            if not self.countdown_active:
                return

            if self.remaining_time > 0:
                # Mettre à jour le label de temps
                self.time_vote_label.config(text=f"Temps restant: {self.remaining_time}", bg="#0c5219", fg='white', font=self.police)
                self.remaining_time -= 1
                
                # Reprogrammer le décompte
                self.vote_timer = game_window.after(1000, update_countdown)
            else:
                # Temps écoulé
                self.time_vote_label.config(text="Temps écoulé !", bg="#0c5219", fg='white', font=self.police)
                self.time_vote_label.pack_forget()

                # Envoyer un vote automatique si pas déjà voté
                if not self.voted:
                    send_vote(by_timer=True)
                
                # Réinitialiser le décompte
                self.countdown_active = False
                if self.vote_timer:
                    game_window.after_cancel(self.vote_timer)

        def start_countdown():
            """
            @brief Initialisation du décompte

            - Variables nécessaires au décompte intialisés
            - Affichage des cartes
            """

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
            """
            @brief Mise à jour du décompte de vote

            @param vote_value (0 par défaut) : Récupère le le vote lorsque l'utilisateur clique sur une carte
            @param by_timer (False par défaut) : Indique si l'arrivée dans cette méthode à été faite par l'utilisateur ou si elle a été automatique suite à la fin du décompte

            Envoi du vote au server
            Desactivation de l'interface de vote
            """
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
            """
            @brief Modifie l'envoi du vote

            @param vote : Valeur du vote de l'utilisateur

            Permet d'éviter des bugs d'interface nottament avec le décompte par la suite
            """
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
                    countdown_time = int(self.time_discussion_var)
                    self.countdown_label.config(text=f"Temps de discussion : {countdown_time}", bg="#0c5219", fg='white', font=self.police)
                    self.countdown_label.pack(pady=10)

                    while countdown_time > 0:
                        self.countdown_label.config(text=f"Temps de discussion : {countdown_time}", bg="#0c5219", fg='white', font=self.police)
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
                self.label_question.config(text=f"Question : {question}", bg="#0c5219", fg='white', font=self.police)
                print('Nouvelle question')
                start_countdown()

            # Mise à jour de la fenêtre
            game_window.update()

        for widget in game_window.winfo_children():
            widget.destroy()
        
        tk.Label(game_window, text="Fin de la partie", bg="#0c5219", fg='white', font=self.police).pack(pady=20)
        tk.Label(game_window, text="Toutes les tâches ont été enregistrées sur le server", bg="#0c5219", fg='white', font=self.police).pack(pady=20)
        tk.Label(game_window, text="Merci pour ta participation !", bg="#0c5219", fg='white', font=self.police).pack(pady=20)

        tk.Button(game_window, text="QUITTER", command=lambda : self.fin_partie(game_window), bg="white", fg='black', font=self.police).pack(padx=20, pady=20)

        ## ATTENTION
        game_window.mainloop()

    
    def fin_partie(self, game_window):
        """
        @brief Méthode déclanchée à la fin de la partie

        @param game_window : Fenêtre de jeu

        Détruit l'interface de vote pour la remplacer par l'écran de fin avec le bouton pour quitter la fenêtre de jeu
        """
        game_window.destroy()
        self.conn.close()

        self.parent.deiconify() # On réaffiche la fenetre principale
        
    # Reinisialiser l'interface
    def clear_window(self):
        """
        @brief Nettoie la fenêtre
        """
        for widget in self.window.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    PlanningPokerApp()
