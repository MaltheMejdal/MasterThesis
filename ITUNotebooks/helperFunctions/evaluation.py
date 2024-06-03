# ---    Dependencies    ---#
import geopandas as gpd
import leafmap
import tempfile
import matplotlib.pyplot as plt
from shapely.geometry import box
import requests
from PIL import Image
import numpy as np
import seaborn as sn
import pandas as pd
from matplotlib.colors import ListedColormap
import matplotlib.ticker as ticker


# ---    Functions    ---#
def displaySegmentation(latitude, longitude, shapefilePath, zoom):
    """
    ## Displays segmentation on satellite image.
        Uses leafmap supplied sattelite imeage.

    ## Parameters:
       - latitude : Center latitude of displayed image.
       - longitude : Center longitude of displayed image.
       - shapefilePath : Path to .shp file in directory with .cpg, .dbf, .prj, .shx file.
       - zoom : Initial zoom of displayed image.


    ## Returns:
       - leafmap map.
    """

    # Loading shapes.
    shapes = gpd.read_file(shapefilePath)

    # Creating tempoary file to hold data in GeoJSON format.
    with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as temp:
        temp.write(shapes.to_json().encode())

        # Creates interactive map.
        m = leafmap.Map(center=[latitude, longitude], zoom=zoom)

        # Adds satellite image to map.
        m.add_basemap("SATELLITE")

        # Adds shapes to map.
        style = {
            "color": "#f44336",
            "weight": 2,
            "opacity": 1,
            "fill": True,
            "fillColor": "#ff00ef",
            "fillOpacity": 0.25,
        }
        m.add_geojson(temp.name, style=style)
    return m


def displayShiftedSegm(
    latitude, longitude, shapefilePath, zoom, f_types, shift=(0, 0), scale=1.0
):
    """
    ## Displays segmentation on satellite image with shift and scale of shapes in relation to satellite image.
        Uses leafmap supplied sattelite imeage.
        Scale implementation is unsuccesful and removes shapes.

    ## Parameters:
       - latitude : Center latitude of displayed image.
       - longitude : Center longitude of displayed image.
       - shapefilePath : Path to .shp file in directory with .cpg, .dbf, .prj, .shx file.
       - zoom : Initial zoom of displayed image.
       - shift : tuple of latitude and longitude shift of shapes.
       - scale : scale to resize shapes.

    ## Returns:
       - leafmap map.
    """

    # Loading and filtering shapes.
    shapes = gpd.read_file(shapefilePath)
    shapes = shapes[shapes["f_type"].isin(f_types)]

    # Shifting and scaling of shapes.
    shapes.geometry = shapes.geometry.translate(xoff=shift[0], yoff=shift[1]).scale(
        xfact=scale, yfact=scale, origin=(latitude, longitude)
    )

    # Creating tempoary file to hold data in GeoJSON format.
    with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as temp:
        temp.write(shapes.to_json().encode())

        # Creates interactive map.
        m = leafmap.Map(center=[latitude, longitude], zoom=zoom)

        # Adds shapes to map.
        style = {
            "color": "#f44336",
            "weight": 2,
            "opacity": 1,
            "fill": True,
            "fillColor": "#ff00ef",
            "fillOpacity": 0.25,
        }
        m.add_geojson(temp.name, style=style)
    return m


def displayFTypeSegm(latitude, longitude, shapefilePath, zoom, f_types):
    """
    ## Displays segmentation on satellite image with filtering of shapes.

    ## Parameters:
       - latitude : Center latitude of displayed image.
       - longitude : Center longitude of displayed image.
       - shapefilePath : Path to .shp file in directory with .cpg, .dbf, .prj, .shx file.
       - zoom : Initial zoom of displayed image.
       - f_types : array of displayed shapes from selection : ['sidewalk','road','crosswalk']


    ## Returns:
       - leafmap map.
    """

    # Loading shapes.
    shapes = gpd.read_file(shapefilePath)

    # Filter the GeoDataFrame based on the f-type attribute
    filteredShapes = shapes[shapes["f_type"].isin(f_types)]

    # Creating tempoary file to hold data in GeoJSON format.
    with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as temp:
        temp.write(filteredShapes.to_json().encode())

        # Creates interactive map.
        m = leafmap.Map(center=[latitude, longitude], zoom=zoom)

        # Adds satellite image to map.
        m.add_basemap("SATELLITE")

        # Adds shapes to map.
        style = {
            "color": "#f44336",
            "weight": 2,
            "opacity": 1,
            "fill": True,
            "fillColor": "#ff00ef",
            "fillOpacity": 0.3,
        }
        m.add_geojson(temp.name, style=style)
    return m


