import socket
import time
import struct

MCAST_GRP = '239.192.0.1'   # multicast group (choose one for local testing)
MCAST_PORT = 12345

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

try:
    with open("data/01302019.NASDAQ_ITCH50", "rb") as f:
        print(f"Simulator started... Multicast group: {MCAST_GRP}, Port: {MCAST_PORT}")
        while True:
            try:
                # Each ITCH msg starts with 2-byte length
                length_bytes = f.read(2)
                if not length_bytes or len(length_bytes) < 2:
                    break
                length = struct.unpack("!H", length_bytes)[0]
                msg = f.read(length)
                if not msg or len(msg) < length:
                    print("Incomplete message read from file.")
                    break

                # Send over UDP multicast
                sock.sendto(length_bytes + msg, (MCAST_GRP, MCAST_PORT))

                # Sleep a bit to simulate pacing (tweak this)
                time.sleep(0.0001)
            except Exception as e:
                print(f"Error during message send: {e}")
                break
except Exception as e:
    print(f"Error: {e}")
