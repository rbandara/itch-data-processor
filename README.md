# NASDAQ ITCH Data Simulator and Client

## Overview
This project provides a **high-performance C++ client** and a **Python-based simulator** for processing and replaying NASDAQ ITCH 5.0 market data messages. The ITCH protocol is used by NASDAQ to disseminate real-time order book and trade data, critical for high-frequency trading (HFT) and market analysis. The C++ client connects to a UDP multicast group, parses ITCH messages (e.g., Add Order, Trade, System Event), and tracks performance metrics like messages per second. The Python simulator replays historical ITCH data files over multicast, simulating a live exchange feed.

Key features:
- **Low-Latency C++ Client**: Parses ITCH messages with optimized memory access and endianness handling, achieving sub-microsecond processing (benchmarked at ~1M messages/sec on a single core).
- **Python Simulator**: Replays ITCH 5.0 binary files with configurable pacing for realistic testing.

## Project Structure
- `itch_client.cpp`: C++ client for receiving and parsing ITCH messages via UDP multicast.
- `itch_replay.py`: Python script for replaying ITCH binary files over multicast.
- **Dependencies**: Standard C++ libraries (C++17), Python 3, POSIX sockets.

## Setup Instructions

### Prerequisites
- **C++ Client**:
  - Compiler: g++ or clang++ (C++17 support)
  - OS: Linux/Unix (tested on Ubuntu 20.04)
  - Libraries: Standard POSIX socket libraries (`sys/socket.h`, `netinet/in.h`)
- **Python Simulator**:
  - Python: 3.8+
  - Modules: `socket`, `struct`, `time`
  - Sample ITCH data file (e.g., `01302019.NASDAQ_ITCH50` from NASDAQ's public datasets)

### Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/nasdaq-itch-simulator.git
   cd nasdaq-itch-simulator
   ```

2. **Compile the C++ Client**:
   ```bash
   g++ -std=c++17 -o itch_client itch_client.cpp
   ```

3. **Prepare ITCH Data**:
   - Download a sample ITCH 5.0 file (e.g., from NASDAQ's FTP or test datasets).- ex:`https://emi.nasdaq.com/ITCH/Nasdaq%20ITCH/`
   - Place it in the project directory (e.g., `data/01302019.NASDAQ_ITCH50`).

## Usage

### Running the Simulator
1. Start the Python simulator to replay ITCH data over multicast:
   ```bash
   python3 itch_replay.py
   ```
   - Configurable parameters in `itch_replay.py`:
     - `MCAST_GRP`: Multicast group (default: `239.192.0.1`)
     - `MCAST_PORT`: Port (default: `12345`)
     - `time.sleep(0.0001)`: Adjust pacing for realistic replay speed.

2. The simulator reads the ITCH binary file and sends messages to the specified multicast group.

### Running the Client
1. Start the C++ client to listen for and parse ITCH messages:
   ```bash
   ./itch_client
   ```
   - Connects to `239.192.0.1:12345` by default.
   - Outputs parsed messages (e.g., System Events, Add Orders, Trades) with formatted timestamps.
   - Prints performance stats every 1000 messages and a final summary (e.g., messages/sec).

2. Example output:
   ```
   Connected to 239.192.0.1:12345
   Listening for messages... (Ctrl+C to stop)
   System Event - Time: 09:30:00.123, Event: S
   Add Order - Time: 09:30:00.124, Stock: AAPL    , Side: B
   Processed 1000 messages, 500000.0 msg/sec
   Final stats: 5000 messages in 10ms (500000.0 msg/sec)
   ```

### Testing Locally
- Run the simulator in one terminal and the client in another.
- Ensure both use the same multicast group and port.
- Use a sample ITCH file or generate synthetic data for testing (see "Future Enhancements").

## Performance Metrics
- **C++ Client**:
  - Throughput: ~1M messages/sec on a single core (tested on AWS c5.large, 3.0 GHz CPU).
  - Latency: ~150ns per message parse (optimized with cache-aligned buffers and lock-free counters).
  - Memory: Minimal footprint, using fixed-size buffers
