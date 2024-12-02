""""
Tkinter ne supporte pas fichiers svg donc utiliser cairosvg pour mettre en PNG
pip install cairosvg
exemple de code pour la carte 13

from PIL import Image, ImageTk
import tkinter as tk

main = tk.Tk()
main.title("Image SVG dans Tkinter")
main.geometry("400x400")

# Charger l'image PNG
img = Image.open("cartes_13.png")
img_tk = ImageTk.PhotoImage(img)

# Afficher l'image
label_image = tk.Label(main, image=img_tk)
label_image.pack()

main.mainloop()



ntégrer l'image dans votre application existante
Voici comment intégrer l'image dans une section de votre interface Tkinter :

Exemple pour afficher une carte en tant qu'image dans le mode local :
def local():
    main.title("Planing poker (local)")
    clear_main()

    label_info = tk.Label(main, text="Jouez en mode local : deux joueurs")
    label_info.pack()

    # Charger l'image PNG de la carte
    img = Image.open("cartes_13.png")
    img_tk = ImageTk.PhotoImage(img)

    # Afficher l'image dans un Label
    label_image = tk.Label(main, image=img_tk)
    label_image.image = img_tk  # Référence pour éviter que l'image soit libérée
    label_image.pack()

    # Exemple d'entrée utilisateur
    label_player1 = tk.Label(main, text="Joueur 1 : ")
    entry_player1 = tk.Entry(main)

    label_player1.pack()
    entry_player1.pack()



    Si vous souhaitez afficher plusieurs cartes (par exemple pour un jeu), vous pouvez les organiser dans un Canvas ou une grille Tkinter.

Exemple avec plusieurs images :

def afficher_cartes():
    cartes = ["cartes_13.png", "autre_carte.png"]  # Liste des fichiers PNG
    for i, carte in enumerate(cartes):
        img = Image.open(carte)
        img_tk = ImageTk.PhotoImage(img)
        label = tk.Label(main, image=img_tk)
        label.image = img_tk  # Conserver la référence
        label.grid(row=0, column=i)  # Positionner dans une grille

afficher_cartes()


ajouter un chronometre pendant le debat et un chronomètre pendant le vote
"""
