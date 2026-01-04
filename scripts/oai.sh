#!/bin/bash

oai() {
  curl -s https://api.openai.com/v1/responses \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --arg q "$*" '{
      model: "gpt-5",
      instructions: "talk like dis: casual, a lil typo-y, short sentences, friendly, use emojis sometimes. no big formal tone.",
      input: $q
    }')" \
  | jq -r '.output_text'
}

oai "$@"