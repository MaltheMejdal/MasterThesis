import cv2
import numpy as np


def loadImages(pathMaps):
    """
    ## Loads images from path.
    Loads:
    "/AM_with_roads.png",
    "/boundaries.png",
    "/routes.png",
    "/AM_Detailed.png",
    "/satellite.png"

    ## Parameters:
       - path: Path to folder containing images.

    """

    am_withRoads = cv2.imread(pathMaps + "/AM_with_roads.png")
    boundaries = cv2.imread(pathMaps + "/boundaries.png")
    routes = cv2.imread(pathMaps + "/routes.png")
    amBaseMap = cv2.imread(pathMaps + "/AM_Detailed.png")
    satellite = cv2.imread(pathMaps + "/satellite.png")

    return am_withRoads, boundaries, routes, amBaseMap, satellite


def privatePropertyFiltering(amBaseMap, boundariesImage, routesImage, pathResult):

    # Copy object to prevent referencing errors
    amBaseMap = amBaseMap.copy()
    boundariesImage = boundariesImage.copy()
    routesImage = routesImage.copy()

    # Convert the image to greyscale
    boundariesGrey = cv2.cvtColor(boundariesImage, cv2.COLOR_BGR2GRAY)

    # Convert to binary, seperating edges from background
    ret, boundariesBinary = cv2.threshold(boundariesGrey, 254, 255, cv2.THRESH_OTSU)

    cv2.imwrite(pathResult + "/subresults/001_Boundary.png", boundariesBinary)

    # Enhance the black lines for proper contour detection.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    boundariesBinary = ~boundariesBinary
    boundariesBinary = cv2.dilate(boundariesBinary, kernel)
    boundariesBinary = ~boundariesBinary

    cv2.imwrite(pathResult + "/subresults/002_Boundary_dialated.png", boundariesBinary)

    # Find contours. RETR_TREE makes it return a hierachi, which we don't use anyways. It may have the potential to be used to filter some areas. Chain approximation is turned off to keep full point detail. Can be turned off to save memory.
    contours, _ = cv2.findContours(
        boundariesBinary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )

    # Filter contours based on area, to avoid contours covering the entire image and small noise induced contours.
    width, height, _ = boundariesImage.shape
    totalPixels = width * height
    contours = [
        contour
        for contour in contours
        if cv2.contourArea(contour) < totalPixels / 2 and cv2.contourArea(contour) > 100
    ]

    # Iterate over each contour:
    for _, contour in enumerate(contours):

        # Mask for selected contour:
        contourMask = np.zeros_like(boundariesGrey)
        cv2.drawContours(contourMask, [contour], -1, (255, 255, 255), cv2.FILLED)

        # Get region from routes.
        boundariesRegion = cv2.bitwise_and(routesImage, routesImage, mask=contourMask)

        # count green pixels in region.
        greenMask = cv2.inRange(boundariesRegion, (0, 150, 0), (30, 255, 30))
        greenMaskPixelCount = cv2.countNonZero(greenMask)

        # decide if it contains green pixels,
        if greenMaskPixelCount > 0:
            # Contains green pixels, fill with green. (public area)
            color = (0, 255, 0)
        else:
            # No green pixels, fill with red (Private area)
            color = (0, 0, 255)  # Red color

        # Fill the areas into boundaries image.
        cv2.drawContours(boundariesImage, [contour], -1, color, cv2.FILLED)

    cv2.imwrite(pathResult + "/subresults/003_Boundary_Contour.png", boundariesImage)

    # Blur to get rid of contour lines.
    boundariesImage = cv2.medianBlur(boundariesImage, 7)

    cv2.imwrite(
        pathResult + "/subresults/004_Boundary_Contour_Blurred.png", boundariesImage
    )

    # Convert the image to HSV color and filter for green pixels, to convert to a binary map.
    hsv = cv2.cvtColor(boundariesImage, cv2.COLOR_BGR2HSV)
    lowerGreen = np.array([40, 40, 40])  # Lower limit for green (HSV)
    upperGreen = np.array([80, 255, 255])  # Upper limit for green (HSV)
    contourMask = cv2.inRange(hsv, lowerGreen, upperGreen)

    filteredBoundaries = cv2.bitwise_not(contourMask)

    # Removing areas from map.
    amBaseMap[filteredBoundaries == 255] = [0, 0, 255]

    cv2.imwrite(pathResult + "/subresults/005_Result.png", amBaseMap)

    return amBaseMap


