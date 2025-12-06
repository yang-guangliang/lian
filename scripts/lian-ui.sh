#! /bin/sh

DIR=$(dirname $(realpath $0))

streamlit run $DIR/app.py
