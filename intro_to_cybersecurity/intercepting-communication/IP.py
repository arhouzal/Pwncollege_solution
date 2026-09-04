from scapy.all import IP, send

# Construction du paquet IP :
# - dst : l'hôte distant (10.0.0.2)
# - proto : le champ protocole personnalisé (255 / 0xFF)
# le champ de payload n est pas obligatoire 
paquet = IP(dst="10.0.0.2", proto=255) / b"payload challenge"

print("[*] Envoi du paquet IP avec proto=0xFF via Scapy...")
# send() envoie le paquet au niveau de la couche 3 (IP)
send(paquet, verbose=True)
print("[+] Paquet IP envoyé !")

#---------------------- code du challenge -------------------
#!/usr/bin/exec-suid --real -- /usr/local/bin/python -I

import os

import psutil
import scapy.all as scapy
from dojjail import Host, Network

flag = open("/flag").read()
parent_process = psutil.Process(os.getppid())

class RawPacketHost(Host):
    def entrypoint(self):
        scapy.conf.ifaces.reload()
        scapy.sniff(prn=self.handle_packet, iface="eth0")

    def handle_packet(self, packet):
        if "IP" not in packet:
            return
        if packet["IP"].proto == 0xFF:
            print(flag, flush=True)

user_host = Host("ip-10-0-0-1", privileged_uid=parent_process.uids().effective)
raw_packet_host = RawPacketHost("ip-10-0-0-2")
network = Network(hosts={user_host: "10.0.0.1", raw_packet_host: "10.0.0.2"}, subnet="10.0.0.0/24")
network.run()

user_host.interactive(environ=parent_process.environ())
#----------------------------------------------------------
# Version avec les Sockets Bruts Natifs (Python socket):
import socket

# 1. Création d'un socket brut IP/RAW (IPPROTO_RAW permet de construire l'en-tête IP soi-même)
s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)

# 2. Activation de l'option IP_HDRINCL pour dire au noyau que l'en-tête IP est inclus dans le buffer
s.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# --- Construction de l'en-tête IP (20 octets minimum) ---
# Version (4 bits) + IHL (4 bits) -> 0x45 (IPv4, taille 5 mots de 32 bits = 20 octets)
version_ihl = b'\x45'
tos = b'\x00'                     # Type of Service
total_length = b'\x00\x1f'        # Longueur totale (20 octets d'en-tête + 15 octets de payload = 31 / 0x001F)
identification = b'\xab\xcd'      # ID du paquet
flags_fragment = b'\x40\x00'      # Flags (Don't Fragment) et offset
ttl = b'\x40'                     # Time to Live (64)
proto = b'\xff'                   # LE CHAMP DEMANDÉ : Protocole 0xFF (255)
checksum = b'\x00\x00'            # Checksum (le noyau peut le calculer automatiquement, on met 0)

# Adresse IP Source (ex: 10.0.0.1) et Destination (10.0.0.2)
src_ip = socket.inet_aton("10.0.0.1")
dst_ip = socket.inet_aton("10.0.0.2")

# Assemblage de l'en-tête IP
ip_header = version_ihl + tos + total_length + identification + flags_fragment + ttl + proto + checksum + src_ip + dst_ip

# 3. Ajout de la charge utile (payload)
payload = b"hello challenge"

# Paquet IP complet (En-tête + Payload)
paquet_ip_complet = ip_header + payload

# 4. Envoi du paquet vers la cible (10.0.0.2)
# Pour un socket brut IP_HDRINCL, on utilise sendto avec l'IP de destination
s.sendto(paquet_ip_complet, ("10.0.0.2", 0))
print("[+] Paquet IP brut avec proto=0xFF envoyé avec succès !")
