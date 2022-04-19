import argparse
from pathlib import Path
from PIL import Image
import time
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
import json

def embed_file_batch(file_list, output_file):
    start_time = time.perf_counter() 
    img_list = [Image.open(filepath).convert('RGB') for filepath in file_list]
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f'{len(img_list)} images loaded in {elapsed_time} s')

    start_time = time.perf_counter()    
    embeddings = model.encode(img_list, 
                              batch_size=32,
                              device=args.device,
                              show_progress_bar=False)
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f'{len(embeddings)} embeddings created in {elapsed_time} s')

    flickr_ids = [file.stem for file in file_list]
    with open(f'bhl_embeddings/{output_file}.json','w') as json_out:
        json.dump(flickr_ids, json_out)

    with open(f'bhl_embeddings/{output_file}.npy','wb') as np_file:
        np.save(np_file, embeddings)
    
    return

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--threads",
                    help="number of threads")
    ap.add_argument("-d", "--device",
                    default='cpu',
                    help="device used to encode")
    args = ap.parse_args()

    torch.set_num_threads(int(args.threads))

    start_time = time.perf_counter()
    model = SentenceTransformer('clip-ViT-B-32')
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f'Model loaded in {elapsed_time} s')

    start_time = time.perf_counter()
    all_names = list(Path('bhl_photos').rglob('*.jpg'))
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f'Took {elapsed_time} s to load {len(all_names)} into a list')

    FILE_BATCH_SIZE = 10000

    #all_names = all_names[:1000]
    #FILE_BATCH_SIZE = 100

    for start in range(0, len(all_names), FILE_BATCH_SIZE):
        file_subset = all_names[start:start+FILE_BATCH_SIZE]
        if len(file_subset) < FILE_BATCH_SIZE:
            file_end = start + len(file_subset)
        else:
            file_end = start + FILE_BATCH_SIZE
        print(start, file_end)
        file_out = f'embeddings_{start}_{file_end}'
        embed_file_batch(file_subset, file_out)
