# 🚨 Troubleshooting - Résolution des Problèmes Pwntools

Guide pour résoudre les erreurs courantes.

---

## 🔴 Problème 1 : "Connection refused"

### Symptômes
```
[!] Couldn't connect to localhost:1234
[!] Error: [Errno 111] Connection refused
```

### Causes Possibles

1. **Le serveur n'est pas lancé**
   
   **Solution:**
   ```bash
   # Terminal 1 - Lancer le serveur
   nc -lvnp 1234
   
   # Terminal 2 - Lancer votre exploit
   python3 exploit.py
   ```

2. **Mauvais port**
   
   **Solution:**
   ```bash
   # Vérifier le port
   netstat -tlnp | grep 1234
   
   # Ou utiliser un autre port
   nc -lvnp 5555
   ```

3. **Firewall bloquant**
   
   **Solution:**
   ```bash
   # Désactiver temporairement (attention!)
   sudo ufw disable
   
   # Ou ouvrir le port
   sudo ufw allow 1234
   ```

### Code de Test
```python
from pwn import *

try:
    p = remote("localhost", 1234, timeout=5)
    log.success("Connecté!")
except ConnectionRefusedError:
    log.failure("Connexion refusée - le serveur n'est pas lancé?")
    log.info("Lancez: nc -lvnp 1234")
except socket.timeout:
    log.failure("Timeout - le serveur répond trop lentement")
```

---

## 🔴 Problème 2 : "Timeout"

### Symptômes
```
[!] Timeout waiting for data
[!] Timeout waiting on the wire
```

### Causes Possibles

1. **Le serveur envoie rien**
   
   **Solution:**
   ```python
   # Augmenter le timeout
   p = remote("localhost", 1234, timeout=30)
   
   # Ou déboguer ce qu'on reçoit
   p.recvline(timeout=5)  # Timeout par commande
   ```

2. **Lecture bloquante**
   
   **Solution:**
   ```python
   # Au lieu de
   p.recvline()  # Bloque indéfiniment
   
   # Utiliser
   p.recvline(timeout=5)  # 5 secondes max
   ```

3. **Le serveur attend quelque chose**
   
   **Solution:**
   ```python
   # Envoyer quelque chose avant de lire
   p.sendline(b"test")
   p.recvline()
   ```

### Code Robuste
```python
from pwn import *

p = remote("localhost", 1234, timeout=10)

try:
    data = p.recvline(timeout=5)
    print(data)
except socket.timeout:
    log.warning("Timeout en lisant - peut-être EOF")
    data = p.recvall()
    print(data)
```

---

## 🔴 Problème 3 : "Binary not found"

### Symptômes
```
[!] Could not open file: No such file or directory
FileNotFoundError: [Errno 2] No such file or directory: './binary'
```

### Causes Possibles

1. **Le binaire n'existe pas**
   
   **Solution:**
   ```bash
   # Vérifier que le fichier existe
   ls -la ./binary
   
   # Ou le compiler
   gcc -o binary binary.c
   ```

2. **Mauvais chemin**
   
   **Solution:**
   ```python
   # À la place de
   elf = ELF("./binary")
   
   # Utiliser
   import os
   binary_path = os.path.join(os.getcwd(), "binary")
   elf = ELF(binary_path)
   ```

3. **Permissions manquantes**
   
   **Solution:**
   ```bash
   # Rendre exécutable
   chmod +x binary
   ```

### Code Robuste
```python
from pwn import *
import os

BINARY = "./binary"

if not os.path.exists(BINARY):
    log.failure(f"Binary not found: {BINARY}")
    log.info("Compile with: gcc -o binary binary.c")
    sys.exit(1)

if not os.access(BINARY, os.X_OK):
    log.warning("Binary not executable, fixing...")
    os.chmod(BINARY, 0o755)

elf = ELF(BINARY)
```

---

## 🔴 Problème 4 : "Symbol not found"

### Symptômes
```
KeyError: "Symbol 'win' not found"
KeyError: "Symbol 'system' not found"
```

### Causes Possibles

1. **Binaire strippé**
   
   **Vérification:**
   ```bash
   # Vérifier si strippé
   file binary
   # Output: ELF 64-bit ... stripped
   
   # Voir les symboles
   nm binary
   objdump -t binary
   strings binary
   ```
   
   **Solution:**
   ```bash
   # Si strippé, compiler sans strip
   gcc -o binary binary.c -g
   
   # Ou strip après
   gcc -o binary binary.c
   # Puis pour reverser: gdb/radare2/ghidra
   ```

2. **Fonction n'existe pas**
   
   **Solution:**
   ```python
   # Vérifier les symboles disponibles
   elf = ELF("./binary")
   print(elf.symbols.keys())
   
   # Chercher manuellement
   for name in elf.symbols:
       if "flag" in name or "win" in name:
           print(f"Found: {name}")
   ```

