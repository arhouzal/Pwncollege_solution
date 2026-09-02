# Défis de Firewall Linux - Documentation Complète

Documentation des solutions pour les 3 défis de configuration de firewall avec `iptables`.

---

## Table des matières
1. [Défi 1 : Bloquer tout le trafic entrant sur un port](#défi-1--bloquer-tout-le-trafic-entrant-sur-un-port)
2. [Défi 2 : Bloquer sélectivement le trafic entrant](#défi-2--bloquer-sélectivement-le-trafic-entrant)
3. [Défi 3 : Autoriser le trafic sortant et établir une connexion](#défi-3--autoriser-le-trafic-sortant-et-établir-une-connexion)

---

## Concepts préalables

### Chaînes iptables principales

- **INPUT** : Trafic entrant vers la machine (ce qu'elle REÇOIT)
- **OUTPUT** : Trafic sortant depuis la machine (ce qu'elle ENVOIE)
- **FORWARD** : Trafic qui traverse la machine (routage)

### Actions possibles

- **ACCEPT** : Laisser passer le paquet ✅
- **DROP** : Bloquer silencieusement (pas de réponse)
- **REJECT** : Bloquer en signalant une erreur

### Ordre d'évaluation

Les règles iptables s'évaluent **de haut en bas** et s'arrêtent à la **première correspondance**. C'est crucial pour comprendre la priorité des règles.

---

## Défi 1 : Bloquer tout le trafic entrant sur un port

### 📋 Situation

Ton hôte `10.0.0.1` reçoit du trafic sur le port `31337`. Tu dois **bloquer complètement ce trafic**, peu importe d'où il vient.

### 🎯 Objectif

Configurer le firewall pour refuser toutes les connexions entrantes sur le port 31337.

### 💻 Solution

```bash
# Bloquer tout le trafic entrant sur le port 31337
sudo iptables -A INPUT -p tcp --dport 31337 -j DROP
```

### 🔍 Explication détaillée

```bash
sudo iptables -A INPUT -p tcp --dport 31337 -j DROP
│    │        │ │     │ │   │        │         │
│    │        │ │     │ │   │        │         └─ ACTION: Bloquer (DROP)
│    │        │ │     │ │   │        └─────────── Port destination: 31337
│    │        │ │     │ │   └────────────────── Protocole: TCP
│    │        │ │     │ └──────────────────── Option: port destination
│    │        │ │     └────────────────────── Type d'option: -p (protocole)
│    │        │ └───────────────────────────── Chaîne: INPUT (trafic entrant)
│    │        └─────────────────────────────── Ajouter une règle (-A)
│    └──────────────────────────────────────── Programme firewall
└─────────────────────────────────────────── Exécuter avec droits admin
```

### 📊 Détail des paramètres

| Paramètre | Signification |
|-----------|--------------|
| `sudo` | Exécute avec droits administrateur (nécessaire) |
| `iptables` | Outil de configuration du firewall |
| `-A INPUT` | **A**joute une règle à la chaîne **INPUT** |
| `-p tcp` | S'applique au protocole **TCP** |
| `--dport 31337` | **D**estination **PORT** = 31337 |
| `-j DROP` | **J**ump (sauter) vers l'action **DROP** (bloquer) |

### ✅ Vérification

```bash
# Afficher les règles de la chaîne INPUT
sudo iptables -L INPUT -n

# Output attendu :
# Chain INPUT (policy ACCEPT)
# target     prot opt source       destination
# DROP       tcp  --  0.0.0.0/0    0.0.0.0/0    tcp dpt:31337
```

### 📝 Notes importantes

- **Pas de source/destination spécifiée** : La règle s'applique à **toutes les IPs**
- **0.0.0.0/0** : Notation CIDR signifiant "n'importe quelle adresse IP"
- **DROP vs REJECT** : DROP ignore silencieusement (plus discret), REJECT envoie une erreur
- **Ordre des règles** : Cette seule règle suffit car elle couvre tous les cas

---

## Défi 2 : Bloquer sélectivement le trafic entrant

### 📋 Situation

Ton hôte `10.0.0.1` reçoit du trafic sur le port `31337` depuis deux machines :
- Machine `10.0.0.2` : Tu veux **AUTORISER** sa connexion ✅
- Machine `10.0.0.3` : Tu veux **BLOQUER** sa connexion ❌

### 🎯 Objectif

Créer des règles **spécifiques** au lieu de bloquer tout en masse. Cela démontre la **filtrage sélectif** et l'importance de l'ordre des règles.

### 💻 Solution

```bash
# Étape 1 : Autoriser la connexion depuis 10.0.0.2
sudo iptables -A INPUT -s 10.0.0.2 -d 10.0.0.1 -p tcp --dport 31337 -j ACCEPT

# Étape 2 : Bloquer la connexion depuis 10.0.0.3
sudo iptables -A INPUT -s 10.0.0.3 -d 10.0.0.1 -p tcp --dport 31337 -j DROP
```

### 🔍 Explication détaillée - Règle 1 (ACCEPT)

```bash
sudo iptables -A INPUT -s 10.0.0.2 -d 10.0.0.1 -p tcp --dport 31337 -j ACCEPT
│    │        │ │     │             │         │       │    │         │
│    │        │ │     │             │         │       │    │         └─ ACTION: Accepter
│    │        │ │     │             │         │       │    └─────────── Port dest: 31337
│    │        │ │     │             │         │       └──────────────── Protocole: TCP
│    │        │ │     │             │         └───────────────────────  IP destination
│    │        │ │     │             └──────────────────────────────── 10.0.0.1
│    │        │ │     └─────────────────────────────────────────────  Source: 10.0.0.2
│    │        │ └───────────────────────────────────────────────────  Chaîne: INPUT
│    │        └─────────────────────────────────────────────────────  Ajouter (-A)
│    └──────────────────────────────────────────────────────────────  iptables
└─────────────────────────────────────────────────────────────────── sudo
```

### 📊 Détail des paramètres - Règle 1

| Paramètre | Signification |
|-----------|--------------|
| `-s 10.0.0.2` | **S**ource (d'où vient le trafic) = 10.0.0.2 |
| `-d 10.0.0.1` | **D**estination (où va le trafic) = 10.0.0.1 |
| `-p tcp` | Protocole TCP |
| `--dport 31337` | Port de destination 31337 |
| `-j ACCEPT` | Action : Laisser passer ✅ |

### 🔍 Explication détaillée - Règle 2 (DROP)

```bash
sudo iptables -A INPUT -s 10.0.0.3 -d 10.0.0.1 -p tcp --dport 31337 -j DROP
│    │        │ │     │             │         │       │    │         │
│    │        │ │     │             │         │       │    │         └─ ACTION: Bloquer
│    │        │ │     │             │         │       │    └─────────── Port dest: 31337
│    │        │ │     │             │         │       └──────────────── Protocole: TCP
│    │        │ │     │             │         └───────────────────────  IP destination
│    │        │ │     │             └──────────────────────────────── 10.0.0.1
│    │        │ │     └─────────────────────────────────────────────  Source: 10.0.0.3
│    │        │ └───────────────────────────────────────────────────  Chaîne: INPUT
│    │        └─────────────────────────────────────────────────────  Ajouter (-A)
│    └──────────────────────────────────────────────────────────────  iptables
└─────────────────────────────────────────────────────────────────── sudo
```

### 📊 Détail des paramètres - Règle 2

| Paramètre | Signification |
|-----------|--------------|
| `-s 10.0.0.3` | Source (d'où vient le trafic) = 10.0.0.3 |
| `-d 10.0.0.1` | Destination (où va le trafic) = 10.0.0.1 |
| `-p tcp` | Protocole TCP |
| `--dport 31337` | Port de destination 31337 |
| `-j DROP` | Action : Bloquer silencieusement ❌ |

### ✅ Vérification

```bash
# Afficher toutes les règles INPUT
sudo iptables -L INPUT -n

# Output attendu :
# Chain INPUT (policy ACCEPT)
# target     prot opt source         destination
# ACCEPT     tcp  --  10.0.0.2       10.0.0.1    tcp dpt:31337
# DROP       tcp  --  10.0.0.3       10.0.0.1    tcp dpt:31337
```

### 🔄 Schéma du traitement des paquets

```
Paquet entrant de 10.0.0.2:54321 → 10.0.0.1:31337
                            ↓
                   ┌────────────────────┐
                   │ Règle 1 : ACCEPT   │
                   │ 10.0.0.2 → 10.0.0.1│
                   │ Correspond? OUI ✅ │
                   │ Action: ACCEPTER   │
                   └────────────────────┘
                            ↓
                   ✅ Paquet accepté


Paquet entrant de 10.0.0.3:54321 → 10.0.0.1:31337
                            ↓
                   ┌────────────────────┐
                   │ Règle 1 : ACCEPT   │
                   │ 10.0.0.2 → 10.0.0.1│
                   │ Correspond? NON ❌ │
                   └────────────────────┘
                            ↓
                   ┌────────────────────┐
                   │ Règle 2 : DROP     │
                   │ 10.0.0.3 → 10.0.0.1│
                   │ Correspond? OUI ✅ │
                   │ Action: BLOQUER    │
                   └────────────────────┘
                            ↓
                   ❌ Paquet bloqué
```

### 📝 Notes importantes

- **L'ordre compte** : Règles évaluées de haut en bas
- **Spécificité** : Les règles spécifiques doivent venir avant les générales
- **Source ET destination** : Les deux critères doivent correspondre
- **Bidirectionnalité** : Seul INPUT ne suffit pas pour une vraie communication

---

## Défi 3 : Autoriser le trafic sortant et établir une connexion

### 📋 Situation

Depuis ton hôte `10.0.0.1`, tu dois te connecter au serveur distant `10.0.0.2` sur le port `31337`. 

**Mais attention** : Le trafic **sortant** vers ce port est bloqué par défaut. Tu dois :
1. Autoriser la **sortie** (OUTPUT) vers 10.0.0.2:31337
2. Autoriser l'**entrée** (INPUT) de la réponse depuis 10.0.0.2:31337
3. Établir la connexion
4. Récupérer le flag

### 🎯 Objectif

Comprendre que **les deux directions** (INPUT et OUTPUT) doivent être autorisées pour une communication bidirectionnelle.

### 💻 Solution - Étape 1 : Autoriser la sortie

```bash
sudo iptables -A OUTPUT -s 10.0.0.1 -d 10.0.0.2 -p tcp --dport 31337 -j ACCEPT
```

### 🔍 Explication - Étape 1 (OUTPUT)

```bash
sudo iptables -A OUTPUT -s 10.0.0.1 -d 10.0.0.2 -p tcp --dport 31337 -j ACCEPT
│    │        │  │      │             │         │       │    │         │
│    │        │  │      │             │         │       │    │         └─ ACTION: Accepter
│    │        │  │      │             │         │       │    └─────────── Port dest: 31337
│    │        │  │      │             │         │       └──────────────── Protocole: TCP
│    │        │  │      │             │         └───────────────────────  IP destination
│    │        │  │      │             └──────────────────────────────── 10.0.0.2
│    │        │  │      └─────────────────────────────────────────────  Source: 10.0.0.1
│    │        │  └───────────────────────────────────────────────────── Chaîne: OUTPUT
│    │        └─────────────────────────────────────────────────────── Ajouter (-A)
│    └──────────────────────────────────────────────────────────────── iptables
└─────────────────────────────────────────────────────────────────── sudo
```

### 📊 Détail des paramètres - Étape 1

| Paramètre | Signification |
|-----------|--------------|
| `-A OUTPUT` | **A**joute une règle à la chaîne **OUTPUT** (trafic sortant) |
| `-s 10.0.0.1` | Source (ta machine) |
| `-d 10.0.0.2` | Destination (le serveur distant) |
| `-p tcp` | Protocole TCP |
| `--dport 31337` | Port de destination |
| `-j ACCEPT` | Action : Laisser sortir ✅ |

### 💻 Solution - Étape 2 : Supprimer la règle DROP générale (si elle existe)

```bash
# Vérifier la configuration OUTPUT
sudo iptables -L OUTPUT -n

# S'il y a une règle DROP 0.0.0.0/0 en première ligne, la supprimer
sudo iptables -D OUTPUT 1
```

### 🔍 Explication - Étape 2

Si tu vois :
```
Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination
DROP       tcp  --  0.0.0.0/0            0.0.0.0/0    tcp dpt:31337
ACCEPT     tcp  --  10.0.0.1             10.0.0.2     tcp dpt:31337
```

**Problème** : La règle DROP s'évalue **avant** ta règle ACCEPT. Même si ta règle est plus spécifique, elle n'est jamais atteinte.

**Solution** : Supprimer la règle générale (ligne 1 = `-D OUTPUT 1`)

```bash
sudo iptables -D OUTPUT 1
│    │        │  │      │
│    │        │  │      └─ Numéro de la règle à supprimer (première)
│    │        │  └──────── Chaîne: OUTPUT
│    │        └─────────── **D**elete (supprimer)
│    └──────────────────── iptables
└─────────────────────── sudo
```

### 💻 Solution - Étape 3 : Autoriser l'entrée de la réponse

```bash
sudo iptables -A INPUT -s 10.0.0.2 -d 10.0.0.1 -p tcp --sport 31337 -j ACCEPT
```

### 🔍 Explication - Étape 3 (INPUT)

```bash
sudo iptables -A INPUT -s 10.0.0.2 -d 10.0.0.1 -p tcp --sport 31337 -j ACCEPT
│    │        │ │     │             │         │       │    │         │
│    │        │ │     │             │         │       │    │         └─ ACTION: Accepter
│    │        │ │     │             │         │       │    └─────────── Port SOURCE: 31337
│    │        │ │     │             │         │       └──────────────── Protocole: TCP
│    │        │ │     │             │         └───────────────────────  IP destination
│    │        │ │     │             └──────────────────────────────── 10.0.0.1
│    │        │ │     └─────────────────────────────────────────────  Source: 10.0.0.2
│    │        │ └───────────────────────────────────────────────────── Chaîne: INPUT
│    │        └─────────────────────────────────────────────────────── Ajouter (-A)
│    └──────────────────────────────────────────────────────────────── iptables
└─────────────────────────────────────────────────────────────────── sudo
```

### 📊 Détail des paramètres - Étape 3

| Paramètre | Signification |
|-----------|--------------|
| `-A INPUT` | Ajoute une règle à la chaîne INPUT (trafic entrant) |
| `-s 10.0.0.2` | Source : le serveur qui répond |
| `-d 10.0.0.1` | Destination : ta machine |
| `-p tcp` | Protocole TCP |
| `--sport 31337` | **S**ource **PORT** = 31337 (port d'où vient la réponse) |
| `-j ACCEPT` | Action : Accepter la réponse ✅ |

### ⚠️ Différence clé : --dport vs --sport

```
OUTPUT (tu envoies)         INPUT (tu reçois)
─────────────────         ─────────────────
Tu envoies VERS            Tu reçois DEPUIS
destination port 31337     source port 31337

--dport 31337             --sport 31337
(destination)             (source)
```

### 💻 Solution - Étape 4 : Se connecter

```bash
nc -v 10.0.0.2 31337
```

### 🔍 Explication - Étape 4

```bash
nc -v 10.0.0.2 31337
│  │ │       │  │
│  │ │       │  └─ Port à connecter
│  │ │       └───── Adresse IP destination
│  │ └───────────── Verbose (affiche les détails)
│  └─────────────── netcat (outil de connexion réseau)
```

**Commandes alternatives :**
```bash
# SSH
ssh user@10.0.0.2 -p 31337

# telnet
telnet 10.0.0.2 31337

# curl (si c'est un service web)
curl http://10.0.0.2:31337
```

### 💻 Solution - Étape 5 : Récupérer le flag

Une fois connecté, envoie une commande :

```bash
# Une fois dans la connexion nc, tape :
flag
# ou
get flag
# ou juste attendre la réponse automatique
```

### ✅ Vérification complète

```bash
# Vérifier OUTPUT
sudo iptables -L OUTPUT -n

# Afficher toutes les règles INPUT et OUTPUT
sudo iptables -L INPUT -n -v
sudo iptables -L OUTPUT -n -v

# Tester la connexion
nc -v 10.0.0.2 31337
```

### 🔄 Schéma du flux de communication complet

```
Ma machine (10.0.0.1)          Serveur distant (10.0.0.2)
────────────────────────────────────────────────────────

Étape 1 : Je veux me connecter
          │
          ├─► OUTPUT: 10.0.0.1 → 10.0.0.2:31337
          │           Vérifie: -s 10.0.0.1 -d 10.0.0.2 --dport 31337
          │           Résultat: ACCEPT ✅
          │
          ├─────────────────────────────────────────────► SYN
                                                          │
                                                    Reçoit connexion
                                                    Répond avec SYN-ACK

Étape 2 : Je reçois la réponse du serveur
          │◄─────────────────────────────────────────── SYN-ACK
          │
          ├─ INPUT: 10.0.0.2:31337 → 10.0.0.1
          │          Vérifie: -s 10.0.0.2 -d 10.0.0.1 --sport 31337
          │          Résultat: ACCEPT ✅
          │
          ├─────────────────────────────────────────────► ACK
                                                          │
                                                  Connexion établie ✅

Étape 3 : Communication établie
          │◄───────────────────────────────────────────► Données
          │ (Bidirectionnelle)
          │
          └─ Flag reçu ! 🚩
```

### 📝 Notes importantes

- **OUTPUT et INPUT doivent travailler ensemble** pour une vraie communication
- **Direction des ports** :
  - `--dport` pour les paquets sortants (destination port)
  - `--sport` pour les paquets entrants (source port)
- **État established** : Les règles ci-dessus supposent TCP avec handshake complet
- **Ordre des règles** : Comme au Défi 2, les règles générales doivent venir après les spécifiques

---

## Comparaison des trois défis

| Défi | Chaîne | Type de filtrage | Complexité |
|------|--------|------------------|-----------|
| **1** | INPUT | Bloquer tout sur un port | Facile |
| **2** | INPUT | Bloquer sélectivement | Moyen |
| **3** | OUTPUT + INPUT | Communication bidirectionnelle | Avancé |

---

## Bonnes pratiques de firewall

### ✅ À faire

```bash
# 1. Bloquer par défaut, autoriser le nécessaire
sudo iptables -P INPUT DROP
sudo iptables -P OUTPUT DROP
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT  # SSH
sudo iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT # HTTP

# 2. Mettre les règles spécifiques en premier
sudo iptables -I INPUT 1 -s 10.0.0.2 --dport 31337 -j ACCEPT

# 3. Vérifier après chaque changement
sudo iptables -L -n

# 4. Sauvegarder les règles
sudo apt-get install iptables-persistent
sudo netfilter-persistent save
```

### ❌ À éviter

```bash
# ❌ Mauvais : Règle générale en premier
sudo iptables -A OUTPUT -j DROP
sudo iptables -A OUTPUT -s 10.0.0.1 -j ACCEPT  # Jamais atteint !

# ❌ Mauvais : Pas de vérification
sudo iptables ... (sans vérifier avec -L -n)

# ❌ Mauvais : Oublier une direction
# Autoriser OUTPUT mais pas INPUT (timeout)
```

---

## Ressources supplémentaires

- [Manual iptables](https://linux.die.net/man/8/iptables)
- [iptables tutorial](https://www.netfilter.org/documentation/)
- [UFW (wrapper simplifié)](https://help.ubuntu.com/community/UFW)

---

## Résumé rapide

```bash
# Défi 1 : Bloquer tout
sudo iptables -A INPUT -p tcp --dport 31337 -j DROP

# Défi 2 : Bloquer sélectivement
sudo iptables -A INPUT -s 10.0.0.2 -d 10.0.0.1 -p tcp --dport 31337 -j ACCEPT
sudo iptables -A INPUT -s 10.0.0.3 -d 10.0.0.1 -p tcp --dport 31337 -j DROP

# Défi 3 : Communiquer bidirectionnellement
sudo iptables -A OUTPUT -s 10.0.0.1 -d 10.0.0.2 -p tcp --dport 31337 -j ACCEPT
sudo iptables -A INPUT -s 10.0.0.2 -d 10.0.0.1 -p tcp --sport 31337 -j ACCEPT
nc -v 10.0.0.2 31337
```
