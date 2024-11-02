import os
import sys
import subprocess
import mmap
import array
from Bio import SeqIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import Process

def rle_decode_file_optimized(input_file, output_file, chunk_size=1024*1024):
    with open(input_file, 'rb') as infile, open(output_file, 'wb') as outfile:
        buffer = bytearray()
        total_read = 0
        total_written = 0
        
        while True:
            chunk = infile.read(chunk_size)
            if not chunk:
                break
            
            buffer.extend(chunk)
            total_read += len(chunk)
            
            i = 0
            while i < len(buffer) - 1:
                count = (buffer[i] & 0x7F) + 1
                char = buffer[i + 1]
                decoded = bytes([char] * count)
                outfile.write(decoded)
                total_written += count
                i += 2
            
            buffer = buffer[i:]
        
        # 남은 버퍼 처리
        if len(buffer) == 1:
            outfile.write(buffer)
            total_written += 1
        
        print(f"Total bytes read: {total_read}")
        print(f"Total bytes written: {total_written}")
        os.remove(input_file)

def run_zpaq(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"명령 실행 완료: {cmd}")
    except subprocess.CalledProcessError as e:
        print(f"복원 중 오류 발생: {e}")
    
def process_files(qual_file):
    qual_basename = os.path.splitext(os.path.basename(qual_file))[0]

    zpaq_cmd_qual_file = f"zpaq x {qual_file}"
    run_zpaq(zpaq_cmd_qual_file)
    rle_decode_file_optimized(f"merged_qual_rle", f"{qual_basename}_decompress.txt")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 pe_decode.py <qual_file1>")
        sys.exit(1)

    process_files(sys.argv[1])