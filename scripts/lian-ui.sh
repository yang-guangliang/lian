#! /bin/sh

DIR=$(dirname $(realpath $0))

streamlit run $DIR/app.py --server.showEmailPrompt false  --theme.base light
