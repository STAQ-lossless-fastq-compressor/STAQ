import collections
import gzip
import os
import time
import utils
import struct
from absl import app
from absl import flags
from absl import logging
import shutil

import numpy as np
import torch
import torch.nn.functional as F

import compress_model
import arithmeticcoding_fast
import utils

torch.manual_seed(0)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
torch.set_printoptions(profile="full") 
FLAGS = flags.FLAGS

# Model parameters
flags.DEFINE_integer('batch_size', 512, 'Batch size for training.')
flags.DEFINE_float('learning_rate', 1e-3, 'Adam Optimizer learning rate.')
flags.DEFINE_integer('hidden_dim', 256, 'Feature dimension.')
flags.DEFINE_integer('vocab_dim', 64, 'Feature dimension.')
flags.DEFINE_integer('n_layers', 1, 'Number of Attention layers.')
flags.DEFINE_integer('ffn_dim', 4096, 'MLP dimension in model.')
flags.DEFINE_integer('n_heads', 8, 'Number of heads for attention.')
flags.DEFINE_string(
    'feature_type', 'sqr',
    'Nonlinearity function for feature. Can be relu, elu+1, sqr, favor+, or favor+{int}.'
)
flags.DEFINE_enum(
    'compute_type', 'iter', ['iter', 'ps', 'parallel_ps'],
    'Which type of method to compute: iter = iterative algorithm, ps = implementation using torch.cumsum, parallel_ps = implementation using custom log prefix sum implementation.'
)
flags.DEFINE_float('weight_decay', 0.0, 'Weight decay for regularization.')

# Training parameters
flags.DEFINE_string('gpu_id', '0', 'ID of GPU.')
flags.DEFINE_integer('random_seed', 0, 'Random seed for both Numpy and Torch.')
flags.DEFINE_integer('print_step', 1000, 'Interval to print metrics.')
# Dataset parameters
flags.DEFINE_integer('seq_len', 8, 'Maximum sequence length (L).')
flags.DEFINE_integer('vocab_size', 256, 'Vocabulary size of data.')
flags.DEFINE_string('input_dir', 'aaa', 'input data dir')
flags.DEFINE_string('prefix', 'text8', 'output dir')


def decode(temp_dir, directory, compressed_file, FLAGS, len_series, last):
  
  bs = FLAGS.batch_size

  iter_num = (len_series - FLAGS.seq_len) // FLAGS.batch_size
  
  ind = np.array(range(bs))*iter_num
  print(iter_num - FLAGS.seq_len)
  series_2d = np.zeros((bs,iter_num), dtype = np.uint8).astype('int')

  f = [open(temp_dir+"/"+compressed_file+'.'+str(i),'rb') for i in range(bs)]
  bitin = [arithmeticcoding_fast.BitInputStream(f[i]) for i in range(bs)]
  dec = [arithmeticcoding_fast.ArithmeticDecoder(32, bitin[i]) for i in range(bs)]

  prob = np.ones(FLAGS.vocab_size)/FLAGS.vocab_size
  cumul = np.zeros(FLAGS.vocab_size+1, dtype = np.uint64)
  cumul[1:] = np.cumsum(prob*10000000 + 1)

  # Decode first K symbols in each stream with uniform probabilities
  for i in range(bs):
    for j in range(min(FLAGS.seq_len, iter_num)):
      series_2d[i,j] = dec[i].read(cumul, FLAGS.vocab_size)
  
  cumul_batch = np.zeros((bs, FLAGS.vocab_size+1), dtype = np.uint64)

  os.environ['CUDA_VISIBLE_DEVICES'] = FLAGS.gpu_id
  np.random.seed(FLAGS.random_seed)
  torch.manual_seed(FLAGS.random_seed)

  model = compress_model.SLiMPerformer(FLAGS.vocab_size, FLAGS.vocab_dim, FLAGS.hidden_dim,FLAGS.n_layers, FLAGS.ffn_dim,FLAGS.n_heads, FLAGS.feature_type, FLAGS.compute_type).cuda()
  print(model)

  optimizer = torch.optim.Adam(model.parameters(), lr=FLAGS.learning_rate, weight_decay=FLAGS.weight_decay, betas=(.9, .999))

  training_start = time.time()
  for train_index in range(iter_num-FLAGS.seq_len):
    model.train()
    train_batch = torch.LongTensor(series_2d[:, train_index:train_index + FLAGS.seq_len]).cuda()
    logits = model.forward(train_batch)
    prob = logits[:, -1, :]
    prob = F.softmax(prob, dim=1).detach().cpu().numpy()
    
    cumul_batch[:,1:] = np.cumsum(prob*10000000 + 1, axis = 1)

    # Decode with Arithmetic Encoder
    for i in range(bs):
      series_2d[i,train_index+FLAGS.seq_len] = dec[i].read(cumul_batch[i,:], FLAGS.vocab_size)
    
    logits = logits.transpose(1, 2)
    label = torch.from_numpy(series_2d[:, train_index+1:train_index+FLAGS.seq_len+1]).cuda()
    train_loss = torch.nn.functional.cross_entropy(logits[:, :, -1], label[:, -1], reduction='mean')
    train_loss.backward()
    optimizer.step()
    optimizer.zero_grad(set_to_none=True)
    
    if train_index % FLAGS.print_step == 0:
      print(train_index, ":", train_loss.item()/np.log(2))
  
  file_name = compressed_file
  base_name = file_name.rsplit('.', 3)[0]
  # out = open(os.path.join(directory, base_name), 'w')
  out = open(os.path.join(directory, base_name), 'wb')
  for i in range(len(series_2d)):
    # out.write(utils.decode_tokens(series_2d[i]))
    out.write(series_2d[i].astype(np.uint8).tobytes())
  
  for i in range(bs):
    bitin[i].close()
    f[i].close()

  if last:
    series = np.zeros(last, dtype = np.uint8).astype('int')
    f = open(temp_dir+"/"+compressed_file+'.last','rb')
    bitin = arithmeticcoding_fast.BitInputStream(f)
    dec = arithmeticcoding_fast.ArithmeticDecoder(32, bitin)
    prob = np.ones(FLAGS.vocab_size)/FLAGS.vocab_size
    cumul = np.zeros(FLAGS.vocab_size+1, dtype=np.uint64)
    cumul[1:] = np.cumsum(prob*10000000 + 1)

    for j in range(last):
      series[j] = dec.read(cumul, FLAGS.vocab_size)
  
    print("Last decode part don't need inference.")
    # out.write(utils.decode_tokens(series))
    # print(utils.decode_tokens(series))
    out.write(series.astype(np.uint8).tobytes())
    # print(utils.decode_tokens(series))
    bitin.close()
    f.close()
    return

