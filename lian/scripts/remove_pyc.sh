#!/bin/bash



remove_pycache() {
    find "$1" -type d -name '__pycache__' -exec rm -rf {} +
}

remove_pycache $1
