# STAQ
**STAQ is a lossless FASTQ compressor with high compression ratio**

This project is based on SPRING.
The SPRING software, sed by Donggyu Hwang, was developed at the University of Illinois at Urbana-Champaign and Stanford University.
The original SPRING license and software can be found here: [SPRING GitHub Repository](https://github.com/shubhamchandak94/Spring).

## Download STAQ
```
git clone https://github.com/labhai-dev/STAQ.git
```

## Install STAQ
```
./install.sh
```

## Usage of STAQ

Compress FASTQ
```
./staq.sh -c -i input_1.fastq [input_2.fastq] [--deep] [--gpu-id gpu_id (Using Deep)] [-l] -o output.staq
```

Decompress FASTQ
```
./staq.sh -d -i input_1.staq [--deep] [--gpu-id gpu_id (Using Deep)] [-l] -o output_1.fastq [output_2.fastq]
```

## Example

### Compress 
If you want to compress a FASTQ file lossless (default)

```
./staq.sh -c -i input.fastq -o output.staq
```

If you want to compress a FASTQ file lossless (using deep)
```
./staq.sh -c -i input.fastq deep [--gpu-id gpu-id] -o output.staq
```

If you want to compress paired-end FASTQ files lossless (default)

```
./staq.sh -c -i input_1.fastq input_2.fastq -o output.staq
```

If you want to compress paired-end FASTQ files lossless (using deep)
```
./staq.sh -c -i input.fastq input_2.fastq deep [--gpu-id gpu-id] -o output.staq
```

### Decompress

If you want to decompress a FASTQ file lossless (default)

```
./staq.sh -d -i input.staq -o output.fastq
```

If you want to decompress a FASTQ file lossless (using deep)
```
./staq.sh -d -i input.staq deep [--gpu-id gpu-id] -o output.fastq
```

If you want to decompress paired-end FASTQ files lossless (default)

```
./staq.sh -d -i input.staq -o output_1.fastq output_2.fastq
```

If you want to decompress paired-end FASTQ files lossless (using deep)
```
./staq.sh -d -i input.staq deep [--gpu-id gpu-id] -o output_1.fastq output_2.fastq
```