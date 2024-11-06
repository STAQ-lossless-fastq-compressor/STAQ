#!/bin/bash

start_time=$(date +%s)

# Check if the correct number of arguments is provided
if [ "$#" -lt 5 ]; then
    echo "Usage: ./staq.sh -c -i input1.fastq [input2.fastq] [--deep] [--gpu-id gpu_id (Using Deep)] [-l] -o output.staq"
    echo "Usage: ./staq.sh -d -i input1.staq [--deep] [--gpu-id gpu_id (Using Deep)] [-l] -o output_1.fastq [output_2.fastq]"
    exit 1
fi


# Variables
mode=""
input_file1=""
input_file2=""
output_file=""
output_file2=""
deep_option=""
gpu_id=""
long_option=""
work_dir="staq_temp_$(date +%s)"  # Unique temporary directory

# Process input arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        -c) mode="-c"; shift ;;
        -d) mode="-d"; shift ;;
        -i)
            input_file1=$2
            if [[ "$3" != "-"* && "$3" != "" ]]; then
                input_file2=$3
                shift 3
            else
                shift 2
            fi
            ;;
        --deep) deep_option="--deep"; shift ;;
        --gpu-id) gpu_id=$2; shift 2 ;;
        -l) long_option="-l"; shift ;;
        -o)
            output_file=$2
            if [[ "$3" != "-"* && "$3" != "" ]]; then
                output_file2=$3
                shift 3
            else
                shift 2
            fi
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Ensure mode and necessary files are specified
if [ -z "$mode" ]; then
    echo "You must select either -c (compression) or -d (decompression) mode."
    exit 1
fi

if [ -z "$input_file1" ] || [ -z "$output_file" ]; then
    echo "You must specify at least one input file and an output file."
    exit 1
fi

# Create a temporary working directory and move there
mkdir -p "$work_dir"
cd "$work_dir" || { echo "Failed to enter directory: $work_dir"; exit 1; }

# Execute Compression
if [ "$mode" == "-c" ]; then
    output_base_name="${output_file%.*}"
    
    if [ -z "$deep_option" ]; then
        if [ -z "$input_file2" ]; then
            ../Spring/build/spring -c -i "$input_file1" --no-quality $long_option -o "$output_base_name.spring" &
            python3 ../split_id_qual.py "$input_file1" &
        else
            ../Spring/build/spring -c -i "$input_file1" "$input_file2" --no-quality $long_option -o "$output_base_name.spring" &
            python3 ../split_id_qual.py "$input_file1" "$input_file2" &
        fi
    else
        if [ -z "$input_file2" ]; then
            ../Spring/build/spring -c -i "$input_file1" --no-quality --deep --gpu-id "$gpu_id" $long_option -o "$output_base_name.spring" &
            python3 ../split_id_qual.py "$input_file1" &
        else
            ../Spring/build/spring -c -i "$input_file1" "$input_file2" --no-quality --deep --gpu-id "$gpu_id" $long_option -o "$output_base_name.spring" &
            python3 ../split_id_qual.py "$input_file1" "$input_file2" &
        fi
    fi
    wait

    tar -cf "../$output_file" "$output_base_name.spring" *.zpaq *_metadata.txt

elif [ "$mode" == "-d" ]; then
    tar -xf "../$input_file1" -C .
    spring_file=$(find . -maxdepth 1 -type f -name "*.spring" -print -quit)
    qual_zpaq_file1=$(find . -maxdepth 1 -type f -name "*_1_qual.zpaq" -print -quit)

    if [ -z "$qual_zpaq_file1" ]; then
        qual_zpaq_file1=$(find . -maxdepth 1 -type f -name "*_qual.zpaq" -print -quit)
    fi

    output_base_name="${output_file%.*}"
    if [ -n "$output_file2" ]; then
        output_base_name2="${output_file2%.*}"
    fi

    qual_base_name1="${qual_zpaq_file1%.*}"

    if [ -z "$spring_file" ]; then
        echo ".spring file not found."
        exit 1
    fi

    if [ -z "$deep_option" ]; then
        if [ -n "$output_file2" ]; then
            ../Spring/build/spring -d -i "$spring_file" -o "$output_base_name.seq" "$output_base_name2.seq" &
            python3 ../pe_decode.py "$qual_zpaq_file1" &
        else
            ../Spring/build/spring -d -i "$spring_file" -o "$output_base_name.seq" &
            python3 ../rle_decode.py "$qual_zpaq_file1" &
        fi
    else
        if [ -n "$output_file2" ]; then
            ../Spring/build/spring -d -i "$spring_file" --deep --gpu-id "$gpu_id" -o "$output_base_name.seq" "$output_base_name2.seq" &
            python3 ../pe_decode.py "$qual_zpaq_file1" &
        else
            ../Spring/build/spring -d -i "$spring_file" --deep --gpu-id "$gpu_id" -o "$output_base_name.seq" &
            python3 ../rle_decode.py "$qual_zpaq_file1" &
        fi
    fi
    wait

    if [ -n "$output_file2" ]; then
        python3 ../combine.py "$output_base_name.seq" "${qual_base_name1}_decompress.txt" "../${output_base_name}.fastq" "$output_base_name2.seq" "../${output_base_name2}.fastq"
    else
        python3 ../combine.py "$output_base_name.seq" "${qual_base_name1}_decompress.txt" "../${output_base_name}.fastq"
    fi
fi

# Clean up and finish
cd ..
rm -rf "$work_dir"
echo "Operation completed: $output_file"

end_time=$(date +%s)
elapsed=$((end_time - start_time))
echo "Elapsed time: $elapsed seconds"