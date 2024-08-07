#!/bin/bash

pip install langchain_community tqdm nvidia-ml-py3

BASE_URL="http://127.0.0.1:11434"
OUTPUT_PATH="./output"

#MODELS=( qwen2:0.5b )
#MODELS=( qwen2:0.5b qwen2:1.5b qwen2:7b qwen2:72b )
MODELS=( gemma2:2b gemma2:9b gemma2:27b )


# Force model download to avoid too long delays between experiments
#for MODEL in "${MODELS[@]}"; do
#   curl $BASE_URL/api/pull -d '{"name": "'"${MODEL}"'"}'
#done


for MODEL in "${MODELS[@]}"; do
   curl -X POST $BASE_URL/api/pull -d '{"name": "'"${MODEL}"'"}'
   echo "Running script for model ${MODEL}"
   python token_rate.py --base_url $BASE_URL --model=$MODEL --output=$OUTPUT_PATH --loops=17
   curl -X DELETE $BASE_URL/api/delete -d '{"name": "'"${MODEL}"'"}'
done
