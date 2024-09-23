import os
import sys
from Bio import SeqIO

def delete_if_exists(filename):
    """파일이 존재하면 삭제합니다."""
    if os.path.exists(filename):
        os.remove(filename)

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

def rle_encode_file(input_file, output_file, chunk_size=1024*1024):  # 1MB 청크
    with open(input_file, 'rb') as infile, open(output_file, 'wb') as outfile:
        prev_char = None
        count = 0
        
        while True:
            chunk = infile.read(chunk_size)
            if not chunk:
                if prev_char is not None:
                    outfile.write(bytes([(count - 1) | (0x80 if count > 1 else 0), prev_char]))
                break
            
            for char in chunk:
                if char == prev_char and count < 255:
                    count += 1
                else:
                    if prev_char is not None:
                        outfile.write(bytes([(count - 1) | (0x80 if count > 1 else 0), prev_char]))
                    count = 1
                    prev_char = char

def compress_with_zpaq(input_files, output_file):
    zpaq_cmd = f"zpaq a {output_file}.zpaq " + " ".join(input_files) + " -m5"
    try:
        subprocess.run(zpaq_cmd, shell=True, check=True)
        print(f"압축된 파일 생성: {output_file}.zpaq")
    except subprocess.CalledProcessError as e:
        print(f"압축 중 오류 발생: {e}")


def process_records(file_path):

    # 파일 이름만 추출
    file_name = os.path.basename(file_path)

    # 기존 파일이 있으면 삭제
    delete_if_exists(f"{file_name}_id.txt")
    delete_if_exists(f"{file_name}_qual.txt")
    
    with open(file_path, "r") as handle, open(f"{file_name}_id.txt", "w") as desc_file, open(f"{file_name}_qual.txt", "w") as qual_file:
        for record in SeqIO.parse(handle, "fastq"):
            # 품질 점수를 ASCII 문자로 변환
            quality_scores = ''.join(chr(q + 33) for q in record.letter_annotations['phred_quality'])

            # 첫 번째 @ 문자 제거
            description = record.description.replace('@', '', 1)

            # 파일에 직접 쓰기
            desc_file.write(description + "\n")
            qual_file.write(quality_scores)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 split_id_qual.py <input_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    process_records(file_path)
    file_name = os.path.basename(file_path)
    print(f"파일이 저장되었습니다: {file_name}_id.txt,{file_name}_qual.txt")

    # ID 파일 압축
    compress_with_zpaq([f"{file_name}_id.txt"], f"{file_name}_id")

    # 품질 파일 RLE 인코딩 후 압축
    rle_encoded_file = f"{file_name}_qual_rle.txt"
    rle_encode_file(f"{file_name}_qual.txt", rle_encoded_file)
    compress_with_zpaq([rle_encoded_file], f"{file_name}_qual")

    print(f"ID, Quality Score가 압축되었습니다.: {file_name}_id.zpaq, {file_name}_qual.zpaq")
    
    os.remove(f"{file_name}_id.txt")
    os.remove(f"{file_name}_qual.txt")
    (f"{file_name}_qual_rle.txt")
