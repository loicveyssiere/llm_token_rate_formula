#!/bin/bash

pip3 install langchain_community tqdm nvidia-ml-py3

BASE_URL="http://192.168.30.240:11434"
OUTPUT_PATH="./output"

#MODELS=( qwen2:0.5b )
MODELS=( qwen2:0.5b qwen2:1.8b qwen2:4b qwen2:7b qwen2:7b-chat-q5_0 qwen2:7b-chat-q6_K qwen2:7b-chat-q8_0 qwen2:7b-chat-fp16 qwen2:14b qwen2:32B qwen2:72B qwen2:110B )


# Force model download to avoid too long delays between experiments
for MODEL in "${MODELS[@]}"; do
   curl $BASE_URL/api/pull -d '{"name": "'"${MODEL}"'"}'
done


for MODEL in "${MODELS[@]}"; do
   echo "Running script for model ${MODEL}"
   python token_rate.py --base_url $BASE_URL --model=$MODEL --output=$OUTPUT_PATH --loops=1
done
