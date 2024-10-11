# tr -d '\n' < qual.txt > qual_single_line.txt 이후

import os

def rle_encode(data):
    encoding = bytearray()
    count = 1
    prev = data[0]
    
    for char in data[1:]:
        if char == prev and count < 255:
            count += 1
        else:
            encoding.append((count - 1) | (0x80 if count > 1 else 0))
            encoding.append(prev)
            count = 1
            prev = char
    
    encoding.append((count - 1) | (0x80 if count > 1 else 0))
    encoding.append(prev)
    
    return bytes(encoding)

def rle_decode(data):
    decoding = bytearray()
    i = 0
    
    while i < len(data):
        count = (data[i] & 0x7F) + 1
        char = data[i+1]
        decoding.extend([char] * count)
        i += 2
    
    return bytes(decoding)

# def rle_encode_file(input_file, output_file, chunk_size=1024*1024*100):  # 1MB 청크
#     with open(input_file, 'rb') as infile, open(output_file, 'wb') as outfile:
#         prev_char = None
#         count = 0
        
#         while True:
#             chunk = infile.read(chunk_size)
#             if not chunk:
#                 if prev_char is not None:
#                     outfile.write(bytes([(count - 1) | (0x80 if count > 1 else 0), prev_char]))
#                 break
            
#             for char in chunk:
#                 if char == prev_char and count < 255:
#                     count += 1
#                 else:
#                     if prev_char is not None:
#                         outfile.write(bytes([(count - 1) | (0x80 if count > 1 else 0), prev_char]))
#                     count = 1
#                     prev_char = char

# def rle_decode_file(input_file, output_file, chunk_size=1024*1024*100):  # 1MB 청크
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

# 사용 예시
input_file = "/home/donggyu/cmc/FastqOurs/qual_comp/SRR30590406_qual_nolinebreak"
compressed_file = "/home/donggyu/cmc/data/SRR30590406_qual.rle1"
decompressed_file = "/home/donggyu/cmc/data/qualities_decompressed.txt"

# 압축
rle_encode_file(input_file, compressed_file)

# 압축 해제
#rle_decode_file(compressed_file, decompressed_file)

# 파일 크기 비교
original_size = os.path.getsize(input_file)
compressed_size = os.path.getsize(compressed_file)
#decompressed_size = os.path.getsize(decompressed_file)

print(f"Original file size: {original_size} bytes")
print(f"Compressed file size: {compressed_size} bytes")
#print(f"Decompressed file size: {decompressed_size} bytes")
#print(f"Compression ratio: {compressed_size / original_size:.2%}")