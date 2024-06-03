# ---    Dependencies    ---#


import requests
import warnings  # Ignore warnings for pyproj.

warnings.simplefilter("ignore", category=FutureWarning)

from pyproj import Proj, transform


# ---    Functions    ---#


def crsToSrs(min_lat, min_lon, max_lat, max_lon):
    """
    ## Converts coordinates from EPSG:4326 to EPSG25832.

    ## Parameters:
        - x1, y1, x2, y2 coordinates of EPSG:4326 WGS 84 system.

    ## Returns:
       - minimum x coordinate, minimum y coordinate, maximum x coordinate, maximum y coordinate

    """
    min_x, min_y = transform(Proj("EPSG:4326"), Proj("EPSG:25832"), min_lat, min_lon)
    max_x, max_y = transform(Proj("EPSG:4326"), Proj("EPSG:25832"), max_lat, max_lon)
    return min_x, min_y, max_x, max_y


def getAMDetailed(min_lat, min_lon, max_lat, max_lon, width, height, path):
    """
    ## Downloads detailed administrative map from Dataforsyningen to specified path as AM_Detailed.png.
        Uses implemented token in function.
        Prints returned errors from call.

    ## Parameters:
       - min_lat: minimum latitude (EPSG:4326)
       - min_lon: minimum longitude (EPSG:4326)
       - max_lat: maximum latitude  (EPSG:4326)
       - max_lon: maximum longitude (EPSG:4326)
       - width: width resolution of image.
       - height: height resolution of image.
       - path: Path to save image.

    """

    # API Address
    APIUrl = "https://api.dataforsyningen.dk/forvaltning2"

    # Token:
    token = "Deleted"

    min_x, min_y, max_x, max_y = crsToSrs(min_lat, min_lon, max_lat, max_lon)

    # Concatenating into a comma seperated string.
    coordinateString = ",".join([str(min_x), str(min_y), str(max_x), str(max_y)])

    # Request parameters
    params = {
        "service": "WMS",
        "request": "GetMap",
        "token": token,
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "FORMAT": "image/png",
        "STYLES": "",
        "TRANSPARENT": "true",
        "layers": "Basis_kort",
        "transparent": "FALSE",
        "tiled": "true",
        "WIDTH": f"{width}",
        "HEIGHT": f"{height}",
        "CRS": "EPSG:25832",
        "BBOX": coordinateString,
    }

    # Requesting images from API and saving
    response = requests.get(APIUrl, params=params)
    if response.status_code == 200:
        with open(path + "/AM_Detailed.png", "wb") as e:
            e.write(response.content)
    else:
        path = (
            APIUrl + "?" + "&".join([f"{key}={value}" for key, value in params.items()])
        )
        print("Failed to fetch map. Status code:", response.status_code)
        print("On path:", path)


def getAMWithRoads(min_lat, min_lon, max_lat, max_lon, width, height, path):
    """
    ## Downloads administrative map with roads from Dataforsyningen to specified path as AM_with_roads.png.
        Uses implemented token in function.
        Prints returned errors from call.

    ## Parameters:
       - min_lat: minimum latitude (EPSG:4326)
       - min_lon: minimum longitude (EPSG:4326)
       - max_lat: maximum latitude  (EPSG:4326)
       - max_lon: maximum longitude (EPSG:4326)
       - width: width resolution of image.
       - height: height resolution of image.
       - path: Path to save image.

    """

    # API Address
    APIUrl = "https://api.dataforsyningen.dk/forvaltning2"

    # Token:
    token = "Deleted"

    min_x, min_y, max_x, max_y = crsToSrs(min_lat, min_lon, max_lat, max_lon)

    # Concatenating into a comma seperated string.
    coordinateString = ",".join([str(min_x), str(min_y), str(max_x), str(max_y)])

    # Request parameters
    params = {
        "service": "WMS",
        "request": "GetMap",
        "token": token,
        "SERVICE": "WMS",
        "VERSION": "1.3.0",
        "FORMAT": "image/png",
        "STYLES": "",
        "TRANSPARENT": "true",
        "layers": "Adresse-byggesag",
        "transparent": "FALSE",
        "tiled": "true",
        "WIDTH": f"{width}",
        "HEIGHT": f"{height}",
        "CRS": "EPSG:25832",
        "BBOX": coordinateString,
    }

    response = requests.get(APIUrl, params=params)
    if response.status_code == 200:
        with open(path + "/AM_with_roads.png", "wb") as e:
            e.write(response.content)
    else:
        print("Failed to fetch roads. Status code:", response.status_code)


