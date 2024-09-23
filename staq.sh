#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 6 ]; then
    echo "Usage: ./staq.sh [-c|-d] -i input.fastq [--deep] -o output.sdzip"
    exit 1
fi

# Mode selection
mode=""

# Set input and output files
input_file=""
output_file=""
deep_option=""

# Process input arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        -c)
            mode="-c"
            shift
            ;;
        -d)
            mode="-d"
            shift
            ;;
        -i)
            input_file=$2
            shift 2
            ;;
        --deep)
            deep_option="--deep"
            shift
            ;;
        -o)
            output_file=$2
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# If neither compression nor decompression mode is specified
if [ -z "$mode" ]; then
    echo "You must select either -c (compression) or -d (decompression) mode."
    exit 1
fi

# If input or output files are not specified
if [ -z "$input_file" ] || [ -z "$output_file" ]; then
    echo "You must specify both input and output files."
    exit 1
fi

# Execute final command
if [ "$mode" == "-c" ]; then
    # Compression mode
    if [ -z "$deep_option" ]; then
        ./spring/build/spring -c -i "$input_file" --no-ids --no-quality -o "$output_file" &
        python3 split_id_qual.py "$input_file" &
        wait

    else
        ./spring/build/spring -c -i "$input_file" --no-ids --no-quality --deep -o "$output_file" &
        python3 split_id_qual.py "$input_file" &
        wait
    fi
elif [ "$mode" == "-d" ]; then
    # Decompression mode
    if [ -z "$deep_option" ]; then
        ./spring/build/spring -d -i "$input_file" -o "$output_file" &
        python3 split_id_qual.py "$input_file" &
        wait
    else
        ./spring/build/spring -d -i "$input_file" --deep -o "$output_file" &
        python3 split_id_qual.py "$input_file" &
        wait
fi

echo "Operation completed: $output_file"
