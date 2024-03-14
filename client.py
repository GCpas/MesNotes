import socket

# Création du socket client
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 12345))  # Adresse IP et port du programme MesNotes

# Envoi du message "est tu la ?"
client_socket.send("est tu la ?".encode())

# Réception de la réponse
response = client_socket.recv(1024).decode()
print("Réponse du serveur :", response)

# Fermeture du socket client
client_socket.close()