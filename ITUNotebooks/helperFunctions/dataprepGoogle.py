# ---    Dependencies    ---#
import math
import requests
import time
from tqdm import tqdm
import os


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


def get_session_token(apiKey):
    """
    ## Requests a session and returns token from Google Tile API if status code 200 is recieved.

    ## Parameters:
        - apiKey : Api key issued by Google.

    ## Returns:
        - Session token if succeeded.

    """

    # Request url
    url = "https://tile.googleapis.com/v1/createSession?key=" + apiKey

    # Headers
    headers = {"Content-Type": "application/json"}

    # Parameters
    data = {"mapType": "satellite", "language": "en-US", "region": "EU"}

    # Requesting data from API.
    response = requests.post(url, json=data, headers=headers)

    # Checking if succeeded.
    if response.status_code == 200:
        responseJson = response.json()
        sessionToken = responseJson.get("session")
        return sessionToken
    else:
        print("Failed to retrieve session token. Status code:", response.status_code)
        return None


def getTiles(zoom, minLat, minLon, maxLat, maxLon, outputDir, apiKey, sessionToken):
    """
    ## Fetches and saves tiles from Google Tiles API

    ## Parameters:
       - minLat : minimum latitude boundary.
       - minLon : minimum longitude boundary.
       - maxLat : maximum latitude boundary.
       - maxLon : maximum longitude boundary.
       - outputDir : Output directive path.
       - apiKey : API key issued by Google.
       - sessionToken : Session toen issued by Google.

    ## Throws:
        - HTTPError : If request failed.

    ## Returns:
       None.
       Prints status messages.
    """

    baseURL = "https://tile.googleapis.com/v1/2dtiles/"

    # User information
    userAgent = "ITU Thesis Malthe Mejdal "
    headers = {"User-Agent": userAgent}

    # Getting tile index
    xMin, xMax, yMin, yMax = deg2tileNum(minLat, maxLat, minLon, maxLon, zoom)

    # Calculating number of tiles.
    totalTiles = (xMax - xMin + 1) * (yMax - yMin + 1)

    # Creating status bar
    status = tqdm(total=totalTiles, desc="Downloading tiles")

    # Looping through all index sets.
    for x in range(xMin, xMax + 1):
        for y in range(yMin, yMax + 1):

            # Creating URL
            url = f"{baseURL}{zoom}/{x}/{y}?session={sessionToken}&key={apiKey}"

            # Determining file path and name.
            filePath = f"{outputDir}/{x}_{y}.png"

            try:
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()

                with open(filePath, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                    status.update(1)
                    status.set_postfix({"Tile": f"{x},{y}"})
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {url} -  {e}")
            time.sleep(0.1)
    status.close()


def createDirectory(projectName, resolution, zoom):
    """
    ## Creates directory to hold tiles in corrosponding with Tile2Net naming convention.

    ## Throws:
        OSError : If directory could not be created.

    ## Parameters:
        - projectName : Unique project identifier
        - resolution : Resolution of tiles.
        - Zoom : Used zoom level.

    ## Returns:
       - Output directory
    """

    # Assemblying directory path
    outputDir = f"C:\\Users\\Nielsen\\Desktop\\tile2net\\tile2net-main\\ITUData\\Google\\tiles\\{projectName}\\tiles\\static\\{resolution}_{zoom}"

    if not os.path.exists(outputDir):

        try:
            os.makedirs(outputDir)
            print(f"Directory '{outputDir}' created.")
        except OSError as e:
            print(f"{outputDir} - {e}")
            return None

    else:
        print(f"Directory '{outputDir}' found.")

    return outputDir
