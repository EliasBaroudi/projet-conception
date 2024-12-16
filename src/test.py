import pytest
import json
import socket
import threading
import time
import os
import sys
from unittest.mock import MagicMock, patch

# Désactiver l'initialisation Tkinter avant l'import
os.environ['DISPLAY'] = ''
sys.modules['tkinter'] = MagicMock()

# Import des classes du script original
from interfacev6 import PlanningPokerApp, HostGame, ClientGame


def test_get_ip_address():
    """
    Tester la méthode get_ip_address de HostGame
    """
    parent_window_mock = MagicMock()  # Mock de parent_window
    host_game = HostGame(parent_window_mock)  # Passer le mock ici
    ip = host_game.get_ip_address()
    
    # Vérification du format d'IP
    assert isinstance(ip, str), "L'IP doit être une chaîne de caractères"
    
    ip_parts = ip.split('.')
    assert len(ip_parts) == 4, "L'IP doit avoir 4 parties"
    
    for part in ip_parts:
        assert part.isdigit(), "Les parties de l'IP doivent être numériques"
        assert 0 <= int(part) <= 255, "Les parties de l'IP doivent être entre 0 et 255"


def test_backlog_loading(tmp_path):
    """
    Tester le chargement du backlog
    """
    parent_window_mock = MagicMock()  # Mock de parent_window
    host_game = HostGame(parent_window_mock)  # Passer le mock ici
    
    # Créer un fichier JSON temporaire pour le test
    test_backlog = {
        "1": "Estimation de la première tâche",
        "2": "Estimation de la deuxième tâche"
    }
    
    test_file = tmp_path / "test_backlog.json"
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_backlog, f)
    
    # Mocker la méthode de sélection de fichier
    with patch('tkinter.filedialog.askopenfilename', return_value=str(test_file)):
        host_game.parcourir()
    
    assert hasattr(host_game, 'backlog'), "Le backlog doit être chargé"
    assert host_game.backlog == test_backlog, "Le contenu du backlog doit correspondre aux données de test"


def test_client_connection():
    """
    Tester le processus de connexion du client
    """
    parent_window_mock = MagicMock()  # Mock de parent_window
    client_game = ClientGame(parent_window_mock)  # Passer le mock ici
    
    # Mocker les entrées
    client_game.entry_ip = MagicMock()
    client_game.entry_ip.get.return_value = '127.0.0.1'
    
    client_game.entry_pseudo = MagicMock()
    client_game.entry_pseudo.get.return_value = 'UtilisateurTest'
    
    # Mocker la connexion socket et l'interface d'attente
    with patch('socket.socket') as mock_socket, \
         patch.object(client_game, 'setup_waiting_interface'):
        
        mock_instance = mock_socket.return_value
        mock_instance.connect.return_value = None
        
        client_game.connect_to_server()
        
        # Vérifications
        mock_socket.assert_called_once()
        mock_instance.connect.assert_called_once_with(('127.0.0.1', 16383))


def test_vote_processing():
    """
    Tester la logique de traitement des votes
    """
    parent_window_mock = MagicMock()  # Mock de parent_window
    host_game = HostGame(parent_window_mock)  # Passer le mock ici

    # Simuler des votes avec des valeurs réelles
    test_votes = [
        ["Utilisateur1", "5"],
        ["Utilisateur2", "8"],
        ["Utilisateur3", "5"]
    ]

    # Préparer le contexte de test
    # Simuler les clients avec MagicMock configurés
    host_game.clients = []
    for vote in test_votes:
        mock_client = MagicMock()
        mock_client.recv.return_value.decode.return_value = f"{vote[0]};{vote[1]}"
        host_game.clients.append(mock_client)

    # Simuler la liste de votes attendus
    host_game.full_list = []
    host_game.votes = []

    # Fenêtre de jeu mockée
    mock_game_window = MagicMock()

    # Tester différents modes
    for mode in ['Moyenne', 'Majorité absolue', 'Majorité relative']:
        host_game.mode = mode

        try:
            # Appelez la méthode collect_votes avec des valeurs réelles uniquement
            host_game.collect_votes(mock_game_window)
        except Exception as e:
            pytest.fail(f"Échec de la collecte des votes pour le mode {mode} : {e}")


def test_server_initialization():
    """
    Tester l'initialisation du serveur
    """
    parent_window_mock = MagicMock()  # Mock de parent_window
    host_game = HostGame(parent_window_mock)  # Passer le mock ici
    
    assert hasattr(host_game, 'PORT'), "L'hôte doit avoir un attribut PORT"
    assert host_game.PORT == 16383, "Le port par défaut doit être 16383"
    assert hasattr(host_game, 'clients'), "L'hôte doit avoir une liste de clients"
    assert len(host_game.clients) == 0, "La liste des clients doit être initialement vide"


if __name__ == '__main__':
    pytest.main()
