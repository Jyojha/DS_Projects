import json
import os.path
from glob import glob
from collections import namedtuple
from django.conf import settings
import pandas as pd

MODELS_DIR = settings.MODELS_DIR
GEO_DIR = settings.GEO_DIR
CITIES = {}
CITIES_GEO = {}
PROPERTIES = {}

Query = namedtuple('Query', ['city', 'neighborhood',
                             'bedrooms', 'bathrooms', 'room_type'])
Property = namedtuple('Property', ['latlong', 'price'])

for dataset_path in glob(os.path.join(MODELS_DIR, "*.csv")):
    city, _ = os.path.splitext(os.path.basename(dataset_path))
    dataset = pd.read_csv(dataset_path)

    with open(os.path.join(GEO_DIR, '%s.json' % city)) as f:
        geo = json.load(f)

    CITIES_GEO[city] = geo
    city_data = {
        'bathrooms': sorted(set(dataset['bathrooms'])),
        'bedrooms': sorted(set(dataset['bedrooms'])),
        'neighborhoods': sorted(set(dataset['neighborhood'])),
        'room_types': sorted(set(dataset['room_type']) - {'Shared room'}),
    }
    CITIES[city] = city_data

    fields = ['neighborhood', 'bedrooms', 'bathrooms',
              'room_type', 'latitude', 'longitude', 'price']
    for item in dataset[fields].itertuples():
        query = Query(city=city,
                      neighborhood=item.neighborhood,
                      bedrooms=item.bedrooms,
                      bathrooms=item.bathrooms,
                      room_type=item.room_type)
        prop = Property(latlong=(item.latitude, item.longitude),
                        price=item.price)

        props = PROPERTIES.setdefault(query, [])
        props.append(prop)

for query in PROPERTIES:
    PROPERTIES[query].sort(key=lambda x: x.price)

def cheap_properties(price, limit, **kwargs):
    query = Query(**kwargs)
    props = PROPERTIES.get(query, [])
    cheap = []

    for prop in props[:limit]:
        if prop.price > price:
            break

        cheap.append(prop)

    return cheap
