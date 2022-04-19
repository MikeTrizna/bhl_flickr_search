import flickrapi
import json
from pathlib import Path
from tenacity import retry
from tenacity.stop import stop_after_attempt
from tenacity.wait import wait_fixed


@retry(stop=stop_after_attempt(7), wait=wait_fixed(2))
def download_photos_from_photoset(photoset_id):
    photo_list = []
    try:
        ps_photos_json = flickr.photosets.getPhotos(user_id=BHL_USER, photoset_id=photoset_id,
                                                per_page = 500,
                                            format='json')
        ps_photos = json.loads(ps_photos_json)
        ps_list = ps_photos['photoset']['photo']
        photo_list += ps_list
        result_pages = ps_photos['photoset']['pages']
        print(photoset_id, result_pages, ps_photos['photoset']['total'])
        if result_pages > 1:
            for page in range(2, result_pages + 1):
                print(page)
                ps_photos_json = flickr.photosets.getPhotos(user_id=BHL_USER, photoset_id=photoset_id,
                                                per_page = 500, page = page,
                                            format='json')
                ps_photos = json.loads(ps_photos_json)
                ps_list = ps_photos['photoset']['photo']
                photo_list += ps_list
        return photo_list
    except:
        print(f'Error downloading photoset {photoset_id}. Trying again...')
        raise Exception

with open('flickr_api_key.json') as api_json:
    flickr_keys = json.load(api_json)

flickr = flickrapi.FlickrAPI(flickr_keys['Key'], 
                             flickr_keys['Secret'])

BHL_USER = '61021753@N02'

with open('bhl_photoset_info.json') as album_json: 
    albums = json.load(album_json)

already_downloaded = [json_file.stem for json_file in Path('photo_info').rglob('*.json')]

albums_to_dl = [album for album in albums if album['id'] not in already_downloaded]
print(f'Downloading {len(albums_to_dl)} remaining photosets')

for album in albums_to_dl:
    photoset_id = album['id']
    photo_list = download_photos_from_photoset(photoset_id)
    out_file = f"photo_info/{album['id']}.json"
    with open(out_file, 'w') as ps_json:
        json.dump(photo_list, ps_json)