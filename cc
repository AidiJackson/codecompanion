#!/bin/bash
case "$1" in
    "") codecompanion --check ;;
    "auto") codecompanion --auto ;;
    "check") codecompanion --check ;;
    *) codecompanion "$@" ;;
esac
