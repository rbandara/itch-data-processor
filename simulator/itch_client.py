import socket
import struct
import sys
from datetime import datetime, timedelta


class ITCHClient:
    def __init__(self, mcast_group='239.192.0.1', mcast_port=12345):
        self.mcast_group = mcast_group
        self.mcast_port = mcast_port
        self.sock = None
        self.message_count = 0

    def connect(self):
        """Set up multicast socket for receiving ITCH data"""
        try:
            # Create socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

            # Allow multiple sockets to use the same PORT number
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to the port
            self.sock.bind(('', self.mcast_port))

            # Tell the kernel that we want to add ourselves to a multicast group
            mreq = struct.pack("4sl", socket.inet_aton(self.mcast_group), socket.INADDR_ANY)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            print(f"Connected to multicast group {self.mcast_group}:{self.mcast_port}")
            return True

        except Exception as e:
            print(f"Error connecting: {e}")
            return False

    def parse_timestamp(self, timestamp_bytes):
        """Convert ITCH timestamp to readable format"""
        timestamp = struct.unpack("!Q", timestamp_bytes)[0]
        # ITCH timestamps are nanoseconds since midnight
        seconds = timestamp / 1_000_000_000
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    def parse_message(self, data):
        """Parse different ITCH message types"""
        if len(data) < 1:
            return None

        msg_type = data[0:1].decode('ascii')

        try:
            if msg_type == 'S':  # System Event Message
                timestamp = self.parse_timestamp(data[5:13])
                event_code = data[11:12].decode('ascii')
                return f"System Event - Time: {timestamp}, Event: {event_code}"

            elif msg_type == 'R':  # Stock Directory Message
                timestamp = self.parse_timestamp(data[5:13])
                stock = data[11:19].strip().decode('ascii')
                market_category = data[19:20].decode('ascii')
                return f"Stock Directory - Time: {timestamp}, Stock: {stock}, Category: {market_category}"

            elif msg_type == 'H':  # Stock Trading Action Message
                timestamp = self.parse_timestamp(data[5:13])
                stock = data[11:19].strip().decode('ascii')
                trading_state = data[19:20].decode('ascii')
                return f"Trading Action - Time: {timestamp}, Stock: {stock}, State: {trading_state}"

            elif msg_type == 'A':  # Add Order Message
                timestamp = self.parse_timestamp(data[5:13])
                order_ref = struct.unpack("!Q", data[11:19])[0]
                side = data[19:20].decode('ascii')
                shares = struct.unpack("!I", data[20:24])[0]
                stock = data[24:32].strip().decode('ascii')
                price = struct.unpack("!I", data[32:36])[0] / 10000  # Price in 0.0001 increments
                return f"Add Order - Time: {timestamp}, Stock: {stock}, Side: {side}, Shares: {shares}, Price: ${price:.4f}"

            elif msg_type == 'F':  # Add Order with MPID
                timestamp = self.parse_timestamp(data[5:13])
                order_ref = struct.unpack("!Q", data[11:19])[0]
                side = data[19:20].decode('ascii')
                shares = struct.unpack("!I", data[20:24])[0]
                stock = data[24:32].strip().decode('ascii')
                price = struct.unpack("!I", data[32:36])[0] / 10000
                mpid = data[36:40].strip().decode('ascii')
                return f"Add Order (MPID) - Time: {timestamp}, Stock: {stock}, Side: {side}, Shares: {shares}, Price: ${price:.4f}, MPID: {mpid}"

            elif msg_type == 'E':  # Order Executed Message
                timestamp = self.parse_timestamp(data[5:13])
                order_ref = struct.unpack("!Q", data[11:19])[0]
                executed_shares = struct.unpack("!I", data[19:23])[0]
                match_number = struct.unpack("!Q", data[23:31])[0]
                return f"Order Executed - Time: {timestamp}, Order: {order_ref}, Shares: {executed_shares}, Match: {match_number}"

            elif msg_type == 'C':  # Order Executed with Price
                timestamp = self.parse_timestamp(data[5:13])
                order_ref = struct.unpack("!Q", data[11:19])[0]
                executed_shares = struct.unpack("!I", data[19:23])[0]
                match_number = struct.unpack("!Q", data[23:31])[0]
                printable = data[31:32].decode('ascii')
                price = struct.unpack("!I", data[32:36])[0] / 10000
                return f"Order Executed w/Price - Time: {timestamp}, Order: {order_ref}, Shares: {executed_shares}, Price: ${price:.4f}"

            elif msg_type == 'X':  # Order Cancel Message
                timestamp = self.parse_timestamp(data[5:13])
                order_ref = struct.unpack("!Q", data[11:19])[0]
                cancelled_shares = struct.unpack("!I", data[19:23])[0]
                return f"Order Cancel - Time: {timestamp}, Order: {order_ref}, Cancelled: {cancelled_shares}"

            elif msg_type == 'D':  # Order Delete Message
                timestamp = self.parse_timestamp(data[5:13])
                order_ref = struct.unpack("!Q", data[11:19])[0]
                return f"Order Delete - Time: {timestamp}, Order: {order_ref}"

            elif msg_type == 'U':  # Order Replace Message
                timestamp = self.parse_timestamp(data[5:13])
                original_ref = struct.unpack("!Q", data[11:19])[0]
                new_ref = struct.unpack("!Q", data[19:27])[0]
                shares = struct.unpack("!I", data[27:31])[0]
                price = struct.unpack("!I", data[31:35])[0] / 10000
                return f"Order Replace - Time: {timestamp}, Original: {original_ref}, New: {new_ref}, Shares: {shares}, Price: ${price:.4f}"

            elif msg_type == 'P':  # Trade Message (Non-Cross)
                timestamp = self.parse_timestamp(data[5:13])
                order_ref = struct.unpack("!Q", data[11:19])[0]
                side = data[19:20].decode('ascii')
                shares = struct.unpack("!I", data[20:24])[0]
                stock = data[24:32].strip().decode('ascii')
                price = struct.unpack("!I", data[32:36])[0] / 10000
                match_number = struct.unpack("!Q", data[36:44])[0]
                return f"Trade - Time: {timestamp}, Stock: {stock}, Side: {side}, Shares: {shares}, Price: ${price:.4f}"

            elif msg_type == 'Q':  # Cross Trade Message
                timestamp = self.parse_timestamp(data[5:13])
                shares = struct.unpack("!Q", data[11:19])[0]
                stock = data[19:27].strip().decode('ascii')
                cross_price = struct.unpack("!I", data[27:31])[0] / 10000
                match_number = struct.unpack("!Q", data[31:39])[0]
                cross_type = data[39:40].decode('ascii')
                return f"Cross Trade - Time: {timestamp}, Stock: {stock}, Shares: {shares}, Price: ${cross_price:.4f}, Type: {cross_type}"

            else:
                return f"Unknown message type: {msg_type} (length: {len(data)})"

        except Exception as e:
            return f"Error parsing {msg_type} message: {e}"

    def listen(self, max_messages=None, filter_stocks=None, show_raw=False):
        """Listen for ITCH messages"""
        if not self.sock:
            print("Not connected. Call connect() first.")
            return

        print(f"Listening for ITCH messages... (Ctrl+C to stop)")
        if filter_stocks:
            print(f"Filtering for stocks: {filter_stocks}")

        try:
            while True:
                if max_messages and self.message_count >= max_messages:
                    break

                # Receive data
                data, addr = self.sock.recvfrom(65536)

                if len(data) < 2:
                    continue

                # Extract length and message
                length = struct.unpack("!H", data[0:2])[0]
                message = data[2:2 + length]

                if show_raw:
                    print(f"Raw: {message.hex()}")

                # Parse the message
                parsed = self.parse_message(message)

                if parsed:
                    # Apply stock filter if specified
                    if filter_stocks:
                        stock_found = any(stock in parsed for stock in filter_stocks)
                        if not stock_found:
                            continue

                    self.message_count += 1
                    print(f"[{self.message_count:06d}] {parsed}")

        except KeyboardInterrupt:
            print(f"\nStopped. Processed {self.message_count} messages.")
        except Exception as e:
            print(f"Error while listening: {e}")

    def close(self):
        """Close the socket connection"""
        if self.sock:
            self.sock.close()
            self.sock = None
            print("Connection closed.")


def main():
    # Create client
    client = ITCHClient()

    # Connect to multicast group
    if not client.connect():
        sys.exit(1)

    try:
        # Example usage:
        # Listen for all messages
        client.listen()

        # Or listen for specific stocks only:
        # client.listen(filter_stocks=['AAPL', 'MSFT', 'GOOGL'])

        # Or limit number of messages:
        # client.listen(max_messages=100)

        # Or show raw hex data:
        # client.listen(show_raw=True, max_messages=10)

    finally:
        client.close()


if __name__ == "__main__":
    main()