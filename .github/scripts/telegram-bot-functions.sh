TG_TOKEN=$1
TG_CHAT_ID=$2
MESSAGE=$3

function send_tg_message {
  curl -s \
    --data-urlencode "chat_id=$TG_CHAT_ID" \
    --data-urlencode "text=$MESSAGE" \
    "https://api.telegram.org/bot$TG_TOKEN/sendMessage"
  echo
}
