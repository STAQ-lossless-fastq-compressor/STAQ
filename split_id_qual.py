import os
import sys
import subprocess
from Bio import SeqIO
from concurrent.futures import ThreadPoolExecutor, as_completed
import filecmp
import concurrent.futures

def delete_if_exists(filename):
    """Deletes the file if it exists."""
    if os.path.exists(filename):
        os.remove(filename)

def compress_with_zpaq(input_files, output_file):
    """Compresses input files using ZPAQ."""
    zpaq_cmd = f"zpaq a {output_file}.zpaq {input_files} -m5"
    try:
        subprocess.run(zpaq_cmd, shell=True, check=True)
        print(f"Compressed file created: {output_file}.zpaq")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during compression: {e}")

def rle_encode_file(input_file, output_file, chunk_size=1024*1024):
    """Encodes a file using RLE and writes the output to another file."""
    with open(input_file, 'rb') as infile, open(output_file, 'wb') as outfile:
        prev_char = None
        count = 0
        total_read = 0
        total_written = 0
        
        while True:
            chunk = infile.read(chunk_size)
            if not chunk:
                if prev_char is not None:
                    while count > 0:
                        write_count = min(count, 128)
                        outfile.write(bytes([(write_count - 1) | 0x80, prev_char]))
                        total_written += 2
                        count -= write_count
                break
            
            total_read += len(chunk)
            
            for char in chunk:
                if char == prev_char and count < 128:
                    count += 1
                else:
                    if prev_char is not None:
                        while count > 0:
                            write_count = min(count, 128)
                            outfile.write(bytes([(write_count - 1) | 0x80, prev_char]))
                            total_written += 2
                            count -= write_count
                    count = 1
                    prev_char = char
        
        print(f"Total bytes read: {total_read}")
        print(f"Total bytes written: {total_written}")

def process_records(file_path, output_prefix):
    """Processes the records in a FASTQ file and writes ID and quality score files."""
    # Delete existing files if they exist
    delete_if_exists(f"{output_prefix}_qual.txt")

    with open(file_path, "r") as handle, open(f"{output_prefix}_qual.txt", "w") as qual_file:
        for record in SeqIO.parse(handle, "fastq"):
            # Convert quality scores to ASCII characters
            quality_scores = ''.join(chr(q + 33) for q in record.letter_annotations['phred_quality'])

            # Write directly to files
            qual_file.write(quality_scores)

def process_file(file_path, output_prefix):
    """Processes a single input file and handles compression of ID and quality files."""
    process_records(file_path, output_prefix)
    print(f"Files saved: {output_prefix}_qual.txt")

    with ThreadPoolExecutor() as executor:    
        rle_encoded_file = f"{output_prefix}_qual_rle"
        rle_future = executor.submit(rle_encode_file, f"{output_prefix}_qual.txt", rle_encoded_file)

        rle_future.result()
        print(f"{output_prefix} Quality file RLE encoding completed.")
        # Compress the RLE encoded quality file within the ThreadPoolExecutor
        qual_future = executor.submit(compress_with_zpaq, rle_encoded_file, f"{output_prefix}_qual")
        qual_future.result()  # Wait for the compression to complete

    print(f"{output_prefix} Quality file compression completed.")

def merge_quality_files(file1, file2, output_file):
    with open(file1, 'r') as f1, open(file2, 'r') as f2, open(output_file, 'w') as out:
        # 첫 번째 파일의 내용을 읽어 쓰기
        out.write(f1.read())
        
        # 두 번째 파일의 내용을 읽어 쓰기
        out.write(f2.read())

def process_records_paired_end(file_path, output_prefix):
    """Processes the records in a FASTQ file and writes ID and quality score files."""
    # Delete existing files if they exist
    delete_if_exists(f"{output_prefix}_qual.txt")
    
    with open(file_path, "r") as handle, open(f"{output_prefix}_qual.txt", "w") as qual_file:
        for record in SeqIO.parse(handle, "fastq"):
            # Convert quality scores to ASCII characters
            quality_scores = ''.join(chr(q + 33) for q in record.letter_annotations['phred_quality'])

            # Write directly to files
            qual_file.write(quality_scores)

def process_file_paired_end(file_path, file_path2, output_prefix, output_prefix2):
    """Processes a single input file and handles compression of ID and quality files."""
    
    # ThreadPoolExecutor를 사용하여 두 작업을 동시에 실행
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(process_records_paired_end, file_path, output_prefix)
        future2 = executor.submit(process_records_paired_end, file_path2, output_prefix2)
        
        # 두 작업이 모두 완료될 때까지 기다림
        for future in as_completed([future1, future2]):
            future.result()  # 예외가 발생했다면 여기서 raise됨
 

    merge_quality_files(f"{output_prefix}_qual.txt", f"{output_prefix2}_qual.txt", "merged_qual.txt")

    print(f"Files saved: {output_prefix}_qual.txt")
    print(f"Files saved: {output_prefix2}_qual.txt")

    # 병합이 완료된 후 RLE 인코딩 실행
    rle_encoded_file = "merged_qual.rle"
    rle_encode_file("merged_qual.txt", rle_encoded_file)
    # Compress the RLE encoded quality file
    compress_with_zpaq(rle_encoded_file, f"{output_prefix}_qual")


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 split_id_qual.py <input_file1> [input_file2]")
        sys.exit(1)
        
    if len(sys.argv) == 3:
        file_path1 = sys.argv[1]
        file_path2 = sys.argv[2]
        output_prefix1 = os.path.basename(file_path1)
        output_prefix1, _ = os.path.splitext(output_prefix1)
        output_prefix2 = os.path.basename(file_path2)
        output_prefix2, _ = os.path.splitext(output_prefix2)
        
        process_file_paired_end(file_path1, file_path2, output_prefix1, output_prefix2)
    else:
        file_path1 = sys.argv[1]
        output_prefix1 = os.path.basename(file_path1)
        output_prefix1, _ = os.path.splitext(output_prefix1)
        
        process_file(file_path1, output_prefix1)

    print("All operations completed.")
