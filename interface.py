import tkinter as tk
from tkinter import ttk
import socket
import threading

main = tk.Tk()  # Création de la fenêtre principale
main.title("Planing poker")
main.geometry("1080x720")

def get_ip(): ## Fonction pour récuperer l'ip du client
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # Essaye de se connecter à un hôte externe (par exemple, Google DNS)
        s.connect(('10.254.254.254', 1))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = '127.0.0.1'  # Si aucun réseau n'est disponible, renvoie l'IP de loopback
    
    s.close()
    return ip_address


def clear_main(): ## Fonction qui nettoie la fenêtre main
    for widget in main.winfo_children():
        widget.destroy()  # Détruit chaque widget (ferme la fenêtre)

def host(): ## Fonction qui permet d'heberger une partie
    main.title("Planing poker (Hôte)")
    clear_main()

    IP = get_ip()
    label_ip = tk.Label(main, text=f'Votre ip : {IP}')
    label_desc = tk.Label(main, text="Indiquez votre IP aux autres utilisateurs pour qu'ils puissent se connecter")

    label_ip.pack()
    label_desc.pack()

    tableau = ttk.Treeview(main, columns=("col1"), show="headings")
    tableau.heading('col1', text='Pseudo')

    ## Lancer la connection interface hote ##

    ID = 'server'
    PORT = 16383        # Port à utiliser

    def ecoute():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((IP, PORT))
            s.listen()
            print(f"Serveur en écoute sur {IP}:{PORT}")
            conn, addr = s.accept()
            with conn:
                print(f"Connecté par {addr}")
                data = conn.recv(1024).decode()
                print(type(data))
                data = data.split(';')
                tableau.insert('', 'end', values=(f'{data[1]}'))
                tableau.pack()
    
    #on peut faire un while True jusqu'a ce qu'un bouton soit préssé côté hote pour laisser les connections ouvertes

    #server_socket.accept() bloque le script jusqu'a la prochaine connection
    
    thread = threading.Thread(target=ecoute)
    thread.start()  



            

def client(): ## Fonction qui permet de rejoindre une partie
    main.title("Planing poker (Client)")
    clear_main()

    # Déclaration des variables globales
    global ID 
    global IP
    ID = ''
    IP = ''
    PORT = 16383       # Port utilisé par le serveur

    def connect(): # récuperer les entrées utilisateurs client
        global IP
        IP = text_ip.get()
        global ID
        ID = text_pseudo.get()
        print(ID,IP)
        connection()
        # return IP,ID

    
    label_ip = tk.Label(main, text="IP : ")
    label_ip.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    text_ip = tk.Entry(main) 
    text_ip.grid(row=0, column=1, padx=10, pady=5, sticky="w")

    label_pseudo = tk.Label(main, text= "Pseudo : ")
    label_pseudo.grid(row=1, column=0, padx=10, pady=5, sticky="w")

    text_pseudo = tk.Entry(main)
    text_pseudo.grid(row=1, column=1, padx=10, pady=5, sticky="w")

    btn_valider = tk.Button(main, text=f'Se connecter', command=connect)
    btn_valider.grid(row=2, column=1, padx=10, pady=5)

    ## Lancer la connection interface client ##

    def connection():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
            conn.connect((IP, PORT))
            print(f"Connexion à {IP}:{PORT}")
            while True:
                credentials = IP+';'+ID
                conn.sendall(credentials.encode())

def lan(): # Fonction qui permet de jouer en LAN
    main.title("Planing poker (LAN)")
    clear_main()

    ### Fenêtre connection en LAN ###
    
    btnHost = tk.Button(main, text="Heberger la partie", command=host)
    btnClient = tk.Button(main, text="Rejoindre une partie", command=client)

    btnHost.pack()
    btnClient.pack()

def local(): # Fonction qui permet de jouer en local
    main.title("Planing poker (local)")
    clear_main()

    ### Fenêtre connection en local ###



### Fonctions intermédiaires ###



### Fenêtre principale ###

label = tk.Label(main, text="Hello, Tkinter!")
btnLAN = tk.Button(main, text="Jouer en LAN", command=lan)
btnLOC = tk.Button(main, text="Jouer en Local", command=local)

label.pack()
btnLAN.pack()
btnLOC.pack()  

main.mainloop()
