import sys

def combine_to_fastq(seq_file, qual_file, output_fastq):
    with open(seq_file, 'r') as seq_f, open(qual_file, 'r') as qual_f, open(output_fastq, 'w') as out_f:
        qual_data = qual_f.read()  # 줄바꿈이 없는 qual 파일 전체를 읽음
        qual_index = 0  # qual 데이터를 읽어 나갈 인덱스

        while True:
            # ID 라인 읽기
            id_line = seq_f.readline().strip()
            if not id_line:  # 파일의 끝에 도달했다면 종료
                break
            
            # 시퀀스 라인 읽기
            seq_line = seq_f.readline().strip()

            # 시퀀스 길이만큼 quality 데이터에서 자르기
            qual_line = qual_data[qual_index:qual_index + len(seq_line)]
            qual_index += len(seq_line)  # 다음 시퀀스에 맞춰 인덱스를 증가

            # FASTQ 형식으로 출력
            out_f.write(f"{id_line}\n")
            out_f.write(f"{seq_line}\n")
            out_f.write("+\n")
            out_f.write(f"{qual_line}\n")

def combine_to_pe_fastq(seq_file1, qual_file1, output_fastq1, seq_file2, output_fastq2):
    with open(seq_file1, 'r') as seq_f, open(seq_file2, 'r') as seq_f2, open(qual_file1, 'r') as qual_f, open(output_fastq1, 'w') as out_f, open(output_fastq2, 'w') as out_f2:
        qual_data = qual_f.read()  # 줄바꿈이 없는 qual 파일 전체를 읽음
        qual_index = 0  # qual 데이터를 읽어 나갈 인덱스

        while True:
            # ID 라인 읽기
            id_line = seq_f.readline().strip()
            if not id_line:  # 파일의 끝에 도달했다면 종료
                break
            
            # 시퀀스 라인 읽기
            seq_line = seq_f.readline().strip()

            # 시퀀스 길이만큼 quality 데이터에서 자르기
            qual_line = qual_data[qual_index:qual_index + len(seq_line)]
            qual_index += len(seq_line)  # 다음 시퀀스에 맞춰 인덱스를 증가

            # FASTQ 형식으로 출력
            out_f.write(f"{id_line}\n")
            out_f.write(f"{seq_line}\n")
            out_f.write("+\n")
            out_f.write(f"{qual_line}\n")

        while True:
            # ID 라인 읽기
            id_line = seq_f2.readline().strip()
            if not id_line:  # 파일의 끝에 도달했다면 종료
                break
            
            # 시퀀스 라인 읽기
            seq_line = seq_f2.readline().strip()

            # 시퀀스 길이만큼 quality 데이터에서 자르기
            qual_line = qual_data[qual_index:qual_index + len(seq_line)]
            qual_index += len(seq_line)  # 다음 시퀀스에 맞춰 인덱스를 증가

            # FASTQ 형식으로 출력
            out_f2.write(f"{id_line}\n")
            out_f2.write(f"{seq_line}\n")
            out_f2.write("+\n")
            out_f2.write(f"{qual_line}\n")
        


if __name__ == "__main__":
    if len(sys.argv) not in [4, 6]:
        print("Usage: python combine_fastq.py <seq_file1> <qual_file1> <output_fastq1> [<seq_file2> <output_fastq2>]")
        sys.exit(1)

    if len(sys.argv) == 6:
        seq_file1 = sys.argv[1]
        qual_file1 = sys.argv[2]
        output_fastq1 = sys.argv[3]
        seq_file2 = sys.argv[4]
        output_fastq2 = sys.argv[5]
        combine_to_pe_fastq(seq_file1, qual_file1, output_fastq1, seq_file2, output_fastq2)
    else:
        seq_file1 = sys.argv[1]
        qual_file1 = sys.argv[2]
        output_fastq1 = sys.argv[3]
        combine_to_fastq(seq_file1, qual_file1, output_fastq1)

    print("FASTQ 파일 생성 완료")