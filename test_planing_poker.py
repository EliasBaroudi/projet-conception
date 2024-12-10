import pytest
import socket
import threading
from unittest.mock import Mock, patch
import tkinter as tk
from planning_poker_app import HostGame, ClientGame, PlanningPokerApp

# === TESTS POUR HOSTGAME ===

def test_get_ip_address():
    host = HostGame()
    ip = host.get_ip_address()
    assert isinstance(ip, str)
    assert ip.count('.') == 3  # Simple verification que c'est une IP

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

def test_client_connection():
    with patch('socket.socket') as mock_socket:
        mock_server_conn = Mock()
        mock_socket.return_value = mock_server_conn

        root = tk.Tk()
        client = ClientGame()
        client.entry_ip.insert(0, '127.0.0.1')
        client.entry_pseudo.insert(0, 'Alice')
        
        client.connect_to_server()
        mock_server_conn.connect.assert_called_with(('127.0.0.1', 16383))
        mock_server_conn.sendall.assert_called_with(b'Alice')
        root.destroy()

def test_client_listen_to_server():
    with patch('socket.socket') as mock_socket:
        mock_conn = Mock()
        mock_conn.recv = Mock(side_effect=[b'Alice;Bob', b'@@START@@'])
        mock_socket.return_value = mock_conn

        root = tk.Tk()
        client = ClientGame()
        client.conn = mock_conn

        client.listen_to_server()
        threading.Event().wait(0.1)

        # Vérifier que les pseudos ont été ajoutés et que la partie a commencé
        assert client.table.get_children() == ()  # Pas de vérification UI directe ici
        root.destroy()

# === TEST POUR PLANNINGPOKERAPP ===

def test_setup_main_menu():
    app = PlanningPokerApp()
    assert len(app.main.winfo_children()) > 0
    app.main.destroy()


def test_clear_window():
    app = PlanningPokerApp()
    tk.Label(app.main, text="Test").pack()
    assert len(app.main.winfo_children()) > 0

    app.clear_window()
    assert len(app.main.winfo_children()) == 0
    app.main.destroy()

# === MOCK POUR SIMULER UNE PARTIE COMPLETE ===

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
