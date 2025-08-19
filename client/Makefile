# Simple Makefile for ITCH C++ Client

CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2
TARGET = itch_client
SOURCE = src/itch_client.cpp

# Default target
$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCE)

# Debug version
debug: CXXFLAGS += -g -DDEBUG -O0
debug: $(TARGET)

# Clean
clean:
	rm -f $(TARGET)

# Run with your simulator
test: $(TARGET)
	@echo "Make sure your Python simulator is running in another terminal:"
	@echo "python3 simulator.py"
	@echo "Then run: ./$(TARGET)"

.PHONY: debug clean test