def var_int_decode(f):
    byte_str_len = 0
    shift = 1
    while True:
        this_byte = struct.unpack('B', f.read(1))[0]
        byte_str_len += (this_byte & 127) * shift
        if this_byte & 128 == 0:
                break
        shift <<= 7
        byte_str_len += shift
    return byte_str_len

def read_metadata(metadata_file):
    metadata = {}
    with open(metadata_file, 'r') as f:
        for line in f:
            # 줄을 읽고 양쪽의 공백을 제거한 뒤, '='로 나눔
            key, value = line.strip().split('=')
            metadata[key] = int(value)  # 값은 숫자로 변환 (필요 시 float이나 다른 타입으로 변환 가능)
    return metadata


def main(_):

  os.environ['CUDA_VISIBLE_DEVICES'] = FLAGS.gpu_id
  np.random.seed(FLAGS.random_seed)
  torch.manual_seed(FLAGS.random_seed)

  # file_name = os.path.basename(FLAGS.input_dir)
  # temp_dir = "{}_temp".format(file_name)

  input_dir = FLAGS.input_dir
  file_name = os.path.basename(input_dir)
  # input_dir에서 디렉터리 경로 추출
  directory = os.path.dirname(input_dir)
  temp_dir = os.path.join(directory, f"{file_name}_temp")
  metadata_file = file_name+"_metadata.txt"
  metadata = read_metadata(metadata_file)
  print(f"Metadata: {metadata}")

  # print(f"Input directory: {FLAGS.input_dir}")
  # print(f"File name: {file_name}")
  # print(f"Temporary directory: {temp_dir}")
  def strided_app(a, L, S):  # Window len = L, Stride len/stepsize = S
    nrows = ((a.size - L) // S) + 1
    n = a.strides[0]
    return np.lib.stride_tricks.as_strided(a, shape=(nrows, L), strides=(S * n, n))
  
  old_seq_len = FLAGS.seq_len
  FLAGS.seq_len = FLAGS.seq_len*(FLAGS.hidden_dim // FLAGS.vocab_dim)
  print("FLAGS.seq_len change from {} to {} due to FLAGS.vocab_dim = {} and FLAGS.hidden_dim = {}.".format(old_seq_len, FLAGS.seq_len, FLAGS.vocab_dim, FLAGS.hidden_dim))
  
  # with open(FLAGS.input_dir, 'rb') as fp:#, encoding='latin-1') as fp:
  #   series = np.fromstring(fp.read(), dtype=np.uint8)
  # train_data = strided_app(series, FLAGS.seq_len+1, 1)

  
  #Decode
  os.mkdir(temp_dir)
  
  #Split compressed file
  
  f = open(directory+'/'+file_name,'rb')
  # len_series = len(series)
  for i in range(FLAGS.batch_size):
    f_out = open(temp_dir+'/'+file_name+'.'+str(i),'wb')
    byte_str_len = var_int_decode(f)
    byte_str = f.read(byte_str_len)
    f_out.write(byte_str)
    f_out.close()
  
  f_out = open(temp_dir+'/'+file_name+'.last','wb')
  byte_str_len = var_int_decode(f)
  byte_str = f.read(byte_str_len)
  f_out.write(byte_str)
  f_out.close()
  f.close()
  
  len_series = metadata.get('len_series') 
  if (len_series-FLAGS.seq_len) % FLAGS.batch_size == 0:
    decode(temp_dir, directory, file_name, FLAGS, len_series, 0)
  else:
    last_length = (len_series - FLAGS.seq_len) % FLAGS.batch_size + FLAGS.seq_len
    decode(temp_dir, directory, file_name, FLAGS, len_series, last_length)
  
  # #Remove temp file
  shutil.rmtree(temp_dir)

if __name__ == '__main__':
  app.run(main)
