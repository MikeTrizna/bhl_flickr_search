import flickrapi
import json

with open('flickr_api_key.json') as api_json:
    flickr_keys = json.load(api_json)

flickr = flickrapi.FlickrAPI(flickr_keys['Key'], 
                             flickr_keys['Secret'])

bhl = flickr.people.findByUsername(username = "biodivlibrary", format='parsed-json')
bhl_id = bhl['user']['id']

ps_list = []
initial_ps_search = flickr.photosets.getList(user_id=bhl_id, format='parsed-json')

bhl_ps_pages = initial_ps_search['photosets']['pages']

for page in range(1, bhl_ps_pages + 1):
    print(f'Fetching Page {page}')
    ps_results = flickr.photosets.getList(user_id=bhl_id, page=page,
                                          format='parsed-json')
    ps_info = ps_results['photosets']['photoset']
    ps_list += ps_info

with open('bhl_photoset_info.json', 'w') as ps_json:
    json.dump(ps_list, ps_json)