def ConvertToMask(shapefilePath, f_types, outputpath, bbox):
    """
    ## Creates mask of shapes bounded by boundary coordinates.
        Shapes are displayed as black on white background.
        Some noisy grey pixels occur.
        Saves mask as .jpg file.

    ## Parameters:
       - shapefilePath : Path to .shp file in directory with .cpg, .dbf, .prj, .shx file.
       - f_types : array of displayed shapes from selection : ['sidewalk','road','crosswalk'].
       - outputpath : Output directory path.
       - bbox : Array of bounding box coordinates of form [minimum longitude , minimum latitude , maximum longitude , max latitude].

    """

    # Read shapefile
    gdf = gpd.read_file(shapefilePath)
    outputpath += "\\mask.jpg"

    # Filter shape types
    filteredShapes = gdf[gdf["f_type"].isin(f_types)]

    # Create a bounding box with the coordinates to ensure proper dimensions
    boundingBox = box(*bbox)

    # Convert bounding box to GeoDataFrame
    shapesGeoDF = gpd.GeoDataFrame(geometry=[boundingBox], crs="EPSG:4326")

    # Reproject bounding box to match the CRS of shapefile
    shapesGeoDF = shapesGeoDF.to_crs(gdf.crs)

    # Create the plot
    ax = filteredShapes.plot(color="black", edgecolor="black", figsize=(10, 10))

    # Set plot limit
    ax.set_xlim(shapesGeoDF.total_bounds[0], shapesGeoDF.total_bounds[2])
    ax.set_ylim(shapesGeoDF.total_bounds[1], shapesGeoDF.total_bounds[3])

    # Remove axis
    ax.axis("off")

    # Save the plot as an image file
    fig = ax.get_figure()
    fig.savefig(outputpath, dpi=600, bbox_inches="tight", pad_inches=0)
    plt.show()


def getSatellite(minLon, minLat, maxLon, maxLat, width, height, outputDir):
    """
    ## Downloads satellite image in bounding box from MapBox with resolution matching mask for further comparison.
        Satellite images from MapBox have are limited to 1200x1200 pixels before resizing, thus quality is lower than google tiles api.

    ## Parameters:
       - minLon : minimum longitude boundary.
       - minLat : minimum latitude boundary.
       - maxLon : maximum longitude boundary.
       - maxLat : maximum latitude boundary.
       - width : Output image width
       - height : Output image height
       - outputDir : Output directory path.

    """

    # MapBox token issued by MapBox
    token = "Deleted"

    # Base URL for request.
    baseURL = "https://api.mapbox.com/styles/v1/mapbox/satellite-v9/static/"

    # User information.
    userAgent = "ITU Thesis Malthe Mejdal "
    headers = {"User-Agent": userAgent}

    # Api supports a max resolution of 1200
    ratio = min(1200 / width, 1200 / height)
    newWidth = int(width * ratio)
    newHeight = int(height * ratio)

    # Assemblying request URL
    url = f"{baseURL}[{minLat},{minLon},{maxLat},{maxLon}]/{newWidth}x{newHeight}?access_token={token}"

    # Assemblying file path.
    filename = f"{outputDir}/satellite.jpg"

    # Download the satellite image and handle potential errors
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()  # Raise an exception for unsuccessful requests

        # Write image to file.
        with open(filename, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

        # Resizing image.
        img = Image.open(filename)
        img_resized = img.resize((width, height))
        img_resized.save(filename)  # Overwrite the original image with the resized one

    except requests.exceptions.RequestException as e:
        print(f"Error downloading tile {url}: {e}")


def compare(shapesMaskPath, groundTruthPath):
    """
    ### Compares shapes to ground truth, displaying confusion matrix and result map.


    ### Parameters:
       - maskPath : Shapes mask path.
       - groundTruthPath : Ground truth path.

    """

    # Load mask images
    shapesMask = np.array(Image.open(shapesMaskPath).convert("L"))
    groundTruthMask = np.array(Image.open(groundTruthPath).convert("L"))

    # Create a new image for visualization
    height, width = shapesMask.shape
    resultMap = np.zeros((height, width, 3), dtype=np.uint8)

    # Initialize counts for confusion matrix.
    tp = fp = fn = tn = 0

    # Looping through pixels comparing masks. Generates result map and confusion matrix.
    for i in range(height):
        for j in range(width):

            # Getting pixels.
            shapePixel = shapesMask[i, j]
            gtPixel = groundTruthMask[i, j]

            # Comparison.
            if shapePixel == 0 and gtPixel == 0:  # Both are black (true)
                resultMap[i, j] = [0, 255, 0]  # Set result Green
                tp += 1
            elif shapePixel == 0 and gtPixel > 0:  # Shape is black, GT is white
                resultMap[i, j] = [255, 255, 0]  # Set result Yellow
                fp += 1
            elif shapePixel > 0 and gtPixel == 0:  # Shape is white, GT is black
                resultMap[i, j] = [255, 0, 0]  # Set result Red
                fn += 1
            else:  # Both are white (negative)
                resultMap[i, j] = [0, 0, 0]  # Set result White
                tn += 1

    # Calculating precision, recall and accuracy
    precision = tp / (tp + fp) if (tp + fp) != 0 else 0
    recall = tp / (tp + fn) if (tp + fn) != 0 else 0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + fp + tn + fn) != 0 else 0

    # Display the result image
    plt.figure(figsize=(13, 13))
    plt.imshow(resultMap)
    plt.axis("off")
    plt.show()

    # Creating dataframe for matrix values
    values = [[tp, fn], [fp, tn]]
    df = pd.DataFrame(
        values,
        index=["GT positive", "GT negative"],
        columns=["Pred. positive", "Pred. negative"],
    )

    # Creating new plot
    plt.figure(figsize=(6, 6))

    # Creating heatmap structure without colors.
    sn.heatmap(
        df,
        annot=True,
        cmap=ListedColormap(["white"]),
        cbar=False,
        fmt=",.0f",
        annot_kws={"size": 12},
        linewidths=1,
        linecolor="black",
        square=False,
    )

    # Increase label size.
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)

    # Displaying confusion matrix and performance metrics.
    plt.show()
    print("Precision:", round(precision, 2))
    print("Recall:", round(recall, 2))
    print("Accuracy:", round(accuracy, 2))