def structureFiltering(amDetailed, structures, pathResult):
    """
    ## Removes structures.
    Saves subresults.
    Might cause worse precision due to overhang of sidewalks.

    ## Parameters:
       - amDetailed: detailed Administrative Map.
       - amWithRoads: Administrative Map with roads.
       - pathResult: Path to save subresults.

    """

    # Copy object to prevent referencing errors
    amDetailed = amDetailed.copy()
    structures = structures.copy()

    # Convert to HSV
    amWithRoadsHSV = cv2.cvtColor(structures, cv2.COLOR_BGR2HSV)

    # Building color range (yellow/orange)
    lowerYellow = np.array([10, 50, 50])  # Lower limit for yellow (HSV)
    upperYellow = np.array([60, 255, 255])  # Upper limit for yellow (HSV)

    # Create mask of pixels matching.
    mask = cv2.inRange(amWithRoadsHSV, lowerYellow, upperYellow)

    # Create red image
    redSolidMask = np.zeros_like(structures)
    redSolidMask[:] = [0, 0, 255]

    # Apply mask to only have a mask of the red areas.
    redMask = cv2.bitwise_and(redSolidMask, redSolidMask, mask=mask)

    cv2.imwrite(pathResult + "/subresults/006_Structures_Redmask.png", redMask)

    # Fill in red areas.
    amDetailed[np.where((redMask == [0, 0, 255]).all(axis=2))] = [0, 0, 255]

    cv2.imwrite(pathResult + "/subresults/007_Structures_Removed.png", amDetailed)

    return amDetailed


