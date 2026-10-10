import subprocess
import os
import ipaddress
from config import WG_CONF, WG_SUBNET

SUBNET = ipaddress.ip_network(WG_SUBNET)

def gen_keypair():
    priv = subprocess.check_output(["wg", "genkey"]).decode().strip()
    pub = subprocess.check_output(
        ["wg", "pubkey"], input=priv.encode()
    ).decode().strip()
    return priv, pub

def next_free_ip():
    used = set()
    if os.path.exists(WG_CONF):
        with open(WG_CONF) as f:
            for line in f:
                if "AllowedIPs" in line:
                    ip = line.split("=")[1].strip().split("/")[0]
                    used.add(ip)
    for ip in SUBNET.hosts():
        if str(ip) not in used and str(ip) != "10.8.0.1":
            return str(ip)
    raise RuntimeError("No free IPs")

def add_peer(public_key, address):
    subprocess.check_call([
        "wg", "set", "wg0",
        "peer", public_key,
        "allowed-ips", f"{address}/32"
    ])
    with open(WG_CONF, "a") as f:
        f.write(f"\n[Peer]\nPublicKey = {public_key}\nAllowedIPs = {address}/32\n")

def remove_peer(public_key):
    subprocess.call(["wg", "set", "wg0", "peer", public_key, "remove"])

def build_client_config(priv, address, server_pub, endpoint, dns="1.1.1.1"):
    return f"""[Interface]
PrivateKey = {priv}
Address = {address}/32
DNS = {dns}

[Peer]
PublicKey = {server_pub}
Endpoint = {endpoint}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
