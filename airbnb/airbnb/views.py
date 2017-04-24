import json
from random import randint

from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render_to_response
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page

from airbnb.predictor import predict_price
from airbnb.data import CITIES, CITIES_GEO
from airbnb.data import cheap_properties, Property

@require_http_methods("GET")
def cities(request):
    return render_to_response('cities.html')

@require_http_methods("GET")
@cache_page(60 * 60)
def predict(request):
    params = request.GET

    try:
        city = params['city']
        neighborhood = params['neighborhood']
        bedrooms = float(params['bedrooms'])
        bathrooms = float(params['bathrooms'])
        room_type = params['room_type']
    except (KeyError, ValueError):
        return HttpResponseBadRequest()

    price = predict_price(city=city,
                          neighborhood=neighborhood,
                          bedrooms=bedrooms,
                          bathrooms=bathrooms,
                          room_type=room_type)

    return JsonResponse({"price": price})

@require_http_methods("GET")
def cities_data(request):
    return JsonResponse(CITIES,
                        json_dumps_params={'sort_keys': True})

@require_http_methods("GET")
def geo_data(request):
    params = request.GET

    try:
        city = params['city']
        neighborhood = params['neighborhood']
        response = CITIES_GEO[city][neighborhood]
    except KeyError:
        return HttpResponseBadRequest()

    return JsonResponse(response)

@require_http_methods("GET")
def cities_cheap(request):
    params = request.GET

    try:
        city = params['city']
        neighborhood = params['neighborhood']
        bedrooms = float(params['bedrooms'])
        bathrooms = float(params['bathrooms'])
        room_type = params.get('room_type', "Entire home/apt")
        price = float(params['price'])
        limit = int(params.get('limit', 3))
    except (KeyError, ValueError):
        return HttpResponseBadRequest()

    cheap = cheap_properties(price=price, limit=limit,
                             city=city, neighborhood=neighborhood,
                             bedrooms=bedrooms, bathrooms=bathrooms,
                             room_type=room_type)

    response = {"properties": [{"price": p.price,
                                "latlong": p.latlong} for p in cheap]}

    return JsonResponse(response)
