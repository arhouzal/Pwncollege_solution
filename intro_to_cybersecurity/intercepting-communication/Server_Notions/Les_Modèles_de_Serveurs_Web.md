# Les Modèles de Serveurs Web - Guide Complet

Guide détaillé sur tous les modèles de traitement des connexions côté serveur avec code complet, explications et comparaisons.

---

## Table des matières

1. [Introduction](#introduction)
2. [Modèle 1 : Sequential Server](#modèle-1--sequential-server)
3. [Modèle 2 : Forking Server](#modèle-2--forking-server)
4. [Modèle 3 : Threading Server](#modèle-3--threading-server)
5. [Modèle 4 : Thread Pool Server](#modèle-4--thread-pool-server)
6. [Modèle 5 : Async/Event-Driven Server](#modèle-5--asyncevent-driven-server)
7. [Comparaison des modèles](#comparaison-des-modèles)
8. [Vulnérabilités DoS par modèle](#vulnérabilités-dos-par-modèle)
9. [Cas d'usage réels](#cas-dusage-réels)

---

## Introduction

### Qu'est-ce qu'un serveur ?

Un serveur est un programme qui :

```
1. Écoute sur un port
2. Accepte les connexions des clients
3. Traite les requêtes
4. Envoie les réponses
5. Ferme la connexion (ou réutilise)
```

### Le problème : Comment traiter PLUSIEURS clients ?

```
Scénario simple : 1 client
─────────────────────────
Client → Serveur → Traite → Répond → Fin
[OK, pas de problème]

Scénario réel : 1000 clients
──────────────────────────────
Client 1 → Serveur → Traite (5 sec) → [Autres clients attendent !]
Client 2 → Attend...
Client 3 → Attend...
...
Client 1000 → Attend...

Comment faire pour que le serveur traite plusieurs clients EN MÊME TEMPS ?
C'est là que les modèles entrent en jeu !
```

---

## Modèle 1 : Sequential Server

### Concept

**Sequential** = Traiter les clients **UN PAR UN** dans l'ordre

```python
while True:
    client1 = accept()      # Accepte client 1
    traite(client1)         # Traite client 1 (bloqué 5 sec)
    close(client1)
    
    client2 = accept()      # Accepte client 2 (après client 1)
    traite(client2)         # Traite client 2 (bloqué 5 sec)
    close(client2)
    
    # Etc...
```

### Code complet avec explications

```python
#!/usr/bin/env python3
"""
Sequential Server - Serveur Séquentiel
Traite UN client à la fois
"""

import socket
import time

def handle_client(client_socket, client_address):
    """
    Traite un client
    
    Args:
        client_socket: Socket du client
        client_address: Adresse du client (IP, port)
    """
    print(f"[*] Handling client: {client_address}")
    
    try:
        # Recevoir les données du client
        data = client_socket.recv(1024)  # ◄─── Bloque ici jusqu'à recevoir
        
        if data:
            print(f"[+] Reçu de {client_address}: {data.decode()}")
            
            # Simuler du traitement (5 secondes)
            print(f"[*] Traitement de {client_address} (5 sec)...")
            time.sleep(5)  # ◄─── BLOQUE pendant 5 secondes
            
            # Envoyer une réponse
            response = b"Hello from Sequential Server!\n"
            client_socket.send(response)
            print(f"[+] Réponse envoyée à {client_address}")
    
    except Exception as e:
        print(f"[-] Erreur avec {client_address}: {e}")
    
    finally:
        # Fermer la connexion
        client_socket.close()
        print(f"[*] Connexion fermée avec {client_address}")


def main():
    """Fonction principale du serveur séquentiel"""
    
    # Créer un socket serveur
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 31337))  # Écouter sur port 31337
    server_socket.listen(1)  # ◄─── Backlog = 1 (un client en attente max)
    
    print("[*] Sequential Server lancé sur le port 31337")
    print("[*] Traitement UN CLIENT À LA FOIS")
    print("[*] Autres clients attendent...")
    
    try:
        while True:
            # Accepter une connexion (BLOQUE jusqu'à connexion)
            print("\n[*] En attente de connexion...")
            client_socket, client_address = server_socket.accept()
            # ◄─── Bloque ici jusqu'à un client se connecte
            
            print(f"[+] Client connecté: {client_address}")
            
            # Traiter le client (UNI PAR UN)
            handle_client(client_socket, client_address)
            
            # Après traitement, retour à accept() pour le suivant
            print("[*] Prêt pour le prochain client")
    
    except KeyboardInterrupt:
        print("\n[*] Arrêt du serveur")
    
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
```

### Exécution et flux

```bash
# Terminal 1: Lancer le serveur
python3 sequential_server.py

# Output:
# [*] Sequential Server lancé sur le port 31337
# [*] Traitement UN CLIENT À LA FOIS
# [*] En attente de connexion...

# Terminal 2: Client 1
nc localhost 31337
# Envoyer: Hello 1
# Attendre 5 secondes
# Réponse: Hello from Sequential Server!

# Pendant ce temps, Terminal 3: Client 2
nc localhost 31337
# ⏳ ATTEND que Client 1 finisse (5 sec)
# Puis reçoit sa réponse après que Client 1 a fini
```

### Diagramme du flux

```
Temps:  0s      1s      2s      3s      4s      5s      6s      7s      8s      9s      10s

Client 1: ▓▓▓▓▓▓▓▓▓▓ (traité 5 sec) ▓▓▓▓▓▓▓▓▓▓
                      ↑
                    Ferme

Client 2:                          ░░░░░░░░░░ (traité 5 sec) ░░░░░░░░░░
                                   ↑                          ↑
                                  Accepté                   Ferme

Client 3:                                                           ▒▒▒▒▒▒▒▒▒▒
                                                                    ↑
                                                                  Accepté

Serveur: [Accept] [Handle C1] [Accept] [Handle C2] [Accept] [Handle C3]
         └──0s──┘ └──5sec───┘ └──5sec──┘ └──5sec──┘ └──5sec──┘

Résultat: Très lent ! Sequential !
```

### Caractéristiques clés

```python
# Listener backlog
server_socket.listen(1)  # ◄─── Seulement 1 client peut attendre
                              # Les autres sont rejetés !

# Blocage
client_socket.recv(1024)  # ◄─── Bloque jusqu'à données
time.sleep(5)             # ◄─── Bloque pendant traitement
```

### Avantages ✅

```
✅ Très simple à comprendre
✅ Facile à déboguer
✅ Pas de concurrence = pas de bugs de concurrence
✅ Très peu de ressources (1 processus, 1 thread)
✅ Déterministe (ordre garanti)
```

### Inconvénients ❌

```
❌ Très LENT - un client = tous attendent
❌ Un client slow = tout le monde slow
❌ Pas scalable du tout
❌ Pas adapté pour 10+ clients simultanés
❌ Timeout n'aide pas (attend toujours le même client)
```

### Cas d'usage

```
✓ Scripts simples
✓ Tests unitaires
✓ Educational (apprendre)
✓ Services internes (1-2 clients max)
✗ Jamais pour un serveur web réel
```

### Vulnérabilité DoS

```
TRÈS VULNÉRABLE à SlowLoris !

Attaquant:
├─ Se connecte
├─ Reste connecté sans rien envoyer
├─ Serveur attend données (bloqué)
├─ Autres clients ne peuvent rien faire
└─ Serveur complètement down

Exemple:
for i in range(10):
    s = socket.socket()
    s.connect(("localhost", 31337))
    # Juste la garder ouverte, rien envoyer
    # Serveur est bloqué !
```

---

## Modèle 2 : Forking Server

### Concept

**Forking** = Créer un nouveau **processus** pour chaque client

```python
while True:
    client1 = accept()      # Accepte client 1
    if fork() == 0:         # Processus enfant
        traite(client1)     # Traite client 1 (peut être bloqué)
        exit()
    else:                   # Processus parent
        close(client1)      # Parent ferme aussi
        # Continue à accept() pour client 2
```

**Résultat :**
```
Parent → Attend nouvelle connexion
Enfant 1 → Traite Client 1
Enfant 2 → Traite Client 2
Enfant 3 → Traite Client 3
...
Tout EN PARALLÈLE !
```

### Code complet avec explications

```python
#!/usr/bin/env python3
"""
Forking Server - Serveur avec Fork
Crée un nouveau processus pour chaque client
"""

import socket
import os
import time
import signal
import sys

def handle_client(client_socket, client_address, process_id):
    """
    Traite un client dans un processus enfant
    
    Args:
        client_socket: Socket du client
        client_address: Adresse du client
        process_id: ID du processus (pour logging)
    """
    print(f"[Processus {process_id}] Traitement de {client_address}")
    
    try:
        # Recevoir les données
        data = client_socket.recv(1024)
        
        if data:
            print(f"[Processus {process_id}] Reçu: {data.decode()}")
            
            # Simuler du traitement
            print(f"[Processus {process_id}] Traitement (5 sec)...")
            time.sleep(5)  # ◄─── Ce processus bloque, pas le parent !
            
            # Envoyer réponse
            response = b"Hello from Forking Server!\n"
            client_socket.send(response)
            print(f"[Processus {process_id}] Réponse envoyée")
    
    except Exception as e:
        print(f"[Processus {process_id}] Erreur: {e}")
    
    finally:
        # Enfant se termine
        client_socket.close()
        print(f"[Processus {process_id}] Terminé")
        os._exit(0)  # ◄─── Processus enfant se termine


def handle_sigchld(signum, frame):
    """
    Gestionnaire pour les processus enfants terminés
    Permet de nettoyer les zombies
    """
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
            print(f"[*] Enfant {pid} terminé, nettoyé")
        except OSError:
            break


def main():
    """Fonction principale du serveur fork"""
    
    # Créer un socket serveur
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 31337))
    server_socket.listen(100)  # ◄─── Backlog = 100 clients en attente
    
    print(f"[*] Forking Server lancé (PID: {os.getpid()})")
    print("[*] Chaque client = nouveau processus")
    print("[*] Clients traités EN PARALLÈLE")
    
    # Installer gestionnaire de signaux pour nettoyer les enfants
    signal.signal(signal.SIGCHLD, handle_sigchld)
    
    process_counter = 0
    
    try:
        while True:
            # Accepter une connexion
            print(f"\n[*] En attente de connexion (PID parent: {os.getpid()})...")
            client_socket, client_address = server_socket.accept()
            # ◄─── Parent bloque ici jusqu'à connexion
            
            print(f"[+] Client connecté: {client_address}")
            
            # FORK - Créer processus enfant
            process_counter += 1
            pid = os.fork()
            
            if pid == 0:
                # ◄─── Code du PROCESSUS ENFANT
                print(f"[Enfant {process_counter}] Créé avec PID {os.getpid()}")
                
                # Enfant traite le client
                handle_client(client_socket, client_address, process_counter)
                # ◄─── Enfant se termine après traitement
            
            else:
                # ◄─── Code du PROCESSUS PARENT
                print(f"[Parent] Fork successful (enfant PID: {pid})")
                client_socket.close()  # ◄─── Parent ferme aussi
                # Parent retour à accept() pour le prochain client
    
    except KeyboardInterrupt:
        print("\n[*] Arrêt du serveur")
    
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
```

### Exécution et flux

```bash
# Terminal 1: Lancer le serveur
python3 forking_server.py

# Output:
# [*] Forking Server lancé (PID: 1000)
# [*] Chaque client = nouveau processus
# [*] En attente de connexion...

# Terminal 2: Client 1
nc localhost 31337
# Envoyer: Hello 1
# [Serveur] [+] Client connecté: ...
# [Serveur] [Enfant 1] Créé avec PID 1001
# [Serveur] [Parent] Fork successful
# [Serveur] [*] En attente de connexion... (Parent continue !)

# Terminal 3: Client 2 (IMMÉDIATEMENT - pas d'attente !)
nc localhost 31337
# Envoyer: Hello 2
# [Serveur] [+] Client connecté: ...
# [Serveur] [Enfant 2] Créé avec PID 1002
# [Serveur] [Parent] Fork successful
# [Serveur] [*] En attente de connexion...

# Les deux clients sont traités EN PARALLÈLE !
```

### Diagramme du flux

```
Temps:  0s      1s      2s      3s      4s      5s      6s      7s      8s      9s      10s

Parent: [Accept C1][Fork] [Accept C2][Fork] [Accept C3][Fork] [Accept]
        └─────────┘      └─────────┘      └─────────┘
              ↓                ↓                ↓
        Enfant 1 (PID 1001): ▓▓▓▓▓▓▓▓▓▓ (5 sec) ▓▓▓▓▓▓▓▓▓▓
        
        Enfant 2 (PID 1002):            ░░░░░░░░░░ (5 sec) ░░░░░░░░░░
        
        Enfant 3 (PID 1003):                         ▒▒▒▒▒▒▒▒▒▒

Résultat: PARALLÈLE ! Les clients ne s'attendent pas !
Parent continue d'accepter pendant que les enfants travaillent
```

### Explication du fork()

```python
pid = os.fork()

# fork() retourne :
# pid == 0   → C'est le PROCESSUS ENFANT
#             Je dois traiter le client
#
# pid > 0    → C'est le PROCESSUS PARENT
#             pid contient l'ID de l'enfant
#             Je continue d'accepter les connexions
#
# pid < 0    → Erreur, fork a échoué
```

### Structure mémoire après fork()

```
Avant fork():
┌──────────────────────┐
│ Serveur Parent       │
│ PID: 1000            │
│                      │
│ Variables:           │
│ ├─ server_socket     │
│ ├─ client_socket     │
│ └─ process_counter   │
└──────────────────────┘

Après fork():
┌──────────────────────┐
│ Serveur Parent       │
│ PID: 1000            │
│                      │
│ Variables:           │
│ ├─ server_socket     │
│ ├─ client_socket     │
│ └─ process_counter=2 │
└──────────────────────┘
         │
         │ (COPIE mémoire)
         ↓
┌──────────────────────┐
│ Serveur Enfant       │
│ PID: 1001            │
│                      │
│ Variables:           │
│ ├─ server_socket     │ (copie)
│ ├─ client_socket     │ (copie)
│ └─ process_counter=2 │ (copie)
└──────────────────────┘

Résultat: 2 processus indépendants (avec mémoire copiée)
Parent: continue d'accepter
Enfant: traite le client et se termine
```

### Avantages ✅

```
✅ Parallélisme vrai (OS-level)
✅ Plusieurs clients EN MÊME TEMPS
✅ Un client lent ≠ impacte pas les autres
✅ Processus isolés (crash d'un enfant ≠ tue parent)
✅ Simplement à comprendre (après fork())
```

### Inconvénients ❌

```
❌ Lourd en ressources (1 processus par client = beaucoup mémoire)
❌ Coûteux de créer un processus (fork() est lent)
❌ Context switching lourd entre processus
❌ Limite OS de processus (ulimit -u)
❌ Enfants zombies si pas nettoyé correctement
```

### Gestion des ressources

```python
# Voir la limite de processus
os.getpid()  # Mon PID
os.getppid() # PID du parent
os.getuid()  # UID

# Limiter les processus (dans bash)
# ulimit -u 1000  ◄─── Max 1000 processus
```

### Cas d'usage

```
✓ Apache (mod_prefork) - historique
✓ Vieux serveurs C
✓ Services spécialisés
✗ Pas idéal pour web moderne (trop lourd)
✗ Pas idéal pour 10,000+ connexions simultanées
```

### Vulnérabilité DoS

```
TRÈS VULNÉRABLE à Process Exhaustion !

Attaquant crée 10,000 connexions:
├─ Server fork 10,000 processus
├─ Chacun consomme mémoire
├─ Chacun consomme ressources
├─ Serveur s'écrase ou out-of-memory
└─ Service down

C'EST EXACTEMENT TON CHALLENGE !
```

---

## Modèle 3 : Threading Server

### Concept

**Threading** = Créer un nouveau **thread** pour chaque client

```python
while True:
    client = accept()
    t = threading.Thread(target=traite, args=(client,))
    t.start()  # ◄─── Thread démarre (pas processus)
    # Main continue à accept() pour le suivant
```

**Différence clé avec fork :**
```
Fork:     Processus enfant = copie mémoire complète (lourd)
Thread:   Thread = partage la même mémoire (léger)
```

### Code complet avec explications

```python
#!/usr/bin/env python3
"""
Threading Server - Serveur avec Threads
Crée un nouveau thread pour chaque client
"""

import socket
import threading
import time
from datetime import datetime

class ThreadingServer:
    def __init__(self, host="0.0.0.0", port=31337):
        self.host = host
        self.port = port
        self.server_socket = None
        self.client_counter = 0
        self.lock = threading.Lock()  # ◄─── Verrou pour accès thread-safe
        
    def handle_client(self, client_socket, client_address, thread_id):
        """
        Traite un client dans un thread séparé
        
        Args:
            client_socket: Socket du client
            client_address: Adresse du client
            thread_id: ID du thread
        """
        thread_name = threading.current_thread().name
        print(f"[Thread {thread_id} - {thread_name}] Traitement de {client_address}")
        
        try:
            # Recevoir les données
            data = client_socket.recv(1024)
            
            if data:
                print(f"[Thread {thread_id}] Reçu: {data.decode()}")
                
                # Simuler du traitement
                print(f"[Thread {thread_id}] Traitement (5 sec)...")
                time.sleep(5)  # ◄─── Ce thread bloque, pas les autres !
                
                # Envoyer réponse
                response = b"Hello from Threading Server!\n"
                client_socket.send(response)
                print(f"[Thread {thread_id}] Réponse envoyée")
        
        except Exception as e:
            print(f"[Thread {thread_id}] Erreur: {e}")
        
        finally:
            client_socket.close()
            print(f"[Thread {thread_id}] Terminé")
            
            # Utiliser un verrou pour accès thread-safe
            with self.lock:
                self.client_counter -= 1
                print(f"[*] Clients actifs: {self.client_counter}")
    
    def start(self):
        """Démarrer le serveur"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)  # ◄─── Backlog = 100
        
        print(f"[*] Threading Server lancé sur {self.host}:{self.port}")
        print("[*] Chaque client = nouveau thread")
        print("[*] Threads PARTAGENT la même mémoire (processus)")
        print("[*] Clients traités EN PARALLÈLE")
        
        thread_counter = 0
        
        try:
            while True:
                print(f"\n[*] En attente de connexion...")
                client_socket, client_address = self.server_socket.accept()
                # ◄─── Main thread bloque ici
                
                print(f"[+] Client connecté: {client_address}")
                
                # Incrémenter le compteur (thread-safe)
                with self.lock:
                    self.client_counter += 1
                    thread_counter += 1
                    client_id = thread_counter
                    count = self.client_counter
                
                print(f"[*] Clients actifs: {count}")
                
                # CRÉER UN THREAD pour ce client
                t = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address, client_id),
                    name=f"ClientThread-{client_id}"
                )
                
                # DAEMON = thread se termine quand main se termine
                t.daemon = False  # Attendre la fin du thread
                
                # DÉMARRER LE THREAD
                t.start()  # ◄─── Lance le thread (pas attend sa fin)
                
                # Main continue immédiatement à accept()
                print(f"[*] Main thread ready for next client")
        
        except KeyboardInterrupt:
            print("\n[*] Arrêt du serveur")
        
        finally:
            self.server_socket.close()


def main():
    server = ThreadingServer()
    server.start()


if __name__ == "__main__":
    main()
```

### Exécution et flux

```bash
# Terminal 1: Lancer le serveur
python3 threading_server.py

# Output:
# [*] Threading Server lancé sur 0.0.0.0:31337
# [*] Chaque client = nouveau thread
# [*] En attente de connexion...

# Terminal 2: Client 1
nc localhost 31337
# Envoyer: Hello 1

# Terminal 3: Client 2 (IMMÉDIATEMENT)
nc localhost 31337
# Envoyer: Hello 2

# Output serveur:
# [+] Client connecté: ...
# [Thread 1 - ClientThread-1] Traitement...
# [*] Main thread ready for next client
# [+] Client connecté: ...
# [Thread 2 - ClientThread-2] Traitement...
# [*] Main thread ready for next client

# Les deux traitements EN PARALLÈLE !
```

### Diagramme du flux

```
Processus Principal:

Mémoire PARTAGÉE (1 seul processus)
┌───────────────────────────────────────────────────┐
│                                                   │
│  Main Thread:     [Accept C1] [Accept C2] ...    │
│  ├─────────────────────────────────────────      │
│  │                                                │
│  │  Thread 1: ▓▓▓▓▓▓▓▓▓▓ (5 sec) ▓▓▓▓▓▓▓▓▓▓      │
│  │  ├─────────────────────────────────────       │
│  │  │                                             │
│  │  │  Thread 2:            ░░░░░░░░░░ (5 sec)  │
│  │  │  ├─────────────────────────────────────    │
│  │  │  │                                          │
│  │  │  │  Thread 3:                   ▒▒▒▒▒▒    │
│  │  │  │  └──────────────────────────────       │
│  │  │  │                                          │
│  │  └──┴─ Tous partagent les MÊMES ressources    │
│  │  data, file handles, etc.                     │
│  │                                                │
│  └─ GIL (Global Interpreter Lock) en Python       │
│     ◄─── Seulement 1 thread à la fois !          │
│          (Mais peut alterner rapidement)         │
└───────────────────────────────────────────────────┘

PID: 1000 (un seul processus pour tous les threads)
```

### Avantages ✅

```
✅ Léger (plus léger que fork - threads partagent mémoire)
✅ Parallélisme (même sans Python GIL pour I/O)
✅ Rapide à créer (création thread < création processus)
✅ Partage de ressources facile (même mémoire)
✅ Bon compromis ressources vs parallélisme
```

### Inconvénients ❌

```
❌ Race conditions (threads partagent mémoire)
❌ Synchronisation complexe (verrous, mutex, etc.)
❌ Python GIL limite CPU parallelism
❌ Un bug dans un thread = potentiellement tout le serveur
❌ Debugging plus difficile (concurrence)
```

### Concept clé : Thread-safety

```python
# MAUVAIS - Race condition :
counter = 0  # Variable partagée

def increment():
    global counter
    for i in range(1000000):
        counter += 1  # ◄─── Pas thread-safe !
                      # 2 threads peuvent read/write à la même fois

t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=increment)
t1.start()
t2.start()
t1.join()
t2.join()

# Résultat attendu: 2,000,000
# Résultat réel: ~1,500,000 (varie !)
# Pourquoi? Race condition !


# BON - Thread-safe avec verrou :
counter = 0
lock = threading.Lock()

def increment():
    global counter
    for i in range(1000000):
        with lock:  # ◄─── Critique section (un seul thread)
            counter += 1

# Résultat: 2,000,000 (garanti)
```

### Python GIL (Global Interpreter Lock)

```
GIL = Verrou global qui limite la concurrence en Python

Résultat:
├─ CPU-bound: pas d'amélioration avec threads
│  └─ Les threads alternent (1 à la fois)
│
└─ I/O-bound: amélioration considérable
   └─ Pendant que 1 thread attend I/O
      Les autres continuent
```

### Cas d'usage

```
✓ Serveurs I/O-bound (web, réseau, base de données)
✓ Services modernes (Django, Flask avec gunicorn)
✓ Bon compromis léger/parallèle
✗ CPU-bound (processing lourd) - utiliser multiprocessing
```

### Vulnérabilité DoS

```
MODÉRÉMENT vulnérable

Attaquant crée 10,000 connexions:
├─ 10,000 threads créés
├─ Mais léger (même mémoire)
├─ Pas d'autant de dégâts que fork
├─ Mais certains timeouts peuvent arriver
└─ Dépend de la limite de threads

Moins grave que Process Exhaustion
Mais toujours possible de surcharger
```

---

## Modèle 4 : Thread Pool Server

### Concept

**Thread Pool** = Pré-créer un nombre FIXE de threads et les RÉUTILISER

```
Pool de 10 threads:

Connexion 1 → Thread 1 traite (puis disponible)
Connexion 2 → Thread 2 traite (puis disponible)
...
Connexion 10 → Thread 10 traite (puis disponible)
Connexion 11 → Attend un thread libre
Connexion 12 → Attend un thread libre

Résultat:
├─ Max 10 traitements en parallèle
├─ Max 10 threads (contrôlé)
├─ Pas d'inflation
├─ Scalable et sûr
```

### Code complet avec explications

```python
#!/usr/bin/env python3
"""
Thread Pool Server - Serveur avec Pool de Threads
Utilise un nombre FIXE de threads réutilisables
"""

import socket
import time
from concurrent.futures import ThreadPoolExecutor
import threading

class ThreadPoolServer:
    def __init__(self, host="0.0.0.0", port=31337, max_workers=10):
        """
        Initialiser le serveur avec un pool de threads
        
        Args:
            host: Adresse à écouter
            port: Port à écouter
            max_workers: Nombre MAXIMUM de threads
        """
        self.host = host
        self.port = port
        self.max_workers = max_workers
        self.executor = None  # ◄─── ThreadPoolExecutor
        self.server_socket = None
        self.client_counter = 0
        self.lock = threading.Lock()
        
    def handle_client(self, client_socket, client_address, client_id):
        """
        Traite un client (exécuté dans un thread du pool)
        
        Args:
            client_socket: Socket du client
            client_address: Adresse du client
            client_id: ID du client
        """
        thread_name = threading.current_thread().name
        print(f"[Pool-{thread_name}] Client {client_id} de {client_address}")
        
        try:
            # Recevoir les données
            data = client_socket.recv(1024)
            
            if data:
                print(f"[Pool-{thread_name}] Reçu: {data.decode()}")
                
                # Simuler du traitement
                print(f"[Pool-{thread_name}] Traitement (5 sec)...")
                time.sleep(5)  # ◄─── Thread traite, d'autres restent libres
                
                # Envoyer réponse
                response = b"Hello from Thread Pool Server!\n"
                client_socket.send(response)
                print(f"[Pool-{thread_name}] Réponse envoyée")
        
        except Exception as e:
            print(f"[Pool-{thread_name}] Erreur: {e}")
        
        finally:
            client_socket.close()
            print(f"[Pool-{thread_name}] Terminé, thread disponible pour le prochain")
            
            with self.lock:
                self.client_counter -= 1
    
    def start(self):
        """Démarrer le serveur"""
        # Créer le pool de threads
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_workers,  # ◄─── MAX threads
            thread_name_prefix="WorkerThread"
        )
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(100)
        
        print(f"[*] Thread Pool Server lancé sur {self.host}:{self.port}")
        print(f"[*] Pool size: {self.max_workers} threads (FIXE)")
        print("[*] Threads RÉUTILISÉS pour les clients")
        print("[*] Ressources CONTRÔLÉES")
        
        client_counter = 0
        
        try:
            while True:
                print(f"\n[*] En attente de connexion...")
                client_socket, client_address = self.server_socket.accept()
                # ◄─── Main thread bloque ici
                
                print(f"[+] Client connecté: {client_address}")
                
                # Incrémenter les compteurs
                with self.lock:
                    self.client_counter += 1
                    client_counter += 1
                    active = self.client_counter
                
                print(f"[*] Clients actifs: {active}")
                
                # SOUMETTRE au pool
                self.executor.submit(
                    self.handle_client,
                    client_socket,
                    client_address,
                    client_counter
                )
                # ◄─── Retour IMMÉDIAT (pas attend la fin)
                #      Le pool gère l'exécution
                
                if active > self.max_workers:
                    print(f"[!] Attention: {active} clients, pool size: {self.max_workers}")
                    print(f"[!] {active - self.max_workers} clients attendent")
        
        except KeyboardInterrupt:
            print("\n[*] Arrêt du serveur")
        
        finally:
            self.executor.shutdown(wait=True)  # ◄─── Attendre fin de tous
            self.server_socket.close()


def main():
    # Créer le serveur avec pool de 10 threads
    server = ThreadPoolServer(max_workers=10)
    server.start()


if __name__ == "__main__":
    main()
```

### Exécution et comportement

```bash
# Terminal 1: Lancer le serveur
python3 thread_pool_server.py

# Output:
# [*] Thread Pool Server lancé sur 0.0.0.0:31337
# [*] Pool size: 10 threads (FIXE)
# [*] Threads RÉUTILISÉS pour les clients

# Connections 1-10: Traitement immédiat
# Connections 11+: Attendre que un thread se libère

# Si on lance 100 clients:
# - 10 premiers traités en parallèle
# - 11-100 attendent (ordonnée queue)
# - Au fur et à mesure que threads se libèrent
#   les clients en attente sont traités
```

### Diagramme du flux

```
Pool de 10 threads:

Temps 0-5s:
Client 1 → Thread 1 traite (5 sec)
Client 2 → Thread 2 traite (5 sec)
Client 3 → Thread 3 traite (5 sec)
Client 4 → Thread 4 traite (5 sec)
Client 5 → Thread 5 traite (5 sec)
Client 6 → Thread 6 traite (5 sec)
Client 7 → Thread 7 traite (5 sec)
Client 8 → Thread 8 traite (5 sec)
Client 9 → Thread 9 traite (5 sec)
Client 10 → Thread 10 traite (5 sec)
Client 11 → Queue (attend)
Client 12 → Queue (attend)

Temps 5s:
Thread 1 se libère → Client 11 commence
Thread 2 se libère → Client 12 commence

Résultat:
├─ Max 10 parallèles TOUJOURS
├─ Pas d'inflation de threads
├─ Pas de débordement mémoire
├─ Queue ordonnée (FIFO)
└─ Scalable et sûr
```

### Avantages ✅

```
✅ Ressources CONTRÔLÉES (exactement N threads)
✅ Performance prévisible
✅ Pas d'inflation de threads
✅ Pas de overhead de création/destruction
✅ Excellent compromis ressources/performance
✅ Très utilisé en production
```

### Inconvénients ❌

```
❌ Besoin de tuner max_workers
   └─ Trop bas = attente, faible performance
   └─ Trop haut = mémoire, overhead
❌ Queue peut croître (clients attendent)
❌ Race conditions toujours possibles
```

### Tuning du pool

```python
# Trop petit (3 threads):
ThreadPoolExecutor(max_workers=3)
└─ Serveur lent, beaucoup de clients attendent

# Équilibré (10-20 threads):
ThreadPoolExecutor(max_workers=10)
└─ Bon pour plupart des cas

# Trop gros (1000 threads):
ThreadPoolExecutor(max_workers=1000)
└─ Trop de ressources, overhead

# Règle générale:
max_workers ≈ 2 × nombre_de_CPU_cores
```

### Cas d'usage

```
✓ Serveurs web modernes
✓ APIs REST
✓ Services avec I/O
✓ Production (très utilisé)
✓ Django + gunicorn
✓ Tomcat
```

### Vulnérabilité DoS

```
RÉSISTANT aux attaques DoS !

Attaquant crée 10,000 connexions:
├─ Pool de 10 threads MAX
├─ 10 connexions traitées
├─ 9,990 en queue
├─ Pas de débordement mémoire
├─ Serveur continue de fonctionner
├─ Clients en queue attendent mais pas server crash
└─ Comportement prévisible et stable

Bien plus sûr que les autres modèles !
```

---

## Modèle 5 : Async/Event-Driven Server

### Concept

**Async** = 1 processus, 1 event loop, 0 bloquage

```python
# Pas de threads, pas de processus
# Juste une boucle qui traite les événements

async def main():
    server = await asyncio.start_server(handle_client, "0.0.0.0", 31337)
    await server.serve_forever()  # ◄─── Event loop tourne indéfiniment

# Quand données arrivent → handle_client() s'exécute
# Quand attend I/O → autre chose s'exécute
# Pas de bloquage = très efficace
```

### Concepts clés

#### 1. Coroutine (async def)

```python
async def ma_fonction():
    """Coroutine - peut être suspendue"""
    await asyncio.sleep(5)  # ◄─── Attend SANS bloquer le thread
    return "Fini"

# await = "Attends ce résultat, mais tu peux faire autre chose"
```

#### 2. Event loop (boucle événementielle)

```python
# La boucle tourne continuellement:

while True:
    # 1. Vérifier s'il y a des données
    if data_available():
        traiter_data()
    
    # 2. Vérifier s'il y a des timers
    if timer_done():
        execute_timer()
    
    # 3. Attendre le prochain événement
    # (pas de busy-wait = efficace)
```

#### 3. Await (attendre SANS bloquer)

```python
# BLOQUANT (mauvais en async):
time.sleep(5)  # ◄─── Le thread est bloqué
# Rien d'autre ne peut s'exécuter

# NON-BLOQUANT (bon en async):
await asyncio.sleep(5)  # ◄─── Attend MAIS autres choses peuvent s'exécuter
# La boucle peut traiter d'autres connexions
```

### Code complet avec explications

```python
#!/usr/bin/env python3
"""
Async Server - Serveur Asynchrone avec asyncio
1 processus, 1 event loop, pas de threads
"""

import asyncio
import time

class AsyncServer:
    def __init__(self, host="0.0.0.0", port=31337):
        self.host = host
        self.port = port
        self.client_counter = 0
        self.active_clients = set()
        self.lock = asyncio.Lock()  # ◄─── Lock async (pas threading.Lock)
        
    async def handle_client(self, reader, writer):
        """
        Traite un client ASYNCHRONIQUEMENT
        
        Args:
            reader: StreamReader pour recevoir données
            writer: StreamWriter pour envoyer données
        """
        # Incrémenter le compteur
        async with self.lock:
            self.client_counter += 1
            client_id = self.client_counter
            self.active_clients.add(client_id)
        
        peername = writer.get_extra_info('peername')
        print(f"[Async-{client_id}] Client connecté: {peername}")
        print(f"[Async-{client_id}] Clients actifs: {len(self.active_clients)}")
        
        try:
            # Recevoir les données (NON-BLOQUANT)
            data = await reader.read(1024)  # ◄─── Attend SANS bloquer loop
            # ◄─── Si pas de données, la boucle traite autres clients
            # ◄─── Quand données arrivent, on revient ici
            
            if data:
                message = data.decode()
                print(f"[Async-{client_id}] Reçu: {message}")
                
                # Simuler du traitement ASYNCHRONE
                print(f"[Async-{client_id}] Traitement (5 sec)...")
                
                # IMPORTANT: utiliser await asyncio.sleep()
                # PAS time.sleep() !
                await asyncio.sleep(5)  # ◄─── Attend SANS bloquer
                # ◄─── Pendant ces 5 sec, la boucle peut traiter d'autres
                # ◄─── clients ! Pas de blocage !
                
                # Envoyer réponse (NON-BLOQUANT)
                response = b"Hello from Async Server!\n"
                writer.write(response)
                await writer.drain()  # ◄─── Attends d'envoyer (non-bloquant)
                print(f"[Async-{client_id}] Réponse envoyée")
        
        except asyncio.TimeoutError:
            print(f"[Async-{client_id}] Timeout")
        
        except Exception as e:
            print(f"[Async-{client_id}] Erreur: {e}")
        
        finally:
            writer.close()
            await writer.wait_closed()  # ◄─── Attendre la fermeture
            
            async with self.lock:
                self.active_clients.discard(client_id)
            
            print(f"[Async-{client_id}] Terminé")
    
    async def start(self):
        """Démarrer le serveur async"""
        # Créer le serveur
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        # ◄─── asyncio.start_server() crée le serveur
        # ◄─── handle_client() s'appelle pour chaque connexion
        
        addr = server.sockets[0].getsockname()
        print(f"[*] Async Server lancé sur {addr[0]}:{addr[1]}")
        print("[*] 1 processus, 1 event loop, pas de threads")
        print("[*] Scalabilité extrême (10,000+ connexions facile)")
        
        # Servir indéfiniment
        async with server:
            await server.serve_forever()  # ◄─── La boucle tourne
            # ◄─── handle_client() s'appelle à chaque événement


async def main():
    """Point d'entrée principal"""
    server = AsyncServer()
    await server.start()


if __name__ == "__main__":
    # Exécuter la boucle d'événements principale
    asyncio.run(main())  # ◄─── Lance la boucle asyncio
```

### Exécution

```bash
# Terminal 1: Lancer le serveur
python3 async_server.py

# Output:
# [*] Async Server lancé sur 0.0.0.0:31337
# [*] 1 processus, 1 event loop, pas de threads
# [*] Scalabilité extrême

# Terminal 2: Client 1 (envoyer avec délai)
nc localhost 31337
# [délai de 0.5s]
# Hello 1
# [Attendre réponse]

# Terminal 3: Client 2 (IMMÉDIATEMENT, pas d'attente !)
nc localhost 31337
# [délai de 0.1s]
# Hello 2
# [Attendre réponse]

# Output serveur:
# [Async-1] Client connecté
# [Async-1] Traitement (5 sec)...
#   [Event loop continue]
# [Async-2] Client connecté
# [Async-2] Traitement (5 sec)...
#   [Event loop continue]
# [après 5 sec]
# [Async-1] Réponse envoyée
# [Async-2] Réponse envoyée

# Les deux traités EN PARALLÈLE SANS THREADS !
```

### Diagramme du flux

```
Event Loop (1 seul processus):

Temps 0s:
├─ Event loop reçoit Client 1
├─ Appelle handle_client(1)
├─ Data n'est pas là → await reader.read()
├─ Event loop continue
│
├─ Event loop reçoit Client 2
├─ Appelle handle_client(2)
├─ Data arrive → traite
├─ Appelle await asyncio.sleep(5)
├─ Event loop continue

Temps 0.1s:
├─ Event loop reçoit données de Client 1
├─ handle_client(1) continue depuis await reader.read()
├─ Appelle await asyncio.sleep(5)
├─ Event loop continue

Temps 1s:
├─ Event loop reçoit Client 3
├─ Appelle handle_client(3)
├─ ...

Résultat:
├─ TOUS traitées EN PARALLÈLE
├─ 1 seul processus
├─ 0 threads
├─ 0 attente
├─ Scalabilité extrême !
```

### Concepts avancés

#### 1. Concurrence vs Parallélisme

```
Threading (Modèle 3):
├─ Concurrence = plusieurs threads PRÉTENDENT s'exécuter en parallèle
├─ Mais OS alterne rapidement entre eux (context switching)
├─ Avec Python GIL = vraiment une à la fois

Async (Modèle 5):
├─ Concurrence COOPÉRATIVE = tâches cèdent volontairement le contrôle
├─ Pas de context switching OS (overhead bas)
├─ Beaucoup plus efficace pour I/O
```

#### 2. Await vs Sleep

```python
# MAUVAIS en async:
time.sleep(5)  # ◄─── Tout la boucle bloque !
# Aucun autre client ne peut être traité

# BON en async:
await asyncio.sleep(5)  # ◄─── Seulement CE await bloque
# La boucle peut traiter d'autres clients
```

#### 3. Gather - Attendre plusieurs coroutines

```python
# Attendre 3 coroutines EN PARALLÈLE
results = await asyncio.gather(
    handle_client_1(),
    handle_client_2(),
    handle_client_3()
)
```

### Avantages ✅

```
✅ Ultra scalable (10,000+ connexions facile)
✅ Ressources minimales (1 processus, 1 thread)
✅ Pas de context switching overhead
✅ Très efficace pour I/O-bound
✅ Moderne et futur-proof
✅ Performance extrême
```

### Inconvénients ❌

```
❌ Code complexe (async/await partout)
❌ Debugging difficile (pas de stack traces clairs)
❌ Besoin de utiliser async libraries (asyncio, aiohttp, etc.)
❌ Pas bon pour CPU-bound (utiliser ProcessPoolExecutor)
❌ Apprentissage difficile
```

### Qui l'utilise

```
✓ Node.js (event-driven par défaut)
✓ Nginx (intérieurement)
✓ Redis (single-threaded event loop)
✓ FastAPI (modern Python)
✓ Go (goroutines = async)
✓ Rust (Tokio = async)
```

### Vulnérabilité DoS

```
TRÈS RÉSISTANT aux attaques DoS !

Attaquant crée 10,000 connexions:
├─ Event loop traite les 10,000 SANS créer threads/processus
├─ Pas de débordement mémoire
├─ Pas de débordement CPU
├─ Serveur continue de fonctionner
└─ Peut même supporter 100,000+ connexions !

La défense est ailleurs (rate limiting applicatif)
```

---

## Comparaison des modèles

### Tableau complet

| Aspect | Sequential | Forking | Threading | Thread Pool | Async |
|--------|-----------|---------|-----------|-------------|-------|
| **Architecture** | 1 process, 1 thread | N processus | 1 process, N threads | 1 process, N threads | 1 process, 1 event loop |
| **Parallélisme** | Aucun ❌ | Oui ✅ | Oui (GIL) | Oui (limité) | Oui ✅ |
| **Ressources** | Très bas | Très haut | Bas-moyen | Contrôlé | Très bas |
| **Création** | N/A | Lent | Rapide | N/A | Ultra rapide |
| **Complexité code** | Simple | Simple | Complexe | Complexe | Très complexe |
| **Scalabilité** | Très basse | Basse | Moyenne | Bonne | Extrême |
| **Max connexions** | ~10 | ~1000 | ~10000 | ~10000 | ~100000+ |
| **Latency** | Élevée | Moyenne | Basse | Basse | Très basse |
| **CPU overhead** | Bas | Moyen-haut | Moyen | Bas | Très bas |
| **DoS Risk** | ⚠️ SlowLoris | ⚠️ Process | ⚠️ Resource | ✅ Bon | ✅ Très bon |

### Graphique de performance

```
Scalabilité:

Async     ████████████████████████████████████ (100,000+)
Thread Pool ███████████████████ (10,000)
Threading ███████████████████ (10,000)
Forking   ████████ (1,000)
Sequential ██ (10)
         └─────────────────────────────────────►
```

### Graphique d'utilisation mémoire

```
Mémoire (100 clients):

Sequential   ▓▓ (très bas)
Async        ▓▓ (très bas)
Thread Pool  ▓▓▓▓ (bas)
Threading    ▓▓▓▓ (bas)
Forking      ▓▓▓▓▓▓▓▓▓▓▓▓▓ (très haut)
            └──────────────────────►
```

---

## Vulnérabilités DoS par modèle

### Sequential Server

**Vulnérabilité :** SlowLoris

```python
# Attaquant:
for i in range(10):
    s = socket.socket()
    s.connect(("localhost", 31337))
    # Reste connecté sans envoyer rien
    # Serveur bloqué sur recv()
    # Tous les autres clients attendent

# Résultat: Service DOWN
```

### Forking Server

**Vulnérabilité :** Process Exhaustion

```python
# Attaquant (TON CHALLENGE 1):
for i in range(10000):
    s = socket.socket()
    s.connect(("localhost", 31337))
    # Serveur fork 10,000 processus
    # Mémoire épuisée
    # Service DOWN

# Résultat: Service DOWN
```

### Threading Server

**Vulnérabilité :** Resource Exhaustion

```python
# Attaquant:
for i in range(100000):
    s = socket.socket()
    s.connect(("localhost", 31337))
    # 100,000 threads créés
    # Serveur peut s'écraser

# Résultat: Possibilité de DOWN
```

### Thread Pool Server

**Défense intégrée :** Limité à max_workers

```python
# Même avec 100,000 connexions:
# Seulement 10 threads traités en parallèle
# 99,990 en queue (attendent)
# Serveur stable, prévisible
# Pas de crash

# Résultat: Stable, performance dégradée mais service UP
```

### Async Server

**Défense intégrée :** Aucune allocation par connexion

```python
# Même avec 100,000 connexions:
# 1 seul processus, 1 event loop
# Pas de threads, pas de processus
# Mémoire par connexion = très basse
# Serveur continue

# Résultat: Stable, peut continuer même avec beaucoup d'attaques
```

---

## Cas d'usage réels

### Apache (Forking)

```
// httpd.conf
<IfModule mpm_prefork_module>
    StartServers 8
    MinSpareServers 5
    MaxSpareServers 20
    MaxRequestWorkers 256  # ◄─── Max processus
</IfModule>

Modèle: Forking
Avantages: Compatible avec modules legacy
Inconvénients: Pas scalable, mémoire haute
```

### Nginx (Async)

```
# nginx.conf
worker_processes auto;  # ◄─── Event-driven par defaut
worker_connections 65536;  # ◄─── Max connexions par worker

Modèle: Async/Event-driven
Avantages: Ultra performant, très scalable
Inconvénients: Pas de modules legacy
```

### Django + Gunicorn (Thread Pool)

```bash
gunicorn --workers 4 --threads 2 --worker-class gthread
#         └─ 4 processus
#                     └─ 2 threads par processus
#                                    └─ Hybrid: thread pool

Modèle: Thread Pool (hybride)
Avantages: Bon compromis, scalable
Inconvénients: Plus lourd qu'async
```

### Node.js (Async)

```javascript
const http = require('http');
const server = http.createServer((req, res) => {
    // Event-driven par défaut
    // Non-bloquant par défaut
});
server.listen(31337);

Modèle: Async/Event-driven
Avantages: Très scalable
Inconvénients: Callback complexity ("callback hell")
```

### Redis (Single-threaded async)

```
Modèle: Single-threaded async event loop
O

Architecture: 1 processus, 1 thread, 1 event loop
Performance: Ultra rapide pour kv operations
Scalabilité: 100,000+ connexions simultanées facile
```

---

## Résumé et recommandations

### Pour débuter

```
✓ Sequential Server
  Comprendre les bases
  Puis apprendre les autres modèles
```

### Pour production web

```
✓ Thread Pool ou Async
  Thread Pool: Facile à déployer, bon perf
  Async: Meilleure perf, plus complexe
```

### Pour ultra-haute scalabilité

```
✓ Async (Nginx, Node.js, FastAPI)
  Minimum de ressources
  Maximum de performance
  Peut supporter 100,000+ connexions
```

### Pour CPU-intensive

```
✓ Process Pool + I/O Async
  Traiter CPU avec processus
  Traiter I/O avec async
  Hybrid approach
```

---

## Conclusion

Les modèles de serveurs sont **fondamentaux** pour comprendre :
- Comment les serveurs web scalent
- Pourquoi Nginx > Apache
- Comment Node.js est si fast
- Vulnérabilités DoS spécifiques
- Trade-offs ressources vs complexité

**Tu as maintenant une compréhension complète** de comment les serveurs traitent les connexions ! 🎉
