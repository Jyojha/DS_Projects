var cities = undefined;

var city_select = $("#city_select");
var neighborhood_select = $("#neighborhood_select");
var bedrooms_select = $("#bedrooms_select");
var bathrooms_select = $("#bathrooms_select");
var room_type_select = $("#room_type_select");

var map = L.map('mapid');
L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoiYWFydGFtb25hdSIsImEiOiJjaXl6b3RyYXIwNGt6MnhvNG5jY2d1a2NoIn0.fdOP_wTZjIHnmOuDPLgIww', {
    maxZoom: 18,
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, ' +
        '<a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, ' +
        'Imagery © <a href="http://mapbox.com">Mapbox</a>',
    id: 'mapbox.streets'
}).addTo(map);

$.ajax("/api/cities/",
       {
           async: false
       }
      ).done(function (data) {
          cities = data
      });

function populateSelect(select, options) {
    select.children().remove();

    for (var key in options) {
        var opt = document.createElement("option");
        var value = options[key];

        opt.value = value;
        opt.innerHTML = value;

        select.append(opt);
    }
}

function getValue(select) {
    return select.find(":selected").text()
}

function formatPrice(price) {
    return '$' + price.toFixed(2);
}

var predict_request = undefined;
function getPredictedValue() {
    if (predict_request != undefined) {
        predict_request.abort();
        predict_request = undefined;
    }

    var data = {
        city: getValue(city_select),
        bedrooms: getValue(bedrooms_select),
        bathrooms: getValue(bathrooms_select),
        room_type: getValue(room_type_select),
        neighborhood: getValue(neighborhood_select)
    };

    $('#price').text('predicting...');
    hideUnderpriced();
    predict_request = $.ajax("/api/predict/", {data: data}).done(
        function (response) {
            var price = response['price'];

            $('#price').text(formatPrice(price));
            getUnderpriced(price, data);
        });
}

function hideUnderpriced() {
    $("#underpriced-fetching").removeClass("hidden");
    $("#underpriced-table").addClass("hidden")
}

function showUnderpriced() {
    $("#underpriced-fetching").addClass("hidden");
    $("#underpriced-table").removeClass("hidden");
}

function getUnderpriced(price, data) {
    data['price'] = price;
    data['limit'] = 3;

    $.ajax("/api/cities/cheap/", {data: data}).done(
        function (response) {
            populateProperties(response.properties);
            showUnderpriced();
        });
}

var propertyMarker = undefined;
function onPropertyClick(price, latlong) {
    return function() {
        if (propertyMarker != undefined) {
            propertyMarker.remove();
        }

        propertyMarker = L.marker(latlong).addTo(map);
        propertyMarker.bindPopup(price, {closeButton: false}).openPopup();
    };
}

function populateProperties(props) {
    var tbody = $('#underpriced-table tbody');
    tbody.text('');

    if (props.length > 0) {
        for (var i in props) {
            var prop = props[i];
            var price = formatPrice(prop.price);
            var latlong = prop.latlong;

            var tr = $(document.createElement("tr"));
            var td_i = $(document.createElement("td"));
            var td_price = $(document.createElement("td"));
            var p = $(document.createElement("p"));

            td_i.text(Number(i) + 1);

            p.addClass("text-right").text(price);
            td_price.append(p);

            tr.append(td_i);
            tr.append(td_price);
            tr.addClass('property')

            tr.click(onPropertyClick(price, latlong));

            tbody.append(tr);
        }
    } else {
        var tr = $(document.createElement("tr"));
        var td = $(document.createElement("td"));
        var p = $(document.createElement("p"));

        p.addClass("text-center").text("No matching properties");
        td.append(p).attr('colspan', 2);
        tr.append(td);
        tbody.append(tr);
    }
}

var update_request = undefined;
var popup = undefined;
var polygon = undefined;
function updateMapView() {
    var city = getValue(city_select);
    var neighborhood = getValue(neighborhood_select);

    if (update_request != undefined) {
        update_request.abort();
        update_request = undefined
    }

    var data = {
        city: city,
        neighborhood: neighborhood
    };

    $.ajax('/api/cities/geo/', {data: data})
        .done(function (data) {
            if (popup != undefined) {
                popup.remove();
            }

            if (polygon != undefined) {
                polygon.remove();
            }

            var center = data['center'];
            if (center) {
                var options = {
                    closeButton: false
                };

                var popup = L.popup(options)
                    .setLatLng(center)
                    .setContent(neighborhood)
                    .openOn(map);

                var coordinates = data['coordinates'];
                if (coordinates) {
                    polygon = L.polygon(coordinates).addTo(map);
                    map.fitBounds(polygon.getBounds());
                } else {
                    map.setView(center, 13);
                }
            }
        });
}

if (cities != undefined) {
    city_select.change(function (e) {
        var city = cities[getValue(city_select)];
        populateSelect(neighborhood_select, city["neighborhoods"]);
        populateSelect(bedrooms_select, city["bedrooms"]);
        populateSelect(bathrooms_select, city["bathrooms"]);
        populateSelect(room_type_select, city["room_types"]);
    });

    populateSelect(city_select, Object.keys(cities))

    city_select.change(updateMapView);
    neighborhood_select.change(updateMapView);

    $("select").change(getPredictedValue);
    city_select.trigger("change");
}
