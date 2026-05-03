#!/bin/bash

OUTPUT_DIR=$1
if [ -z "$OUTPUT_DIR" ]; then
    echo "Usage: $0 <OUTPUT_DIR>"
    exit 1
fi

ls "$OUTPUT_DIR/raw_scenes/"*_final.mp4 | sort | sed "s|^|file '|" | sed "s|$|'|" > file_list.txt

if [ -s file_list.txt ]; then
    echo "Stitching the following scenes into final_movie.mp4:"
    cat file_list.txt
    # Use ffmpeg concat demuxer to stitch them together
    ffmpeg -y -f concat -safe 0 -i file_list.txt -c copy "$OUTPUT_DIR/final_movie.mp4"
    echo "Done! Final movie saved to $OUTPUT_DIR/final_movie.mp4"
    rm file_list.txt
else
    echo "No *_final.mp4 files found in $OUTPUT_DIR/raw_scenes/."
    rm file_list.txt
fi
