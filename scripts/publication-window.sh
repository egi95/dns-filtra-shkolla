#!/usr/bin/env bash
# Interpret every check in the school timezone, including daylight-saving changes.
export TZ=Europe/Belgrade
hour=$(date +%H)
if (( 10#$hour >= 7 && 10#$hour < 17 )); then
  echo "Publikimi pret deri ne oren 17:00 te shkolles." >&2
  exit 1
fi
