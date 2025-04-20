#!/usr/bin/env python3

import os,sys

def get_user_input(prompt):
    input_wrap = input
    return input_wrap(prompt).upper()

name = get_user_input("Please enter your name: ")
print(f"Hello, {name}!")
