function send_tg_message {
  curl -s \
    --data-urlencode "chat_id=$2" \
    --data-urlencode "text=$3" \
    "https://api.telegram.org/bot$1/sendMessage"
  echo
}
