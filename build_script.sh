#!/bin/bash
PROJECT_DIR="/Users/jackmazac/Development/RED4ext"
cd "$PROJECT_DIR"
rm -rf build
/usr/bin/cmake -B build -S . -DCMAKE_BUILD_TYPE=Debug > "$PROJECT_DIR/build_log.txt" 2>&1
/usr/bin/cmake --build build --target RED4ext.Dll >> "$PROJECT_DIR/build_log.txt" 2>&1
