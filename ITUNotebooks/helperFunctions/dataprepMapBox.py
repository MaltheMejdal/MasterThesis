# ---    Dependencies    ---#
import math
import requests
import time
from tqdm import tqdm


# ---    Functions    ---#
def deg2tileNum(latDeg1, latDeg2, lonDeg1, lonDeg2, zoom):
    """
    ## Converts EPSG:4326 WGS 84 coordinate boundaries to global tile index boundaries.

    Inspiration source: https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames

    ## Parameters:
       - latDeg1 : latitude coordinate 1.
       - latDeg2 : latitude coordinate 2.
       - lonDeg1 : longitude coordinate 1.
       - lonDeg2 : longitude coordinate 2.
       - zoom : Tile zoom value.


    ## Returns:
       - xMin, xMax, yMin, yMax : Global tile index span.
    """

    # Converting coordinates to radians.
    latRad1 = math.radians(latDeg1)
    latRad2 = math.radians(latDeg2)

    # Calculating number of tiles using bitwise shifting.
    n = 1 << zoom

    # Index set 1
    x1 = int((lonDeg1 + 180.0) / 360.0 * n)
    y1 = int((1.0 - math.asinh(math.tan(latRad1)) / math.pi) / 2.0 * n)

    # Index set 2
    x2 = int((lonDeg2 + 180.0) / 360.0 * n)
    y2 = int((1.0 - math.asinh(math.tan(latRad2)) / math.pi) / 2.0 * n)

    # Determining start and end index.
    xMin = min(x1, x2)
    xMax = max(x1, x2)
    yMin = min(y1, y2)
    yMax = max(y1, y2)

    return xMin, xMax, yMin, yMax


def getTiles(zoom, minLat, minLon, maxLat, maxLon, outputDir):
    """
    ## Fetches and saves tiles from Google Tiles API

    ## Parameters:
       - minLat : minimum latitude boundary.
       - minLon : minimum longitude boundary.
       - maxLat : maximum latitude boundary.
       - maxLon : maximum longitude boundary.
       - outputDir : Output directive path.

    ## Throws:
        - HTTPError : If request failed.

    ## Returns:
       None.
       Prints status messages.
    """

    # Access token issued by MapBox
    token = "Deleted"

    # Request URL base
    baseURL = "https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/"

    # User information
    userAgent = "ITU Thesis Malthe Mejdal "
    headers = {"User-Agent": userAgent}

    # Getting tile index
    xMin, xMax, yMin, yMax = deg2tileNum(minLat, maxLat, minLon, maxLon, zoom)

    # Creating status bar.
    totalTiles = (xMax - xMin + 1) * (yMax - yMin + 1)
    progress_bar = tqdm(total=totalTiles, desc="Downloading tiles")

    # Looping through tile index sets.
    for x in range(xMin, xMax + 1):
        for y in range(yMin, yMax + 1):

            # Assembying request URL.
            url = f"{baseURL}{zoom}/{x}/{y}/?access_token={token}"

            # getting file path and name.
            filePath = f"{outputDir}/{x}_{y}.png"

            # Download the tile and handle potential errors
            try:
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()  # Raise an exception for unsuccessful requests

                with open(filePath, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                    progress_bar.update(1)  # Update progress bar
                    progress_bar.set_postfix({"Tile": f"{x},{y}"})
            except requests.exceptions.RequestException as e:
                print(f"Error downloading tile {url}: {e}")
            time.sleep(0.1)

    progress_bar.close()