3. **Binaire dynamique (nécessite libc)**
   
   **Solution:**
   ```python
   from pwnlib.dynelf import DynELF
   
   elf = ELF("./binary")
   libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
   
   # Utiliser libc pour les symboles
   system = libc.symbols['system']
   ```

### Code Robuste
```python
from pwn import *

elf = ELF("./binary")

# Vérifier si un symbole existe
if 'win' in elf.symbols:
    win_addr = elf.symbols['win']
else:
    log.warning("Symbol 'win' not found (binary is stripped?)")
    # Chercher manuellement avec GDB/objdump
    log.info("Use: objdump -t binary | grep win")
    # Ou utiliser une adresse hardcoded trouvée avec GDB
    win_addr = 0x08048450
```

---

## 🔴 Problème 5 : "ASLR Enabled"

### Symptômes
```
Adresses différentes chaque fois que vous lancez le binaire
L'exploit marche une fois puis échoue
```

### Causes

ASLR (Address Space Layout Randomization) randomise les adresses.

### Solutions

**Locale (pour tester)**
```bash
# Désactiver ASLR temporairement
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space

# Vérifier
cat /proc/sys/kernel/randomize_va_space  # 0 = désactivé

# Réactiver
echo 1 | sudo tee /proc/sys/kernel/randomize_va_space
```

**Dans le code**
```python
from pwn import *

# Désactiver ASLR pour ce processus
p = process("./binary", aslr=False)
```

**Vérifier avec GDB**
```bash
# Vérifier si PIE
file binary
# Résultat: ... PIE (Position Independent Executable)

# Ou avec checksec
checksec binary
```

### Exploit avec ASLR

Si vous devez supporter ASLR, leaker une adresse d'abord :

```python
from pwn import *

p = process("./binary")

# Leak une adresse (format string par exemple)
p.recvuntil(b"Address: ")
leaked_addr = int(p.recvline().strip(), 16)
log.success(f"Leaked: {hex(leaked_addr)}")

# Calculer le base
elf = ELF("./binary")
base = leaked_addr - elf.symbols['main']
log.info(f"Base: {hex(base)}")

# Utiliser dans l'exploit
win_addr = base + elf.symbols['win']
```

---

## 🔴 Problème 6 : Stack Canary

### Symptômes
```
Stack smashing detected
Abort called
```

### Cause

Un "canary" (valeur de vérification) sur la stack empêche le BOF.

### Solutions

1. **Compiler sans canary (pour tester)**
   ```bash
   gcc -o binary binary.c -fno-stack-protector
   ```

2. **Leaker le canary (exploitation réelle)**
   ```python
   from pwn import *
   
   # Format string pour leaker le canary
   p = process("./binary")
   p.sendline(b"AAAA %x %x %x %x")
   output = p.recvline()
   
   # Analyser la sortie pour trouver le canary
   # Supposons qu'il soit à la 4eme valeur
   values = output.split()
   canary = int(values[3], 16)
   log.info(f"Canary: {hex(canary)}")
   
   # Utiliser dans le payload
   payload = b'A' * 32
   payload += p64(canary)  # Inclure le canary
   payload += p64(win_addr)
   ```

3. **Vérifier avec checksec**
   ```bash
   checksec binary
   # Chercher "Canary: Canary found"
   ```

---

## 🔴 Problème 7 : NX Bit / DEP

### Symptômes
```
Segmentation fault quand vous essayez d'exécuter la stack
```

### Cause

NX (No eXecute) empêche l'exécution de code sur la stack.

### Solutions

1. **Compiler sans NX (pour tester)**
   ```bash
   gcc -o binary binary.c -z execstack
   ```

2. **Utiliser ROP chains**
   ```python
   rop = ROP(elf)
   rop.call("system", ["/bin/sh"])
   chain = rop.chain()
   ```

3. **Vérifier avec checksec**
   ```bash
   checksec binary
   # Chercher "NX: NX enabled"
   ```

---

## 🔴 Problème 8 : Segmentation Fault

### Symptômes
```
Segmentation fault (core dumped)
```

### Causes Possibles

1. **Mauvaise adresse**
   
   **Solution:**
   ```python
   # Déboguer avec GDB
   p = gdb.debug("./binary", gdbscript="run")
   # GDB montrera où ça crash
   ```

2. **Payload mal aligné**
   
   **Solution:**
   ```python
   # Sur x86-64, RSP doit être alignée sur 16 bytes
   # Avant un call
   payload = b'A' * 32
   payload += b'B' * 8  # Padding
   payload += p64(address)
   # RSP = non alignée, ajouter/retirer 8 bytes
   ```

3. **Stack écrasée**
   
   **Solution:**
   ```python
   # Vérifier le payload n'est pas trop grand
   log.info(f"Payload size: {len(payload)}")
   
   # Déboguer avec cyclic
   pattern = cyclic(200)
   p.sendline(pattern)
   # Voir où ça crash
   ```

