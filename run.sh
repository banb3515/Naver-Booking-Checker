#!/bin/bash

# Crontab 실행을 위한 스크립트

source /home/banb/miniconda3/etc/profile.d/conda.sh
conda activate naver-booking

cd /home/banb/repos/naver-booking
python app.py

conda deactivate
