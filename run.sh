#!/bin/bash

pip3 install langchain_community tqdm nvidia-ml-py3

BASE_URL="http://192.168.30.240:11434"
OUTPUT_PATH="./output"
MODELS=( qwen2:0.5b )

#for MODEL in "${MODELS[@]}"; do
#   curl $BASE_URL/api/pull -d '{"name": "'"${MODEL}"'"}'
#done


for MODEL in "${MODELS[@]}"; do
   echo "Running script for model ${MODEL}"
   python token_rate.py --base_url $BASE_URL --model=$MODEL --output=$OUTPUT_PATH
done
