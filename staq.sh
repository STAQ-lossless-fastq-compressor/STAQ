#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 6 ]; then
    echo "Usage: ./staq.sh [-c|-d] -i input.fastq [--deep] -o output.staq [--gpu-id gpu_id (Using Deep)]"
    exit 1
fi

# Mode selection
mode=""

# Set input and output files
input_file=""
output_file=""
deep_option=""
gpu_id=""

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
        --gpu-id)
            gpu_id=$2  # GPU ID 값을 받음
            shift 2
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
        ./Spring/build/spring -c -i "$input_file" --no-ids --no-quality --deep --gpu-id "$gpu_id" -o "staq.spring" &
        python3 split_id_qual.py "$input_file" &
        wait
    fi
    # tar로 결과 파일을 묶기
    # tar -cf "${output_file}" *.spring *.zpaq *.combined
    tar -cf "${output_file}" *.spring *.zpaq *_metadata.txt
    # rm -f *.spring *.zpaq *.combined
    rm -f *.spring *.zpaq *_metadata.txt

elif [ "$mode" == "-d" ]; then
    # tar 압축 해제
    tar -xf "${input_file}" -C .
    spring_file=$(find . -maxdepth 1 -type f -name "*.spring" -print -quit)
    id_zpaq_file=$(find . -maxdepth 1 -type f -name "*id.zpaq" -print -quit)
    qual_zpaq_file=$(find . -maxdepth 1 -type f -name "*qual.zpaq" -print -quit)

    output_base_name="${output_file%.*}"
    id_base_name="${id_zpaq_file%.*}"
    qual_base_name="${qual_zpaq_file%.*}"

    echo "$output_base_name, $id_base_name, $qual_base_name"

    if [ -z "$input_file" ]; then
    echo ".spring 확장자로 끝나는 파일을 찾을 수 없습니다."
    exit 1
    fi

    # Decompression mode
    if [ -z "$deep_option" ]; then
        ./Spring/build/spring -d -i "$spring_file" -o "$output_base_name.seq" &
        python3 rle_decode.py "$id_zpaq_file" "$qual_zpaq_file"
        wait
    else
        ./Spring/build/spring -d -i "$spring_file" --deep --gpu-id "$gpu_id" -o "$output_base_name.seq" &
        python3 rle_decode.py "$id_zpaq_file" "$qual_zpaq_file"
        wait
    fi
    python3 combine.py "$id_base_name.txt" "$output_base_name.seq" "${qual_base_name}_decompress.txt" "$output_base_name.fastq"
    rm -f *_metadata.txt
fi

echo "Operation completed: $output_file"