def getRoutes(min_lat, min_lon, max_lat, max_lon, width, height, path):
    """
    ## Downloads route map containing roads and walking paths from The Danish Road Directorate to specified path as routes.png.
        Prints returned errors from call.

    ## Parameters:
       - min_lat: minimum latitude (EPSG:4326)
       - min_lon: minimum longitude (EPSG:4326)
       - max_lat: maximum latitude  (EPSG:4326)
       - max_lon: maximum longitude (EPSG:4326)
       - width: width resolution of image.
       - height: height resolution of image.
       - path: Path to save image.

    """

    # API Address
    APIUrl = "https://geocloud.vd.dk/CVF/wms"

    # Converting from EPSG:4326 to EPSG25832
    min_x, min_y, man_x, max_y = crsToSrs(min_lat, min_lon, max_lat, max_lon)

    # Concatenating into a comma seperated string.
    coordinateString = ",".join([str(min_x), str(min_y), str(man_x), str(max_y)])

    # Request parameters
    params = {
        "service": "WMS",
        "request": "GetMap",
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "FORMAT": "image/png",
        "STYLES": "",
        "TRANSPARENT": "false",
        "transparent": "FALSE",
        "layers": "CVF:veje",
        "tiled": "true",
        "WIDTH": f"{width}",
        "HEIGHT": f"{height}",
        "SRS": "EPSG:25832",
        "BBOX": coordinateString,
    }

    response = requests.get(APIUrl, params=params)
    if response.status_code == 200:
        with open(path + "/routes.png", "wb") as e:
            e.write(response.content)
    else:
        print("Failed to fetch roads. Status code:", response.status_code)


def getBoundaries(min_lat, min_lon, max_lat, max_lon, width, height, path):
    """
    ## Downloads property boundary map from Dataforsyningen to specified path as boundaries.png.
        Uses implemented token in function.
        Prints returned errors from call.

    ## Parameters:
       - min_lat: minimum latitude (EPSG:4326)
       - min_lon: minimum longitude (EPSG:4326)
       - max_lat: maximum latitude  (EPSG:4326)
       - max_lon: maximum longitude (EPSG:4326)
       - width: width resolution of image.
       - height: height resolution of image.
       - path: Path to save image.

    """

    token = "Deleted"
    APIUrl = "https://api.dataforsyningen.dk/wms/MatGaeldendeOgForeloebigWMS_DAF"

    # Converting from EPSG:4326 to EPSG25832
    min_x, min_y, man_x, max_y = crsToSrs(min_lat, min_lon, max_lat, max_lon)

    # Concatenating into a comma seperated string.
    coordinateString = ",".join([str(min_x), str(min_y), str(man_x), str(max_y)])

    # Request parameters
    params = {
        "token": f"{token}",
        "version": "2.0.0",
        "service": "WMS",
        "request": "GetMap",
        "sld_version": "1.1.0",
        "layers": "MatrikelSkel_Gaeldende",
        "FORMAT": "image/png",
        "STYLES": "Sorte_skel",
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "TRANSPARENT": "false",
        "transparent": "FALSE",
        "WIDTH": f"{width}",
        "HEIGHT": f"{height}",
        "SRS": "EPSG:25832",
        "BBOX": coordinateString,
    }

    response = requests.get(APIUrl, params=params)
    if response.status_code == 200:
        with open(path + "/boundaries.png", "wb") as e:
            e.write(response.content)
    else:
        print("Failed to fetch roads. Status code:", response.status_code)


def getSatellite(min_lat, min_lon, max_lat, max_lon, width, height, path):
    """
    ## Downloads ortofoto images from Dataforsyningen to specified path as satellite.png.
        Uses implemented token in function.
        Prints returned errors from call.

    ## Parameters:
       - min_lat: minimum latitude (EPSG:4326)
       - min_lon: minimum longitude (EPSG:4326)
       - max_lat: maximum latitude  (EPSG:4326)
       - max_lon: maximum longitude (EPSG:4326)
       - width: width resolution of image.
       - height: height resolution of image.
       - path: Path to save image.

    """

    token = "Deleted"
    APIUrl = "https://api.dataforsyningen.dk/orto_foraar_DAF"

    # Converting from EPSG:4326 to EPSG25832
    min_x, min_y, man_x, max_y = crsToSrs(min_lat, min_lon, max_lat, max_lon)

    # Concatenating into a comma seperated string.
    coordinateString = ",".join([str(min_x), str(min_y), str(man_x), str(max_y)])

    # Request parameters
    params = {
        "token": f"{token}",
        "version": "1.3.0",
        "styles": "default",
        "service": "WMS",
        "request": "GetMap",
        "sld_version": "1.1.0",
        "layers": "orto_foraar",
        "FORMAT": "image/png",
        "transparent": "FALSE",
        "WIDTH": f"{width}",
        "HEIGHT": f"{height}",
        "CRS": "EPSG:25832",
        "BBOX": coordinateString,
    }

    response = requests.get(APIUrl, params=params)
    if response.status_code == 200:
        with open(path + "/satellite.png", "wb") as e:
            e.write(response.content)
    else:
        print("Failed to fetch roads. Status code:", response.status_code)


# Example to compare crs google orthophoto to srs dataforsyningen orthophoto
"""
56.151540792592655, 10.202991035233715
56.15252836947363, 10.201633243638183

dd = crsToSrs(
    56.151540792592655, 10.201633243638183, 56.15252836947363, 10.202991035233715
)

width = dd[2] - dd[0]
height = dd[3] - dd[1]

print(width, height)
ratio = 1000 / width
width = 1000
height = int(height * ratio)

getSatellite(
    56.151540792592655,
    10.201633243638183,
    56.15252836947363,
    10.202991035233715,
    width,
    height,
    "ITUData",
)
"""