def routeAndVegFiltering(amBaseMap, routesImage, satellite, pathResult):

    # Copying image objects
    amBaseMap = amBaseMap.copy()
    routesImage = routesImage.copy()

    # Color ranges to get brown and green lines, and blue water.
    brown_lower = np.array([200, 215, 230], dtype=np.uint8)
    brown_upper = np.array([210, 230, 240], dtype=np.uint8)

    green_lower = np.array([205, 230, 210], dtype=np.uint8)
    green_upper = np.array([220, 255, 235], dtype=np.uint8)

    blue_lower = np.array([250, 235, 215], dtype=np.uint8)
    blue_upper = np.array([255, 245, 225], dtype=np.uint8)

    # Mask for brown color range
    brown_mask = cv2.inRange(amBaseMap, brown_lower, brown_upper)
    # Mask for green color range
    green_mask = cv2.inRange(amBaseMap, green_lower, green_upper)
    # Mask for blue color range
    blue_mask = cv2.inRange(amBaseMap, blue_lower, blue_upper)

    # Combine masks
    combined_mask = cv2.bitwise_or(brown_mask, green_mask)
    combined_mask = cv2.bitwise_or(combined_mask, blue_mask)

    cv2.imwrite(pathResult + "/subresults/008_Filtering_Blue_Mask.png", blue_mask)
    cv2.imwrite(pathResult + "/subresults/009_Filtering_Brown_Mask.png", brown_mask)
    cv2.imwrite(pathResult + "/subresults/010_Filtering_Green_Mask.png", green_mask)
    cv2.imwrite(
        pathResult + "/subresults/011_Filtering_Combined_Mask.png", combined_mask
    )

    # Invert the mask to get non-matching pixels
    non_matching_pixels_mask = cv2.bitwise_not(combined_mask)

    # Set non-matching pixels to white (Deleting the lines)
    amBaseMap[non_matching_pixels_mask == 0] = [255, 255, 255]

    cv2.imwrite(pathResult + "/subresults/012_Filtering_Result.png", amBaseMap)

    # Apply filter to get rid of noise from deleted lines.
    amBaseMap = cv2.bilateralFilter(amBaseMap, 5, 255, 255)

    cv2.imwrite(pathResult + "/subresults/013_Filtering_Noise_Reduced.png", amBaseMap)

    # Convert the image to grayscale
    amBaseMapGrey = cv2.cvtColor(amBaseMap, cv2.COLOR_BGR2GRAY)

    # Convert to binary, separating edges from background
    ret, amBaseMapBinary = cv2.threshold(amBaseMapGrey, 245, 255, cv2.THRESH_BINARY)

    cv2.imwrite(pathResult + "/subresults/014_Filtering_Binary.png", amBaseMapBinary)

    # Inverting image
    amBaseMapBinary = ~amBaseMapBinary

    # Enhance the black lines for proper contour detection.
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    amBaseMapBinary = cv2.dilate(amBaseMapBinary, kernel)

    # Invert image back to normal.
    amBaseMapBinary = ~amBaseMapBinary

    cv2.imwrite(pathResult + "/subresults/015_Enhanced_Lines.png", amBaseMapBinary)

    # Find contours
    contours, _ = cv2.findContours(
        amBaseMapBinary, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE
    )

    # Filter contours based on area, to avoid contours covering the entire image and small noise-induced contours.
    width, height, _ = amBaseMap.shape
    totalPixels = width * height
    contours = [
        contour
        for contour in contours
        if cv2.contourArea(contour) < totalPixels / 2 and cv2.contourArea(contour) > 100
    ]

    # Convert to grey
    grey_image = cv2.cvtColor(routesImage, cv2.COLOR_BGR2GRAY)

    # Threshold the greyscale image to create a binary image
    _, binaryImage = cv2.threshold(grey_image, 240, 255, cv2.THRESH_BINARY)
    binaryImage = ~binaryImage

    cv2.imwrite(pathResult + "/subresults/016_Routes_Binary.png", binaryImage)

    # Convert to HSV for color detection
    satellite_hsv = cv2.cvtColor(satellite, cv2.COLOR_BGR2HSV)

    # Range of green color in HSV
    lower_green = np.array([85 / 2, 2 * 2.5, 2 * 2.5])
    upper_green = np.array([145 / 2, 100 * 2.5, 100 * 2.5])

    # Filter mask of green colors
    green_mask = cv2.inRange(satellite_hsv, lower_green, upper_green)

    cv2.imwrite(pathResult + "/subresults/017_1_Satellite_Green_Mask.png", green_mask)

    kernel = np.ones((5, 5), np.uint8)
    green_mask = cv2.erode(green_mask, kernel, iterations=1)

    cv2.imwrite(
        pathResult + "/subresults/017_2_Satellite_Green_Mask_Reduced.png", green_mask
    )

    for _, contour in enumerate(contours):

        # Create a mask for the current contour
        contourMask = np.zeros_like(binaryImage, dtype=np.uint8)
        cv2.drawContours(contourMask, [contour], -1, 255, cv2.FILLED)

        # Extract the region from the binary image using the contour mask
        region = cv2.bitwise_and(binaryImage, contourMask)

        # Count the number of total pixels in region.
        totalPixelCount = cv2.countNonZero(contourMask)
        # Count the number of number of true pixels
        whitePixelCount = cv2.countNonZero(region)

        # Check if there are true pixels (roads)
        if whitePixelCount / totalPixelCount > 0.001:
            # if true, fill with red.
            color = (0, 0, 255)
            cv2.drawContours(amBaseMap, [contour], -1, color, cv2.FILLED)

        else:

            # Else check if there are green pixels in satellite indicating a green area.

            # Create mask of contour
            contourMask = np.zeros_like(green_mask, dtype=np.uint8)
            cv2.drawContours(contourMask, [contour], -1, 255, cv2.FILLED)

            # Extract the region from satellite green mask.
            region = cv2.bitwise_and(green_mask, contourMask)

            # Count the number of green pixels.
            greenPixelCount = cv2.countNonZero(region)

            # calculate the coverage degree / The ratio of green pixels.
            greenCoverage = greenPixelCount / totalPixelCount

            # Check if it is above the treshold of 10%
            if greenCoverage > 0.10:
                # Fill the contour with red.
                color = (0, 0, 255)
                cv2.drawContours(amBaseMap, [contour], -1, color, cv2.FILLED)

    # Create a copy of the base map image to draw contours on
    amBaseMap_with_contours = amBaseMap.copy()

    # Compare AM with roads.
    overlay = cv2.addWeighted(amBaseMap_with_contours, 1 - 0.5, routesImage, 0.5, 0)
    cv2.imwrite(pathResult + "/subresults/018_AM_Roads_Overlay.png", overlay)

    # Draw contours on the copy of the base map image
    cv2.drawContours(amBaseMap_with_contours, contours, -1, (0, 255, 0), 1)

    cv2.imwrite(pathResult + "/subresults/019_AM_Contours.png", amBaseMap_with_contours)

    # Convert to greyscale.
    amBaseMap_grey = cv2.cvtColor(amBaseMap, cv2.COLOR_BGR2GRAY)

    # Apply treshold to get it to a binary map of white (All empty areas) and black (All red areas).
    _, binaryImage = cv2.threshold(
        amBaseMap_grey, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )

    # invert binary
    binaryImage = cv2.bitwise_not(binaryImage)
    cv2.imwrite(pathResult + "/subresults/020_AM_Binary.png", binaryImage)

    # Remove noise, as could be thin contour lines.
    kernel = np.ones((4, 4), np.uint8)
    binaryReducedStage1 = cv2.morphologyEx(binaryImage, cv2.MORPH_OPEN, kernel)
    binaryReducedStage1 = cv2.morphologyEx(binaryReducedStage1, cv2.MORPH_CLOSE, kernel)
    binaryReducedStage2 = binaryReducedStage1.copy()
    binaryReducedStage2 = cv2.medianBlur(binaryReducedStage2, 15)

    cv2.imwrite(pathResult + "/subresults/021_AM_Reduced_1.png", binaryReducedStage1)
    cv2.imwrite(pathResult + "/subresults/021_AM_Reduced_2.png", binaryReducedStage2)

    return binaryReducedStage2


