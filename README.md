![banner](screenshots/banner.png)

Ce projet à été réalisé dans le cadre du cours de CAPI (Conception Agile de Projet Informatique), dans le but de nous apprendre les principales techniques de gestion de développement de projet informatique.
L'application réalisée est une application connue dans ce milieu, le Planning Poker.

---

## Table des matières

1. [Aperçu du Projet](#aperçu-du-projet)
2. [Fonctionnalités](#fonctionnalités)
3. [Installation](#installation)
4. [Utilisation](#utilisation)
5. [Considérations](#considérations)

---

## Aperçu du Projet

Ajoute une capture d'écran ou une courte démo du projet ici pour donner une idée claire de ce qu'il fait.

---

## Fonctionnalités

- Charger un backlog 
- Organiser et participer à des parties de Planning Poker
- Générer un backlog avec les difficultés estimées
- Parties en local (sur le même réseau)
- Nombre de joueurs illimités
- Partie hôte : fonctionne comme un server : logs, résultats, avancement de la partie...
  
---

## Installation

Suivez les intstructions suivantes affin d'installer l'application sur votre machine.

```bash
# Clonez le repo
$ git clone https://github.com/EliasBaroudi/projet-conception

# Accédez au dossier du projet
$ cd projet-conception

# Installez les dépendances (conseillé de le faire dans un environnement créé au préalable)
$ pip install -r requirements.txt
```

## Utilisation

Il est conseillé pour un test sur la même machine d'avoir un terminal pour simuler l'hôte et un autre pour simuler un joueur

- Lancement de l'application :
```bash
# Exemple d'exécution du projet
$ cd src/
$ python .\interfacev6
```

- Utilisation de l'interface :

**🎮 L'écran d'accueil**  
Votre point d'entrée dans l'application où vous pouvez choisir entre héberger une nouvelle partie (HOST) ou rejoindre une partie existante (JOIN).

<img src="screenshots/main.png" alt="Menu principal" width="300"/>

### Mode Hôte

**🎲 Configuration de la partie**  
En tant qu'hôte, vous pourrez configurer tous les paramètres de votre session :
- Sélection du fichier de backlog
- Paramétrage des temps de discussion et de vote
- Configuration du mode de jeu
- Lancement de la partie une fois l'équipe au complet

<img src="screenshots/host.png" alt="Interface hôte" width="300"/>

**📊 Console de supervision**  
Un tableau de bord complet pour suivre votre session en temps réel :
- Visualisation de la question en cours
- Suivi de l'avancement de la partie
- Monitoring des votes reçus
- Vérification des conditions de victoire

<img src="screenshots/console.png" alt="Console hôte" width="300"/>

### Mode Joueur

**🔑 Connexion à la partie**  
Rejoignez facilement une session en cours :
- Entrez l'IP de l'hôte
- Choisissez votre nom d'utilisateur
- Connectez-vous à la partie

**⌛ Salle d'attente**  
Préparez-vous au démarrage de la session :
- Visualisez les autres participants en temps réel
- Attendez le signal de l'hôte pour commencer

<img src="screenshots/waiting.png" alt="Salle d'attente" width="300"/>


**🎯 Interface de jeu**  
Participez activement à l'estimation des tâches :
- Consultez la question/tâche actuelle
- Sélectionnez votre carte de vote
- Gardez un œil sur le temps restant

<img src="screenshots/play.png" alt="Interface de jeu" width="300"/>

**🗣️ Interface de discussion**  
Il est temps d'en parler !
- Consultez les votes des autres joueurs
- Gardez un œil sur le temps restant

<img src="screenshots/feedback.png" alt="Interface de discussion" width="300"/>

Une fois que la partie est terminée, l'hôte et les joueurs peuvent quitter la fenêtre de jeu et relancer une partie s'ils le souhaitent.

## Considérations : 

Le backlog chargé doit être doté de l'extension .json et sous la forme suivante :
```json
{
    "1": "Créer une interface",
    "2": "Ajouter un bouton",
    "3": "Gérer le backlog"
}
```

Le backlog est sauvegardé dans un fichier nommé 'backlog_output.json' sous la forme suivante :
```json
{
    "Créer une interface": 1,
    "Ajouter un bouton": 1,
    "Gérer le backlog": 2
}
```

Si un utilisateur utilise la carte avec l'icône de tasse à café, la partie s'arrêtera prématurément, sauvegardant l'avancement dans le fichier backlog_output.json
Attention, un nouveau backlog contenant les questions non traitées sera écrit dans un fichier avec le nom backlog.json à côté du script, si un backlog est déjà présent, il sera écrasé.

Le premier tour de la partie sera toujours jugé selon la majorité absolue, laissant l'opportunité aux joueurs de discuter des tâches.

Tous les joueurs disposent d'un temps imparti pour voter, si un joueur ne vote pas, un vote nul (vote 0) est envoyé au server.

