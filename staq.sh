#!/bin/bash

# # Check if the correct number of arguments is provided
# if [ "$#" -lt 6 ]; then
#     echo "Usage: ./staq.sh [-c|-d] -i input1.fastq [input2.fastq] [--deep] [-l] -o output.staq [--gpu-id gpu_id (Using Deep)]"
#     exit 1
# fi

# # Mode selection
# mode=""

# # Set input and output files
# input_file1=""
# input_file2=""
# output_file=""
# deep_option=""
# gpu_id=""
# long_option=""

# # Process input arguments
# while [ "$#" -gt 0 ]; do
#     case "$1" in
#         -c)
#             mode="-c"
#             shift
#             ;;
#         -d)
#             mode="-d"
#             shift
#             ;;
#         -i)
#             input_file1=$2
#             if [[ "$3" != "-"* && "$3" != "" ]]; then  # 두 번째 입력 파일이 있는지 확인
#                 input_file2=$3
#                 shift 3
#             else
#                 shift 2
#             fi
#             ;;
#         --deep)
#             deep_option="--deep"
#             shift
#             ;;
#         --gpu-id)
#             gpu_id=$2  # GPU ID 값을 받음
#             shift 2
#             ;;
#         -l)
#             long_option="-l"  # long read 옵션 활성화
#             shift
#             ;;
#         -o)
#             output_file=$2
#             shift 2
#             ;;
#         *)
#             echo "Unknown option: $1"
#             exit 1
#             ;;
#     esac
# done

# # If neither compression nor decompression mode is specified
# if [ -z "$mode" ]; then
#     echo "You must select either -c (compression) or -d (decompression) mode."
#     exit 1
# fi

# # If input or output files are not specified
# if [ -z "$input_file1" ] || [ -z "$output_file" ]; then
#     echo "You must specify at least one input file and an output file."
#     exit 1
# fi

# # Execute final command
# if [ "$mode" == "-c" ]; then
#     output_base_name="${output_file%.*}"
#     # Compression mode
#     if [ -z "$deep_option" ]; then
#         if [ -z "$input_file2" ]; then
#             ./Spring/build/spring -c -i "$input_file1" --no-ids --no-quality $long_option -o "$output_base_name.spring" &
#             python3 split_id_qual.py "$input_file1" &
#         else
#             ./Spring/build/spring -c -i "$input_file1" "$input_file2" --no-ids --no-quality $long_option -o "$output_base_name.spring" &
#             python3 split_id_qual.py "$input_file1" "$input_file2" &
#         fi
#         wait
#     else
#         if [ -z "$input_file2" ]; then
#             ./Spring/build/spring -c -i "$input_file1" --no-ids --no-quality --deep --gpu-id "$gpu_id" $long_option -o "$output_base_name.spring" &
#             python3 split_id_qual.py "$input_file1" &
#         else
#             ./Spring/build/spring -c -i "$input_file1" "$input_file2" --no-ids --no-quality --deep --gpu-id "$gpu_id" $long_option -o "$output_base_name.spring" &
#             python3 split_id_qual.py "$input_file1" "$input_file2" &
#         fi
#         wait
#     fi
#     # tar로 결과 파일을 묶기
#     tar -cf "${output_file}" "$output_base_name.spring" *.zpaq *_metadata.txt
#     rm -f *.spring *.zpaq *.combined
#     rm -f *.spring *.zpaq *_metadata.txt

# elif [ "$mode" == "-d" ]; then
#     # tar 압축 해제
#     tar -xf "${input_file1}" -C .
#     spring_file=$(find . -maxdepth 1 -type f -name "*.spring" -print -quit)
#     id_zpaq_file=$(find . -maxdepth 1 -type f -name "*id.zpaq" -print -quit)
#     qual_zpaq_file=$(find . -maxdepth 1 -type f -name "*qual.zpaq" -print -quit)

#     output_base_name="${output_file%.*}"
#     id_base_name="${id_zpaq_file%.*}"
#     qual_base_name="${qual_zpaq_file%.*}"

