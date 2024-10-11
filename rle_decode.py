import os
import sys
import subprocess
import mmap
import array
from Bio import SeqIO
from concurrent.futures import ThreadPoolExecutor, as_completed

# def rle_decode_file(input_file, output_file, chunk_size=1024*1024*1000):
#     with open(input_file, 'rb') as infile, open(output_file, 'wb') as outfile:
#         buffer = bytearray()
        
#         while True:
#             chunk = infile.read(chunk_size)
#             if not chunk:
#                 break
            
#             buffer.extend(chunk)
            
#             while len(buffer) >= 2:
#                 count = (buffer[0] & 0x7F) + 1
#                 char = buffer[1]
#                 outfile.write(bytes([char] * count))
#                 buffer = buffer[2:]
#     os.remove(input_file)
    
# def rle_decode_file_optimized(input_file, output_file, chunk_size=1024*1024*100):
#     with open(input_file, 'rb') as infile, open(output_file, 'wb') as outfile:
#         # Memory-mapped file for faster reading
#         mm = mmap.mmap(infile.fileno(), 0, access=mmap.ACCESS_READ)
        
#         buffer = bytearray()
#         output_buffer = array.array('B')
        
#         file_size = os.path.getsize(input_file)
#         position = 0
        
#         while position < file_size:
#             chunk = mm[position:position+chunk_size]
#             position += chunk_size
            
#             buffer.extend(chunk)
            
#             i = 0
#             while i < len(buffer) - 1:
#                 count = (buffer[i] & 0x7F) + 1
#                 char = buffer[i+1]
#                 output_buffer.extend([char] * count)
#                 i += 2
            
#             if len(output_buffer) >= chunk_size:
#                 outfile.write(output_buffer)
#                 output_buffer = array.array('B')
            
#             buffer = buffer[i:]
        
#         if output_buffer:
#             outfile.write(output_buffer)
        
#         mm.close()
    
#     os.remove(input_file)

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

def rle_encode_file(input_file, output_file, chunk_size=1024*1024):
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

def decompress_with_zpaq(id_file, qual_file):
    # 각각 id.zpaq, qual.zpaq 파일 복원
    zpaq_cmd_id = f"zpaq x {id_file}"
    zpaq_cmd_qual = f"zpaq x {qual_file}"
    
    try:
        subprocess.run(zpaq_cmd_id, shell=True, check=True)
        subprocess.run(zpaq_cmd_qual, shell=True, check=True)
        print(f"복원된 파일: {id_file}, {qual_file}")
    except subprocess.CalledProcessError as e:
        print(f"복원 중 오류 발생: {e}")

    os.remove(f"{id_file}")
    os.remove(f"{qual_file}")
    
    

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
    qual_decompressed_file = f"{qual_basename}_decompess.txt"
    rle_decode_file_optimized(f"/home/donggyu/cmc/STAQ/SRR30480369_1.fastq_qual_rle", 'qual_decompressed_file_test')
