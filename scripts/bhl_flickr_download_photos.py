import requests
from PIL import Image
import io
import time
import pandas as pd
import numpy as np
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_fixed
import argparse


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def requests_PIL_download(photo_info):
    width, height = np.nan, np.nan
    filename = Path('bhl_photos') / f"{photo_info['id']}.jpg"
    med_url = f"https://live.staticflickr.com/{photo_info['server']}/{photo_info['id']}_{photo_info['secret']}.jpg"

    try:
        r = requests.get(med_url, timeout=60)
        if r.headers['Content-Type'] == 'image/jpeg':
            with Image.open(io.BytesIO(r.content)) as im:
                width, height = im.size
                im.save(filename)
    except:
        print(f"Error downloading photo {photo_info['id']}. Trying again...")
        raise Exception
    return {'width': width, 'height': height, 'ids_id': photo_info['id']}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--processes",
                    help="number of processes")
    args = ap.parse_args()

    photos_df = pd.read_csv('bhl_photo_ids.tsv', sep='\t')
    photos_df = photos_df.drop_duplicates(subset='id')
    photo_list = photos_df.to_dict(orient='records')
    #photo_list = photos_df.sample(1000).to_dict(orient='records')

    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=int(args.processes)) as executor:
        dim_list = list(executor.map(requests_PIL_download, photo_list))

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Downloaded {len(dim_list)} images in {elapsed_time} s")

    dim_df = pd.DataFrame(dim_list)
    dim_df.to_csv('bhl_photo_med_dimensions.tsv', index=False, sep='\t')

