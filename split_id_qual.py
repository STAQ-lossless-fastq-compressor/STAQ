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

def rle_encode(data):
    """Encodes data using Run-Length Encoding (RLE)."""
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

def compress_with_zpaq(input_files, output_file):
    """Compresses input files using ZPAQ."""
    zpaq_cmd = f"zpaq a {output_file}.zpaq " + " ".join(input_files) + " -m5"
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
    delete_if_exists(f"{output_prefix}_id.txt")
    delete_if_exists(f"{output_prefix}_qual.txt")
    
    with open(file_path, "r") as handle, open(f"{output_prefix}_id.txt", "w") as desc_file, open(f"{output_prefix}_qual.txt", "w") as qual_file:
        for record in SeqIO.parse(handle, "fastq"):
            # Convert quality scores to ASCII characters
            quality_scores = ''.join(chr(q + 33) for q in record.letter_annotations['phred_quality'])

            # Remove the first '@' character from the description
            description = record.description.replace('@', '', 1)

            # Write directly to files
            desc_file.write(description + "\n")
            qual_file.write(quality_scores)

def are_files_identical(file1, file2):
    """Compares if the contents of two files are identical."""
    return filecmp.cmp(file1, file2, shallow=False)

def process_file(file_path, output_prefix, previous_id_file=None):
    """Processes a single input file and handles compression of ID and quality files."""
    process_records(file_path, output_prefix)
    print(f"Files saved: {output_prefix}_id.txt, {output_prefix}_qual.txt")

    with ThreadPoolExecutor() as executor:
        if previous_id_file and are_files_identical(f"{output_prefix}_id.txt", previous_id_file):
            print(f"{output_prefix} ID file is identical to the previous file. Skipping compression.")
            os.remove(f"{output_prefix}_id.txt")
            id_future = None
        else:
            id_future = executor.submit(compress_with_zpaq, [f"{output_prefix}_id.txt"], f"{output_prefix}_id")
        
        rle_encoded_file = f"{output_prefix}_qual_rle"
        rle_future = executor.submit(rle_encode_file, f"{output_prefix}_qual.txt", rle_encoded_file)

        # Wait for all tasks to complete
        for future in as_completed([f for f in [id_future, rle_future] if f]):
            if future is id_future:
                print(f"{output_prefix} ID file compression completed.")
            elif future is rle_future:
                print(f"{output_prefix} Quality file RLE encoding completed.")

    # Compress the RLE encoded quality file
    compress_with_zpaq([rle_encoded_file], f"{output_prefix}_qual")

    if id_future:
        print(f"ID and Quality Score have been compressed: {output_prefix}_id.zpaq, {output_prefix}_qual.zpaq")
    else:
        print(f"Quality Score has been compressed: {output_prefix}_qual.zpaq")

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python3 split_id_qual.py <input_file1> [input_file2]")
        sys.exit(1)
    
    file_path1 = sys.argv[1]
    output_prefix1 = os.path.basename(file_path1)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        future1 = executor.submit(process_file, file_path1, output_prefix1)

        if len(sys.argv) == 3:
            file_path2 = sys.argv[2]
            output_prefix2 = os.path.basename(file_path2)
            future2 = executor.submit(process_file, file_path2, output_prefix2)

        # Wait for the first file to complete
        future1.result()

        if len(sys.argv) == 3:
            # If there's a second file, wait for it to complete
            future2.result()

            # Now compare the ID files
            if are_files_identical(f"{output_prefix1}_id.txt", f"{output_prefix2}_id.txt"):
                print("ID files are identical. Removing the second ID file.")
                os.remove(f"{output_prefix2}_id.txt")
                os.remove(f"{output_prefix2}_id.zpaq")
            else:
                print("ID files are different. Keeping both.")

    # os.remove(f"{output_prefix1}_qual.txt")
    # os.remove(f"{output_prefix1}_qual_rle")
    # if os.path.exists(f"{output_prefix2}_id.txt"):
    #     os.remove(f"{output_prefix2}_id.txt")
    # os.remove(f"{output_prefix2}_qual_rle")
    # os.remove(f"{output_prefix1}_qual.txt")
    for i in range(1,3):
        name = 'output_prefix' + str(i)
        if os.path.exists(f"{name}_id.txt"):
            os.remove(f"{name}_id.txt")
        if os.path.exists(f"{name}_qual.txt"):
            os.remove(f"{name}_qual.txt")
        if os.path.exists(f"{name}qual_rle"):
            os.remove(f"{name}_qual_rle")

    print("All operations completed.")