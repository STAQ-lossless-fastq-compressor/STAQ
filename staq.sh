#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 6 ]; then
    echo "Usage: ./staq.sh [-c|-d] -i input.fastq [--deep] -o output.staq"
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
        ./Spring/build/spring -c -i "$input_file" --no-ids --no-quality -o "staq.spring" &
        python3 split_id_qual.py "$input_file" &
        wait
    else
        ./Spring/build/spring -c -i "$input_file" --no-ids --no-quality --deep -o "staq.spring" &
        python3 split_id_qual.py "$input_file" &
        wait
    fi
    # tar로 결과 파일을 묶기
    tar -cf "${output_file}" *.spring *.zpaq *.combined
    rm -f *.spring *.zpaq *.combined

elif [ "$mode" == "-d" ]; then
    # tar 압축 해제
    tar -xf "${input_file}" -C .
    # Decompression mode
    if [ -z "$deep_option" ]; then
        ./Spring/build/spring -d -i "$input_file" -o "$output_file" &
        python3 split_id_qual.py "$input_file" &
        wait
    else
        ./Spring/build/spring -d -i "$input_file" --deep -o "$output_file" &
        python3 split_id_qual.py "$input_file" &
        wait
    fi
fi

echo "Operation completed: $output_file"
