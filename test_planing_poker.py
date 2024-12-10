import pytest
import socket
import threading
from unittest.mock import Mock, patch, MagicMock
import tkinter as tk
from interfacev2 import HostGame, ClientGame, PlanningPokerApp

# === TESTS POUR HOSTGAME ===

def test_get_ip_address():
    host = HostGame()
    ip = host.get_ip_address()
    assert isinstance(ip, str)
    assert ip.count('.') == 3  # Simple vérification que c'est une IP

def test_host_start_server_thread():
    host = HostGame()
    with patch('socket.socket') as mock_socket:
        mock_server = Mock()
        mock_socket.return_value = mock_server

        # Démarrage du thread serveur
        host.start_server_thread()
        threading.Event().wait(0.1)  # Attendre brièvement pour le thread

        mock_server.bind.assert_called_with((host.IP, 16383))
        mock_server.listen.assert_called_once()

def test_broadcast_pseudos():
    host = HostGame()
    with patch.object(host, 'clients', [Mock(), Mock()]) as mock_clients:
        host.pseudo_list = ['Alice', 'Bob']
        host.broadcast_pseudos()

        for client in mock_clients:
            client.sendall.assert_called_with(b'Alice;Bob')

# === TESTS POUR CLIENTGAME ===

# Les patchs servent à empecher l'ouverture de fenetres réelles pendant le test puisqu'elles posent probleme

@patch('tkinter.Tk', MagicMock())   # On utilsie donc des Mock pour simuler les entrées utilisateurs comme le texte par exemple
@patch('tkinter.Entry', MagicMock())
def test_client_connection():
    with patch('socket.socket') as mock_socket:
        mock_server_conn = Mock()
        mock_socket.return_value = mock_server_conn

        client = ClientGame()
        client.entry_ip.get = Mock(return_value='127.0.0.1')
        client.entry_pseudo.get = Mock(return_value='Alice')
        
        client.connect_to_server()
        mock_server_conn.connect.assert_called_with(('127.0.0.1', 16383))
        mock_server_conn.sendall.assert_called_with(b'Alice')

@patch('tkinter.Tk', MagicMock())
@patch('tkinter.Entry', MagicMock())
def test_client_listen_to_server():
    with patch('socket.socket') as mock_socket:
        mock_conn = Mock()
        mock_conn.recv = Mock(side_effect=[b'Alice;Bob', b'@@START@@'])
        mock_socket.return_value = mock_conn

        client = ClientGame()
        client.conn = mock_conn

        client.listen_to_server()
        threading.Event().wait(0.1)

        # Vérifier que le socket reçoit les bonnes données
        assert mock_conn.recv.call_count >= 2

# === TEST POUR PLANNINGPOKERAPP ===

@patch('tkinter.Tk', MagicMock())
def test_setup_main_menu():
    app = PlanningPokerApp()
    assert app.main is not None

@patch('tkinter.Tk', MagicMock())
def test_clear_window():
    app = PlanningPokerApp()
    app.main.winfo_children = Mock(return_value=[Mock()])
    app.clear_window()
    app.main.winfo_children.assert_called()

# === MOCK POUR SIMULER UNE PARTIE COMPLETE ===

@patch('tkinter.Tk', MagicMock())
def test_full_game_flow():
    with patch('socket.socket') as mock_socket:
        mock_host_conn = Mock()
        mock_client_conn = Mock()

        # Mock des sockets serveur et client
        mock_socket.side_effect = [mock_host_conn, mock_client_conn]

        # Hôte lance le serveur
        host = HostGame()
        host.start_server_thread()

        # Client se connecte
        client = ClientGame()
        client.conn = mock_client_conn
        client.conn.sendall = Mock()
        client.conn.recv = Mock(side_effect=[b'@@START@@'])

        host.handle_client(mock_client_conn)
        assert len(host.clients) == 1
        
        host.start_game()
        client.listen_to_server()

        mock_client_conn.sendall.assert_called()
        mock_client_conn.recv.assert_called()


if __name__ == "__main__":
    pytest.main()
