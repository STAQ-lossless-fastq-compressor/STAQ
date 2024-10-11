import mmap
import array
import os

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

def compare_files(file1, file2, chunk_size=1024*1024):
    with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
        position = 0
        while True:
            chunk1 = f1.read(chunk_size)
            chunk2 = f2.read(chunk_size)
            if chunk1 != chunk2:
                for i, (b1, b2) in enumerate(zip(chunk1, chunk2)):
                    if b1 != b2:
                        print(f"Difference at position {position + i}: {b1} ({chr(b1)}) != {b2} ({chr(b2)})")
                        print(f"Context: {chunk1[max(0, i-10):i+10]} != {chunk2[max(0, i-10):i+10]}")
                        return False
                if len(chunk1) != len(chunk2):
                    print(f"File lengths differ at position {position + min(len(chunk1), len(chunk2))}")
                    return False
            if not chunk1:
                return True
            position += len(chunk1)

if __name__ == "__main__":
    original_file = "/home/donggyu/cmc/STAQ/SRR30480369_1.fastq_qual.txt"
    encoded_file = 'fastq_qual_rle'
    decoded_file = 'qual_decoded.txt'

    print(f"Original file size: {os.path.getsize(original_file) / (1024*1024*1024):.2f} GB")
    
    rle_encode_file(original_file, encoded_file)
    print(f"Encoded file size: {os.path.getsize(encoded_file) / (1024*1024*1024):.2f} GB")
    
    rle_decode_file_optimized(encoded_file, decoded_file)
    print(f"Decoded file size: {os.path.getsize(decoded_file) / (1024*1024*1024):.2f} GB")
    
    if compare_files(original_file, decoded_file):
        print("Files are identical")
    else:
        print("Files are different")