---

## 🔴 Problème 9 : "Permission denied"

### Symptômes
```
[!] Error: [Errno 13] Permission denied: './binary'
PermissionError: [Errno 13] Permission denied
```

### Solution
```bash
# Rendre exécutable
chmod +x ./binary

# Ou
chmod 755 ./binary
```

---

## 🔴 Problème 10 : Architecture Mismatch

### Symptômes
```
Wrong architecture
[!] Could not set architecture
```

### Solution
```python
from pwn import *

# Vérifier l'architecture
file_output = os.popen("file ./binary").read()
print(file_output)

# Définir la bonne architecture
if "x86-64" in file_output:
    context.arch = 'amd64'
elif "Intel 80386" in file_output:
    context.arch = 'i386'
elif "ARM" in file_output:
    context.arch = 'arm'

print(f"Architecture set to: {context.arch}")
```

---

## 🔴 Problème 11 : Endianness

### Symptômes
```
Les adresses ne correspondent pas
Les valeurs sont inversées
```

### Solution
```python
from pwn import *

# Vérifier l'endianness
file_output = os.popen("file ./binary").read()
print(file_output)

# Définir correctement
if "little-endian" in file_output or "LSB" in file_output:
    context.endian = 'little'
else:
    context.endian = 'big'

# Ou packer explicitement
p32(0x12345678, endian='little')  # Little
p32(0x12345678, endian='big')     # Big
```

---

## 🔴 Problème 12 : Format String Exploitation

### Problème : "Can't find offset"

```python
from pwnlib.fmtstr import *

def fmt_oracle(payload):
    p = process("./vulnerable")
    p.sendline(payload)
    result = p.recvline()
    p.close()
    return result

try:
    offset = find_fmt_offset(fmt_oracle)
    print(f"Offset: {offset}")
except:
    log.failure("Could not find offset")
    log.info("Try manually: %x %x %x %x ...")
```

---

## 🛠️ Debugging Techniques

### Technique 1 : Logging Agressif

```python
from pwn import *

context.log_level = 'debug'  # Maximum verbosité

# Cela affichera TOUT ce qui se passe
p = process("./binary")
p.sendline(b"test")
p.recvline()
```

### Technique 2 : Sauvegarder le Payload

```python
# Sauvegarder pour analyse
with open("payload.bin", "wb") as f:
    f.write(payload)

# Analyser avec hexdump
os.system("hexdump -C payload.bin")

# Ou avec xxd
os.system("xxd payload.bin")
```

### Technique 3 : Déboguer Étape par Étape

```python
from pwn import *

log.info("[1] Lire le prompt")
prompt = p.recvline()
print(prompt)

log.info("[2] Créer le payload")
payload = b'A' * 64 + p64(0x12345678)
print(f"Payload: {payload.hex()}")

log.info("[3] Envoyer le payload")
p.sendline(payload)

log.info("[4] Attendre la réponse")
try:
    response = p.recvline(timeout=5)
    print(response)
except socket.timeout:
    log.warning("Timeout")
```

### Technique 4 : GDB Interactif

```python
from pwn import *

p = gdb.debug("./binary", gdbscript="""
    break main
    continue
    
    # À ce point, entrez les commandes GDB
    # gdb> c (continue)
    # gdb> x/i $rip (instruction)
    # gdb> p $rax (valeur de rax)
    # etc...
""")

p.interactive()
```

---

## 📋 Checklist Avant de Lancer

- [ ] Binaire existe et est exécutable?
- [ ] Architecture correcte? (file binary)
- [ ] Protections vérifiées? (checksec binary)
- [ ] ASLR activé? (cat /proc/sys/kernel/randomize_va_space)
- [ ] Canary/NX/PIE? (Compilation appropriée)
- [ ] Adresses trouvées? (objdump, gdb, objdump)
- [ ] Offset calculé? (cyclic)
- [ ] Endianness correct? (little/big)
- [ ] Payload testé? (sauvegarder et analyser)
- [ ] Timeout correctement configuré?

---

## 🔗 Ressources Utiles

```bash
# Afficher les informations du binaire
file binary
objdump -d binary
objdump -t binary
nm -D binary
strings binary

# Déboguer
gdb binary
radare2 binary

# Vérifier les protections
checksec binary

# Trouver les gadgets
ROPgadget --binary binary

# Analyser le réseau
strace -e socket,connect -f ./binary
```

---

## 💡 Tips Pro

1. **Toujours tester localement d'abord** ✓
2. **Utiliser des patterns pour les offsets** ✓
3. **Sauvegarder les payloads** ✓
4. **Déboguer avec GDB** ✓
5. **Vérifier les messages d'erreur** ✓
6. **Documenter votre exploitation** ✓

---

**Si vous ne trouvez pas la solution ici, cherchez sur Google avec le message d'erreur! 🔍**

**Bonne chance! 🚀**
