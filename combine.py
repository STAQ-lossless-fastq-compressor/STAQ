import sys

def combine_to_fastq(id_file, seq_file, qual_file, output_fastq, default_qual="I"):
    with open(id_file, 'r') as id_f, open(seq_file, 'r') as seq_f, open(qual_file, 'r') as qual_f, open(output_fastq, 'w') as out_f:
        seq_lines = seq_f.readlines()
        id_lines = id_f.readlines()
        qual_data = qual_f.read()  # 줄바꿈이 없는 qual 파일 전체를 읽음

        qual_index = 0  # qual 데이터를 읽어 나갈 인덱스

        # 시퀀스 파일에서 '@' 기호를 제외하고 시퀀스만 추출
        seq_lines = [line.strip() for line in seq_lines if not line.startswith('@') and line.strip()]

        for id_line, seq_line in zip(id_lines, seq_lines):
            id_line = id_line.strip()
            seq_line = seq_line.strip()

            # 시퀀스 길이만큼 quality 데이터에서 자르기
            qual_line = qual_data[qual_index:qual_index + len(seq_line)]
            qual_index += len(seq_line)  # 다음 시퀀스에 맞춰 인덱스를 증가

            # FASTQ 형식으로 출력
            out_f.write(f"@{id_line}\n")
            out_f.write(f"{seq_line}\n")
            out_f.write("+\n")
            out_f.write(f"{qual_line}\n")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python combine_fastq.py <id_file> <seq_file> <qual_file> <output_fastq>")
        sys.exit(1)

    id_file = sys.argv[1]
    seq_file = sys.argv[2]
    qual_file = sys.argv[3]
    output_fastq = sys.argv[4]

    combine_to_fastq(id_file, seq_file, qual_file, output_fastq)
