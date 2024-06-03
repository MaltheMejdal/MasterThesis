# ---    Dependencies    ---#
import math
import requests
import time
from tqdm import tqdm
import os


# ---    Functions    ---#
def tileSysConv(x1, y1, x2, y2):
    """
    ## Converts global tile coordinate boundaries to Dataforsyningen tile coordinate boundaries.

    I was unable to establish a relationship between the two systems as the tile systems overlap.

    ## Parameters:
       - x1: minimum x coordinate
       - y1: minimum y coordinate
       - x2: maximum x coordinate
       - y2: maximum y coordinate

    ## Returns:
       - x1, y1, x2, y2 coordinates of EPSG:4326 WGS 84 system.

    """

    zoom = 15
    xStart = 120000
    yStart = 5900000
    xEnd = 1000000
    yEnd = 6500000
    matrixWidth = 68750
    matrixHeight = 46875
    xSpan = xEnd - xStart
    ySpan = yEnd - yStart

    xRatio = xSpan / matrixWidth
    yRatio = ySpan / matrixHeight

    x1Tile = int((x1 - xStart) / xRatio + 1)
    y1Tile = int(matrixHeight - ((y1 - yStart) / yRatio + 1))
    x2Tile = int((x2 - xStart) / xRatio + 1)
    y2Tile = int(matrixHeight - ((y2 - yStart) / yRatio + 1))

    xMinTile = min(x1Tile, x2Tile)
    xMaxTile = max(x1Tile, x2Tile)
    yMinTile = min(y1Tile, y2Tile)
    yMaxTile = max(y1Tile, y2Tile)

    # return xMinTile, xMaxTile, yMinTile, yMaxTile
    return 35479, 35489, 21566, 21571


def getTiles(minXC, minYC, maxXC, maxYC, outputDir, token):
    """
    ## Fetches and saves tiles from dataforsyningen spring ortofoto API

    Tile matrix 15 is being used, being the tile system of highest resolution. This is the equevalent to zoom of other tile systems.

    ## Parameters:
       - minXC: minimum x coordinate.
       - minYC: minimum y coordinate.
       - maxXC: maximum x coordinate.
       - maxYC: maximum y coordinate.
       - outputDir: Output directive path.
       - token: Token for API usage, issued by dataforsyningen.

    ## Returns:
       None.
       Prints status messages.
    """

    # Endpoint of API
    baseURL = "https://api.dataforsyningen.dk/orto_foraar_wmts_DAF"

    # User data in header
    userAgent = "ITU Thesis Malthe Mejdal "
    headers = {"User-Agent": userAgent}

    # Tile boundaries.
    xMin, xMax, yMin, yMax = tileSysConv(minXC, minYC, maxXC, maxYC)

    # Status bar
    totalTiles = (xMax - xMin + 1) * (yMax - yMin + 1)
    status = tqdm(total=totalTiles, desc="Downloading tiles")

    # Looping through each tile coordinate set.
    for x in range(xMin, xMax + 1):
        for y in range(yMin, yMax + 1):

            # Assembling URL for api call.
            url = f"{baseURL}?token={token}&layer=orto_foraar_wmts&style=default&tilematrixset=KortforsyningTilingDK&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image%2Fjpeg&TileMatrix=15&TileCol={x}&TileRow={y}"

            # Path and naming of file
            filePath = f"{outputDir}/{x}_{y}.png"

            # Making API call
            try:
                response = requests.get(url, headers=headers, stream=True)
                response.raise_for_status()

                # Writing to file.
                with open(filePath, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                    status.update(1)
                    status.set_postfix({"Tile": f"{x},{y}"})
            except requests.exceptions.RequestException as e:
                print(f"Error downloading {url} - {e}")

            # Some APIs may require a timeout between requests.
            time.sleep(0.1)
    status.close()


def createDirectory(resolution, zoom):
    """
    ## Creates directory to hold tiles in corrosponding with Tile2Net naming convention.


    ## Parameters:
        - Resolution of tiles.
        - Zoom.

    ## Returns:
       - Output directory
    """
    output_dir = f"C:\\Users\\Nielsen\\Desktop\\tile2net\\tile2net-main\\ITUData\\Dataforsyningen\\tiles\\static\\{resolution}_{zoom}"

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Directory '{output_dir}' created.")
        except OSError as e:
            print(f"{output_dir} -  {e}")
            return None
    else:
        print(f"Directory '{output_dir}' found.")
    return output_dir
