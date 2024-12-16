import pytest
import json
import socket
import threading
import time
from unittest.mock import MagicMock, patch
import tkinter as tk

# Importer les classes du script original
from interfacev4 import PlanningPokerApp, HostGame, ClientGame

# Créer une racine Tkinter mockée pour les tests
def mock_tk_root():
    """
    Crée un mock pour la racine Tkinter pour éviter les interactions graphiques réelles.
    """
    root = MagicMock(spec=tk.Tk)
    root.title = MagicMock()
    root.geometry = MagicMock()
    root.mainloop = MagicMock()
    root.protocol = MagicMock()
    return root

def test_get_ip_address():
    """
    Tester la méthode get_ip_address de HostGame
    Vérifie que l'adresse IP retournée a un format valide
    """
    host_game = HostGame()
    
    # Remplacer la création de la fenêtre Tkinter par un mock
    with patch('tkinter.Tk', return_value=mock_tk_root()):
        ip = host_game.get_ip_address()
    
    # Vérifier le format de l'adresse IP
    assert isinstance(ip, str), "L'IP doit être une chaîne de caractères"
    
    # Validation basique de l'adresse IPv4
    ip_parts = ip.split('.')
    assert len(ip_parts) == 4, "L'IP doit avoir 4 parties"
    
    for part in ip_parts:
        assert part.isdigit(), "Les parties de l'IP doivent être numériques"
        assert 0 <= int(part) <= 255, "Les parties de l'IP doivent être entre 0 et 255"

def test_backlog_loading():
    """
    Tester le chargement du backlog
    """
    # Mocker la racine Tkinter et la boîte de dialogue de fichier
    with patch('tkinter.Tk', return_value=mock_tk_root()), \
         patch('tkinter.filedialog.askopenfilename', return_value='test_backlog.json'):
        
        host_game = HostGame()
        
        # Créer un fichier JSON temporaire pour le test
        test_backlog = {
            "1": "Estimation de la première tâche",
            "2": "Estimation de la deuxième tâche"
        }
        
        with open('test_backlog.json', 'w', encoding='utf-8') as f:
            json.dump(test_backlog, f)
        
        host_game.parcourir()
        
        assert hasattr(host_game, 'backlog'), "Le backlog doit être chargé"
        assert host_game.backlog == test_backlog, "Le contenu du backlog doit correspondre aux données de test"

def test_client_connection():
    """
    Tester le processus de connexion du client
    C'est un test simulé car on ne peut pas créer de connexions réseau réelles dans un test unitaire
    """
    # Mocker la racine Tkinter
    with patch('tkinter.Tk', return_value=mock_tk_root()):
        client_game = ClientGame()
        
        # Mocker la connexion socket
        with patch('socket.socket') as mock_socket:
            # Simuler une connexion réussie
            mock_instance = mock_socket.return_value
            mock_instance.connect.return_value = None
            
            # Configurer les entrées de test
            client_game.entry_ip = MagicMock()
            client_game.entry_ip.get.return_value = '127.0.0.1'
            
            client_game.entry_pseudo = MagicMock()
            client_game.entry_pseudo.get.return_value = 'UtilisateurTest'
            
            # Mocker la méthode de connexion
            with patch.object(client_game, 'setup_waiting_interface') as mock_waiting:
                client_game.connect_to_server()
                
                # Vérifier les tentatives de connexion
                mock_socket.assert_called_once()
                mock_instance.connect.assert_called_once_with(('127.0.0.1', 16383))
                mock_waiting.assert_called_once()

def test_vote_processing():
    """
    Tester la logique de traitement des votes
    """
    # Mocker la racine Tkinter
    with patch('tkinter.Tk', return_value=mock_tk_root()):
        host_game = HostGame()
        
        # Simuler des votes avec des valeurs de chaînes
        test_votes = [
            ["Utilisateur1", "5"],
            ["Utilisateur2", "8"],
            ["Utilisateur3", "5"]
        ]
        
        # Mocker les clients pour qu'ils retournent des chaînes de votes
        mock_clients = []
        for user, vote in test_votes:
            mock_client = MagicMock()
            mock_client.recv.return_value = f"{user};{vote}".encode()
            mock_clients.append(mock_client)
        
        host_game.clients = mock_clients
        host_game.full_list = test_votes
        host_game.votes = [vote[1] for vote in test_votes]
        
        # Fenêtre de jeu mockée pour la méthode collect_votes
        mock_game_window = MagicMock()
        
        # Tester différents modes
        test_modes = [
            'Moyenne',
            'Majorité absolue', 
            'Majorité relative'
        ]
        
        for mode in test_modes:
            host_game.mode = mode
            
            # Mocker la réception socket pour retourner les votes prédéfinis
            with patch('socket.socket.recv', side_effect=[f"{user};{vote}".encode() for user, vote in test_votes]):
                try:
                    host_game.collect_votes(mock_game_window)
                except Exception as e:
                    pytest.fail(f"La collecte des votes a échoué pour le mode {mode} : {e}")
                
def test_configuration_initialization():
    """
    Tester l'initialisation de la configuration de l'application
    """
    # Mocker la racine Tkinter
    with patch('tkinter.Tk', return_value=mock_tk_root()):
        app = PlanningPokerApp()
        
        # Vérifier les propriétés de base (mockées)
        assert hasattr(app, 'main'), "L'application doit avoir une fenêtre principale"
        assert hasattr(app, 'PORT'), "L'application doit avoir un attribut PORT"

def test_server_initialization():
    """
    Tester l'initialisation du serveur dans HostGame
    """
    # Mocker la racine Tkinter
    with patch('tkinter.Tk', return_value=mock_tk_root()):
        host_game = HostGame()
        
        assert hasattr(host_game, 'PORT'), "L'hôte doit avoir un attribut PORT"
        assert host_game.PORT == 16383, "Le port par défaut doit être 16383"
        assert hasattr(host_game, 'clients'), "L'hôte doit avoir une liste de clients"
        assert len(host_game.clients) == 0, "La liste des clients doit être initialement vide"

if __name__ == '__main__':
    pytest.main()