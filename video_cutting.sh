#!/bin/bash

# Check for input file 
if [ -z "$1" ]; then
    echo "Usage: $0 [input_video]"
    exit 1
fi

input="$1"

# Check if file exists
if [ ! -f "$input" ]; then
    echo "Error: File '$input' not found!"
    exit 1
fi

# Get video duration (seconds)
duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$input")

# Convert to integer seconds
total_seconds=$(printf "%.0f" "$duration")

chunk_length=5
counter=0
start=0

while [ "$start" -lt "$total_seconds" ]; do
    end=$(( start + chunk_length ))

    # Don't go past total duration
    if [ "$end" -gt "$total_seconds" ]; then
        end=$total_seconds
    fi

    ffmpeg -i "$input" \
           -ss "$(printf '%02d:%02d:%05.2f' $((start/3600)) $(((start/60)%60)) $(bc <<< "$start%60"))" \
           -to "$(printf '%02d:%02d:%05.2f' $((end/3600)) $(((end/60)%60)) $(bc <<< "$end%60"))" \
           -c copy "${input%.*}_cut_${counter}.mp4"

    start=$end
    counter=$(( counter + 1 ))
done
