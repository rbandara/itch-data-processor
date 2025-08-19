#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <chrono>
#include <iomanip>

class SimpleITCHClient {
private:
    int sock_fd;
    struct sockaddr_in addr;
    std::string mcast_group;
    int mcast_port;
    int message_count;

public:
    SimpleITCHClient(const std::string& group = "239.192.0.1", int port = 12345) 
        : sock_fd(-1), mcast_group(group), mcast_port(port), message_count(0) {}
    
    ~SimpleITCHClient() {
        if (sock_fd >= 0) {
            close(sock_fd);
        }
    }
    
    bool connect() {
        // Create UDP socket
        sock_fd = socket(AF_INET, SOCK_DGRAM, 0);
        if (sock_fd < 0) {
            perror("socket");
            return false;
        }
        
        // Allow port reuse
        int reuse = 1;
        if (setsockopt(sock_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
            perror("setsockopt");
            return false;
        }
        
        // Bind to port
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_addr.s_addr = INADDR_ANY;
        addr.sin_port = htons(mcast_port);
        
        if (bind(sock_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
            perror("bind");
            return false;
        }
        
        // Join multicast group
        struct ip_mreq mreq;
        mreq.imr_multiaddr.s_addr = inet_addr(mcast_group.c_str());
        mreq.imr_interface.s_addr = INADDR_ANY;
        
        if (setsockopt(sock_fd, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) < 0) {
            perror("setsockopt IP_ADD_MEMBERSHIP");
            return false;
        }
        
        std::cout << "Connected to " << mcast_group << ":" << mcast_port << std::endl;
        return true;
    }
    
    // Convert network byte order to host byte order
    uint16_t readUint16(const char* data) {
        uint16_t value;
        memcpy(&value, data, sizeof(value));
        return ntohs(value);
    }
    
    uint64_t readUint64(const char* data) {
        uint64_t value;
        memcpy(&value, data, sizeof(value));
        // Convert from big-endian (network) to host byte order
        return ((uint64_t)ntohl(value & 0xFFFFFFFF) << 32) | ntohl(value >> 32);
    }
    
    std::string formatTimestamp(uint64_t timestamp_ns) {
        // ITCH timestamps are nanoseconds since midnight
        uint64_t hours = timestamp_ns / 3600000000000ULL;
        timestamp_ns %= 3600000000000ULL;
        uint64_t minutes = timestamp_ns / 60000000000ULL;
        timestamp_ns %= 60000000000ULL;
        uint64_t seconds = timestamp_ns / 1000000000ULL;
        uint64_t ms = (timestamp_ns % 1000000000ULL) / 1000000ULL;
        
        char buffer[32];
        snprintf(buffer, sizeof(buffer), "%02llu:%02llu:%02llu.%03llu", 
                 hours, minutes, seconds, ms);
        return std::string(buffer);
    }
    
    void parseMessage(const char* data, int length) {
        if (length < 1) return;
        
        char msg_type = data[0];
        
        switch (msg_type) {
            case 'S': { // System Event Message
                if (length >= 12) {
                    uint64_t timestamp = readUint64(data + 5);
                    char event_code = data[11];
                    std::cout << "System Event - Time: " << formatTimestamp(timestamp) 
                              << ", Event: " << event_code << std::endl;
                }
                break;
            }
            
            case 'A': { // Add Order Message
                if (length >= 36) {
                    uint64_t timestamp = readUint64(data + 5);
                    char side = data[19];
                    std::string stock(data + 24, 8);
                    // Remove trailing spaces
                    stock.erase(stock.find_last_not_of(" ") + 1);
                    
                    std::cout << "Add Order - Time: " << formatTimestamp(timestamp) 
                              << ", Stock: " << stock 
                              << ", Side: " << side << std::endl;
                }
                break;
            }
            
            case 'P': { // Trade Message
                if (length >= 44) {
                    uint64_t timestamp = readUint64(data + 5);
                    char side = data[19];
                    std::string stock(data + 24, 8);
                    stock.erase(stock.find_last_not_of(" ") + 1);
                    
                    std::cout << "Trade - Time: " << formatTimestamp(timestamp) 
                              << ", Stock: " << stock 
                              << ", Side: " << side << std::endl;
                }
                break;
            }
            
            case 'L': { // Stock Directory Message (example, adjust fields as needed)
                // Check minimum length for Stock Directory message (e.g., 22 bytes for ITCH 5.0)
                if (length >= 22) {
                    std::string stock(data + 1, 8);
                    stock.erase(stock.find_last_not_of(" ") + 1);
                    std::cout << "Stock Directory - Stock: " << stock << std::endl;
                }
                break;
            }
            
            case 'D': { // Delete Order Message
                if (length >= 19) {
                    uint64_t timestamp = readUint64(data + 5);
                    std::cout << "Delete Order - Time: " << formatTimestamp(timestamp) << std::endl;
                }
                break;
            }
            
            case 'U': { // Replace Order Message
                if (length >= 35) {
                    uint64_t timestamp = readUint64(data + 5);
                    char side = data[19];
                    std::string stock(data + 24, 8);
                    stock.erase(stock.find_last_not_of(" ") + 1);
                    std::cout << "Replace Order - Time: " << formatTimestamp(timestamp)
                              << ", Stock: " << stock
                              << ", Side: " << side << std::endl;
                }
                break;
            }
            
            case 'X': { // Order Cancel Message
                if (length >= 23) {
                    uint64_t timestamp = readUint64(data + 5);
                    std::cout << "Order Cancel - Time: " << formatTimestamp(timestamp) << std::endl;
                }
                break;
            }
            
            default:
                std::cout << "Unknown message type: " << msg_type 
                          << " (length: " << length << ")" << std::endl;
                break;
        }
    }
    
    void listen(int max_messages = 0) {
        if (sock_fd < 0) {
            std::cerr << "Not connected. Call connect() first." << std::endl;
            return;
        }
        
        std::cout << "Listening for messages... (Ctrl+C to stop)" << std::endl;
        
        char buffer[65536];
        auto start_time = std::chrono::steady_clock::now();
        
        while (true) {
            if (max_messages > 0 && message_count >= max_messages) {
                break;
            }
            
            ssize_t bytes_received = recv(sock_fd, buffer, sizeof(buffer), 0);
            if (bytes_received < 0) {
                perror("recv");
                break;
            }
            
            if (bytes_received < 2) {
                continue;
            }
            
            // First 2 bytes are message length
            uint16_t msg_length = readUint16(buffer);
            
            if (bytes_received < msg_length + 2) {
                std::cerr << "Incomplete message" << std::endl;
                continue;
            }
            
            // Parse the ITCH message (skip the 2-byte length)
            parseMessage(buffer + 2, msg_length);
            
            message_count++;
            
            // Print stats every 1000 messages
            if (message_count % 1000 == 0) {
                auto now = std::chrono::steady_clock::now();
                auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(now - start_time);
                double msg_per_sec = (double)message_count * 1000.0 / duration.count();
                std::cout << "Processed " << message_count << " messages, " 
                          << std::fixed << std::setprecision(1) << msg_per_sec 
                          << " msg/sec" << std::endl;
            }
        }
        
        auto end_time = std::chrono::steady_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
        double msg_per_sec = (double)message_count * 1000.0 / duration.count();
        
        std::cout << "\nFinal stats: " << message_count << " messages in " 
                  << duration.count() << "ms (" << msg_per_sec << " msg/sec)" << std::endl;
    }
};

int main() {
    std::cout << "Simple ITCH Client Starting..." << std::endl;
    
    SimpleITCHClient client;
    
    if (!client.connect()) {
        std::cerr << "Failed to connect" << std::endl;
        return 1;
    }
    
    try {
        // Listen for messages (0 = infinite, or specify a number like 100)
        client.listen(0);
    } catch (...) {
        std::cerr << "Exception caught" << std::endl;
    }
    
    return 0;
}