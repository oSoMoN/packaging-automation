#!/bin/bash
set -eu

ROOT=$(dirname "$(readlink -f "$0")")

source "$ROOT/logging-functions.sh"
source "$ROOT/telegram-bot-functions.sh"

CHANNEL=$1
TG_TOKEN=$2
TG_CHAT_ID=$3
CHANNEL_FILE="chromium-last-version-$CHANNEL.txt"

if [[ -f $CHANNEL_FILE ]]; then
  LAST_VERSION=$(cat $CHANNEL_FILE)
else
  LAST_VERSION="0.0.0.0"
fi

log_ts "Last known version for the $CHANNEL channel: $LAST_VERSION"

NEW_VERSION=$(curl -s "https://omahaproxy.appspot.com/all.json?os=linux&channel=$CHANNEL" | jq -r .[0].versions[0].current_version)

if [[ -z "$NEW_VERSION" ]]; then
  exit 0
fi

log_ts "Current version for the $CHANNEL channel: $NEW_VERSION"

if `dpkg --compare-versions $LAST_VERSION lt $NEW_VERSION`; then
  msg="New update in the $CHANNEL channel: $LAST_VERSION → $NEW_VERSION"
  echo $NEW_VERSION > $CHANNEL_FILE
  log_ts "$msg"
  send_tg_message "$TG_TOKEN" "$TG_CHAT_ID" "$msg"
else
  log_ts "No new version in the $CHANNEL channel, all up-to-date"
  exit 0
fi