#     echo "$output_base_name, $id_base_name, $qual_base_name"

#     if [ -z "$spring_file" ]; then
#         echo ".spring 확장자로 끝나는 파일을 찾을 수 없습니다."
#         exit 1
#     fi

#     # Decompression mode
#     if [ -z "$deep_option" ]; then
#         ./Spring/build/spring -d -i "$spring_file" -o "$output_base_name.seq" &
#         python3 rle_decode.py "$id_zpaq_file" "$qual_zpaq_file"
#         wait
#     else
#         ./Spring/build/spring -d -i "$spring_file" --deep --gpu-id "$gpu_id" -o "$output_base_name.seq" &
#         python3 rle_decode.py "$id_zpaq_file" "$qual_zpaq_file"
#         wait
#     fi
#     python3 combine.py "$id_base_name.txt" "$output_base_name.seq" "${qual_base_name}_decompress.txt" "$output_base_name.fastq"
#     rm -f *_metadata.txt
# fi

# echo "Operation completed: $output_file"

#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 5 ]; then
    echo "Usage: ./staq.sh [-c|-d] -i input1.fastq [input2.fastq] [--deep] [-l] -o output.staq [--gpu-id gpu_id (Using Deep)]"
    exit 1
fi

# Variables
mode=""
input_file1=""
input_file2=""
output_file=""
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
        -o) output_file=$2; shift 2 ;;
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
            ../Spring/build/spring -c -i "$input_file1" --no-ids --no-quality $long_option -o "$output_base_name.spring" &
            python3 ../split_id_qual.py "$input_file1" &
        else
            ../Spring/build/spring -c -i "$input_file1" "$input_file2" --no-ids --no-quality $long_option -o "$output_base_name.spring" &
            python3 ../split_id_qual.py "$input_file1" "$input_file2" &
        fi
    else
        if [ -z "$input_file2" ]; then
            ../Spring/build/spring -c -i "$input_file1" --no-ids --no-quality --deep --gpu-id "$gpu_id" $long_option -o "$output_base_name.spring" &
            python3 ../split_id_qual.py "$input_file1" &
        else
            ../Spring/build/spring -c -i "$input_file1" "$input_file2" --no-ids --no-quality --deep --gpu-id "$gpu_id" $long_option -o "$output_base_name.spring" &
            python3 ../split_id_qual.py "$input_file1" "$input_file2" &
        fi
    fi
    wait

    tar -cf "../$output_file" "$output_base_name.spring" *.zpaq *_metadata.txt
    rm -f *.spring *.zpaq *_metadata.txt

# Execute Decompression
elif [ "$mode" == "-d" ]; then
    tar -xf "../$input_file1" -C .
    spring_file=$(find . -maxdepth 1 -type f -name "*.spring" -print -quit)
    id_zpaq_file=$(find . -maxdepth 1 -type f -name "*id.zpaq" -print -quit)
    qual_zpaq_file=$(find . -maxdepth 1 -type f -name "*qual.zpaq" -print -quit)

    output_base_name="${output_file%.*}"
    id_base_name="${id_zpaq_file%.*}"
    qual_base_name="${qual_zpaq_file%.*}"

    if [ -z "$spring_file" ]; then
        echo ".spring file not found."
        exit 1
    fi

    if [ -z "$deep_option" ]; then
        ../Spring/build/spring -d -i "$spring_file" -o "$output_base_name.seq" &
        python3 ../rle_decode.py "$id_zpaq_file" "$qual_zpaq_file" &
    else
        ../Spring/build/spring -d -i "$spring_file" --deep --gpu-id "$gpu_id" -o "$output_base_name.seq" &
        python3 ../rle_decode.py "$id_zpaq_file" "$qual_zpaq_file" &
    fi
    wait

    python3 ../combine.py "$id_base_name.txt" "$output_base_name.seq" "${qual_base_name}_decompress.txt" "../$output_base_name.fastq"
    rm -f *_metadata.txt
fi

# Clean up and finish
cd ..
rm -rf "$work_dir"
echo "Operation completed: $output_file"
