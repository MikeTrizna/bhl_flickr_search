import streamlit as st
from annoy import AnnoyIndex
from sentence_transformers import SentenceTransformer
import json
from PIL import Image
import os
import urllib

st.set_page_config(
     page_title="BHL Flickr Image Search",
     page_icon="🖼️",
     layout="wide"
)

def download_file(file_path):
    # Don't download the file twice. (If possible, verify the download using the file length.)
    if os.path.exists(file_path):
        if "size" not in EXTERNAL_DEPENDENCIES[file_path]:
            return
        elif os.path.getsize(file_path) == EXTERNAL_DEPENDENCIES[file_path]["size"]:
            return

    # These are handles to two visual elements to animate.
    weights_warning, progress_bar = None, None
    try:
        weights_warning = st.warning("Downloading %s..." % file_path)
        progress_bar = st.progress(0)
        with open(file_path, "wb") as output_file:
            with urllib.request.urlopen(EXTERNAL_DEPENDENCIES[file_path]["url"]) as response:
                length = int(response.info()["Content-Length"])
                counter = 0.0
                MEGABYTES = 2.0 ** 20.0
                while True:
                    data = response.read(8192)
                    if not data:
                        break
                    counter += len(data)
                    output_file.write(data)

                    # We perform animation by overwriting the elements.
                    weights_warning.warning("Downloading %s... (%6.2f/%6.2f MB)" %
                        (file_path, counter / MEGABYTES, length / MEGABYTES))
                    progress_bar.progress(min(counter / length, 1.0))

    # Finally, we remove these visual elements by calling .empty().
    finally:
        if weights_warning is not None:
            weights_warning.empty()
        if progress_bar is not None:
            progress_bar.empty()
    
    return

@st.cache(allow_output_mutation=True)
def load_clip_model():
    return SentenceTransformer('clip-ViT-B-32')

@st.cache(allow_output_mutation=True)
def load_annoy_index():
    annoy_index = AnnoyIndex(512, metric='angular')
    annoy_index.load('bhl_index.annoy')
    return annoy_index

@st.cache(allow_output_mutation=True)
def load_flickr_data():
    with open('bhl_flickr_list.json') as json_in:
        bhl_flickr_ids = json.load(json_in)
    return bhl_flickr_ids

def bhl_id_search(query_id, k=5):
    for idx, row in enumerate(bhl_flickr_ids):
        if str(row['flickr_id']) == query_id:
            matching_row = idx
    neighbors = bhl_index.get_nns_by_item(matching_row, k,
                                          include_distances=True)
    return neighbors

def bhl_text_search(query_text, k=5):
    query_emb = model.encode([query_text], show_progress_bar=False)
    neighbors = bhl_index.get_nns_by_vector(query_emb[0], k,
                                            include_distances=True)
    return neighbors

def bhl_image_search(query_image, k=5):
    query_emb = model.encode([query_image], show_progress_bar=False)
    neighbors = bhl_index.get_nns_by_vector(query_emb[0], k,
                                            include_distances=True)
    return neighbors 

EXTERNAL_DEPENDENCIES = {
    "bhl_index.annoy": {
        "url": "https://www.dropbox.com/s/gf3e1icom0txu5g/bhl_index.annoy?dl=1",
        "size": 702894660
    }
}

DEPLOY_MODE = 'localhost'
if DEPLOY_MODE == 'localhost':
    BASE_URL = 'http://localhost:8501/'

if __name__ == "__main__":
    st.markdown("# BHL Flickr Image Search")
    st.markdown("Some sort of short blurb here")

    st.sidebar.markdown('### Search Mode')
    query_params = st.experimental_get_query_params()
    mode_index = 0
    if 'mode' in query_params:
        search_mode = query_params['mode'][0]
        if search_mode == 'flickr_id':
            mode_index = 1

    app_mode = st.sidebar.radio("How would you like to search?",
                        ['Text search', 'BHL Flickr ID', 'Upload Image'],
                        index = mode_index)

    for filename in EXTERNAL_DEPENDENCIES.keys():
        download_file(filename)
    model = load_clip_model()
    bhl_index = load_annoy_index()
    bhl_flickr_ids = load_flickr_data()

    if app_mode == 'Text search':
        text_query = st.text_input('Search query', 'a watercolor illustration of an insect with flowers')   
        closest_k_idx, closest_k_dist = bhl_text_search(text_query, 100)

    elif app_mode == 'BHL Flickr ID':
        search_id = '5974846748'
        if 'id' in query_params:
            search_id = query_params['id'][0]
        id_query = st.text_input('Query ID', search_id)

        closest_k_idx, closest_k_dist = bhl_id_search(id_query, 100)
    
    elif app_mode == 'Upload Image':
        image_file = st.file_uploader("Upload Image", type=["png","jpg","jpeg"])
        closest_k_idx = []
        if image_file is not None:
            img = Image.open(image_file)
            st.image(img,width=100)
            closest_k_idx, closest_k_dist = bhl_image_search(img, 100)

    col_list = st.columns(5)

    if len(closest_k_idx):
        for idx, annoy_idx in enumerate(closest_k_idx):
            bhl_ids = bhl_flickr_ids[annoy_idx]
            bhl_url = f"https://live.staticflickr.com/{bhl_ids['server']}/{bhl_ids['flickr_id']}_{bhl_ids['secret']}.jpg"
            #next(cols).image(bhl_url, use_column_width=True, caption=idx%5)
            col_list[idx%5].image(bhl_url, use_column_width=True)
            flickr_url = f"https://www.flickr.com/photos/biodivlibrary/{bhl_ids['flickr_id']}/"
            neighbors_url = f"{BASE_URL}?mode=flickr_id&id={bhl_ids['flickr_id']}"
            #col_list[idx%5].markdown(f'[Flickr Link]({flickr_url}) | [Neighbors]({neighbors_url})')
            link_html = f'<a href="{flickr_url}" target="_blank">Flickr Link</a> | <a href="{neighbors_url}">Neighbors</a>'
            col_list[idx%5].markdown(link_html, unsafe_allow_html=True)
            col_list[idx%5].markdown("---")


