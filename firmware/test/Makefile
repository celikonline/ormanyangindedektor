# ON-1 saf mantik birim testleri (PC). Kullanim:  make  (veya: make CXX=clang++)
CXX      ?= g++
CXXFLAGS ?= -std=c++11 -O1 -g -Wall -Wextra -Wno-unused-parameter
SRC_DIR  := ../OrmanNobetcisi
SRCS     := test_logic.cpp $(SRC_DIR)/storage.cpp $(SRC_DIR)/textutil.cpp \
            $(SRC_DIR)/detector.cpp $(SRC_DIR)/commands.cpp

all: run

test_logic: $(SRCS) $(wildcard $(SRC_DIR)/*.h)
	$(CXX) $(CXXFLAGS) -I$(SRC_DIR) -o $@ $(SRCS)

run: test_logic
	./test_logic

clean:
	rm -f test_logic test_logic.exe

.PHONY: all run clean
