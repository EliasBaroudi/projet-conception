import pytest
import json
import socket
import threading
import time
from unittest.mock import MagicMock, patch

# Import the classes from the original script
from interfacev4 import PlanningPokerApp, HostGame, ClientGame

def test_get_ip_address():
    """
    Test the get_ip_address method of HostGame
    Ensures it returns a valid IP address format
    """
    host_game = HostGame()
    ip = host_game.get_ip_address()
    
    # Check IP address format
    assert isinstance(ip, str), "IP should be a string"
    
    # Basic IP address validation (IPv4)
    ip_parts = ip.split('.')
    assert len(ip_parts) == 4, "IP should have 4 parts"
    
    for part in ip_parts:
        assert part.isdigit(), "IP parts should be numeric"
        assert 0 <= int(part) <= 255, "IP parts should be between 0 and 255"

def test_backlog_loading():
    """
    Test the backlog loading functionality
    """
    host_game = HostGame()
    
    # Create a temporary JSON file for testing
    test_backlog = {
        "1": "First task estimation",
        "2": "Second task estimation"
    }
    
    with patch('tkinter.filedialog.askopenfilename', return_value='test_backlog.json'):
        with open('test_backlog.json', 'w', encoding='utf-8') as f:
            json.dump(test_backlog, f)
        
        host_game.parcourir()
        
        assert hasattr(host_game, 'backlog'), "Backlog should be loaded"
        assert host_game.backlog == test_backlog, "Backlog content should match test data"

def test_client_connection():
    """
    Test client connection process
    This is a mock test since we can't create actual network connections in a unit test
    """
    client_game = ClientGame()
    
    # Mock socket connection
    with patch('socket.socket') as mock_socket:
        # Simulate successful connection
        mock_instance = mock_socket.return_value
        mock_instance.connect.return_value = None
        
        # Set up test inputs
        client_game.entry_ip = MagicMock()
        client_game.entry_ip.get.return_value = '127.0.0.1'
        
        client_game.entry_pseudo = MagicMock()
        client_game.entry_pseudo.get.return_value = 'TestUser'
        
        # Mock the connection method
        with patch.object(client_game, 'setup_waiting_interface') as mock_waiting:
            client_game.connect_to_server()
            
            # Verify connection attempts
            mock_socket.assert_called_once()
            mock_instance.connect.assert_called_once_with(('127.0.0.1', 16383))
            mock_waiting.assert_called_once()

def test_vote_processing():
    """
    Test vote processing logic
    """
    host_game = HostGame()
    
    # Simulate votes
    test_votes = [
        ["User1", "5"],
        ["User2", "8"],
        ["User3", "5"]
    ]
    
    host_game.clients = [MagicMock() for _ in range(len(test_votes))]
    host_game.full_list = test_votes
    host_game.votes = [vote[1] for vote in test_votes]
    
    # Mocked game window for collect_votes method
    mock_game_window = MagicMock()
    
    # Test different modes
    test_modes = [
        ('Moyenne', True),
        ('Majorité absolue', True),
        ('Majorité relative', True)
    ]
    
    for mode, _ in test_modes:
        host_game.mode = mode
        
        # We can't directly test the result, but we can check if the method runs without error
        try:
            host_game.collect_votes(mock_game_window)
        except Exception as e:
            pytest.fail(f"Collect votes failed for mode {mode}: {e}")

def test_configuration_initialization():
    """
    Test initial configuration of the app
    """
    # Use patch to prevent actual window creation
    with patch('tkinter.Tk'):
        app = PlanningPokerApp()
        
        # Check basic properties (mocked)
        assert hasattr(app, 'main'), "App should have a main window"
        assert hasattr(app, 'PORT'), "App should have a PORT attribute"

def test_server_initialization():
    """
    Test server initialization in HostGame
    """
    host_game = HostGame()
    
    assert hasattr(host_game, 'PORT'), "Host should have a PORT attribute"
    assert host_game.PORT == 16383, "Default port should be 16383"
    assert hasattr(host_game, 'clients'), "Host should have a clients list"
    assert len(host_game.clients) == 0, "Clients list should initially be empty"

if __name__ == '__main__':
    pytest.main()