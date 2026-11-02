#!/bin/bash
cd "$(dirname "$0")"
for U in 4 6 8 10; do OMP_NUM_THREADS=1 nohup python3 -I vawt2d.py $U 4.0 64 case_U$U 3 50 0 0.33 2.4 > case_U$U.log 2>&1 & done
