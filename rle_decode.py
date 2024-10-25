import os
import sys
import subprocess
import mmap
import array
from Bio import SeqIO
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def decompress_with_zpaq(id_file, qual_file):
    zpaq_cmd_id = f"zpaq x {id_file}"
    zpaq_cmd_qual = f"zpaq x {qual_file}"

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(run_zpaq, zpaq_cmd_id),
            executor.submit(run_zpaq, zpaq_cmd_qual)
        ]

        # 모든 작업이 끝날 때까지 대기
        for future in futures:
            future.result()

    os.remove(id_file)
    os.remove(qual_file)
    

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 split_id_qual.py <id_file> <qual_file>")
        sys.exit(1)
    
    id_file = sys.argv[1]
    qual_file = sys.argv[2]

    qual_basename = os.path.basename(qual_file)
    qual_basename = os.path.splitext(qual_basename)[0]  # 확장자 제거
    
    # id.zpaq와 qual.zpaq 압축 해제
    decompress_with_zpaq(id_file, qual_file)
    
    # qual 파일 RLE 디코딩
    qual_decompressed_file = f"{qual_basename}_decompress.txt"
    rle_decode_file_optimized(f"{qual_basename}_rle", qual_decompressed_file)