def removeRailways():
    return True


def segmentAM(
    amBaseMap, amWithRoads, boundariesImage, routesImage, satellite, pathResult
):
    """
    ## Segments administrative map by cross referencing with other maps.
        Does not consider buildings or structures.
        Saves subresults.

    ## Parameters:
       - amBaseMap: Administrative Base Map.
       - am_withRoads: Administrative Map with roads.
       - boundaries: Property boundary map.
       - routes: Route map of roads and walking paths.
       - ortofoto: Satellite or aerial image.
       - path: Path to save images.

    """

    amDetailed = privatePropertyFiltering(
        amBaseMap, boundariesImage, routesImage, pathResult
    )
    amDetailed = routeAndVegFiltering(amDetailed, routesImage, satellite, pathResult)
    cv2.imwrite(pathResult + "/segmented.jpg", amDetailed)

    return segmentAM


def segmentAM_noStructures(
    amBaseMap,
    structures,
    boundaries,
    routes,
    ortofoto,
    pathResultNoStructures,
):
    """
    ## Segments administrative map by cross referencing with other maps.
        Excludes areas covered by buildings and structures, which may cover sidewalks.
        Saves subresults.

    ## Parameters:
       - amBaseMap: Administrative Base Map.
       - am_withRoads: Administrative Map with roads.
       - boundaries: Property boundary map.
       - routes: Route map of roads and walking paths.
       - ortofoto: Satellite or aerial image.
       - path: Path to save images.

    """
    amDetailed = privatePropertyFiltering(
        amBaseMap, boundaries, routes, pathResultNoStructures
    )
    amDetailed = structureFiltering(amDetailed, structures, pathResultNoStructures)
    amDetailed = routeAndVegFiltering(
        amDetailed, routes, ortofoto, pathResultNoStructures
    )
    cv2.imwrite(pathResultNoStructures + "/segmented.jpg", amDetailed)

    return segmentAM
