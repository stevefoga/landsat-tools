# Landsat Quality Assessment (QA) QGIS Toolbox
This tool color codes bit-packed Landsat Level-1 and Level-2 quality bands. More information regarding quality bands can be found on the [Landsat Mission Webpage](https://landsat.usgs.gov/).


## Version 0.1 Release Notes
Release Date: August 2017

No git tag associated with this release.

Developed and tested with QGIS Essen 2.14.1, which uses Python 2.7.5. 

### Changes
* Initial version of the code.

### TO-DO
* QGIS [does not support Raster Attribute Tables](https://issues.qgis.org/issues/4321), so the tool simply color-codes and re-names each category, but does not make them accessible for analysis. This is potentially useful only for mapping and quick visualization.
  * If Raster Attribute Table support becomes available, methodology needs revision in [decode_qa.py](./src/decode_qa.py).
* ~~Code could be simplified if qa_values variable is removed from [lookup_dict.py](./src/lookup_dict.py) and replaced with bit flags.~~ DONE 28 Aug 2017.
* Tool should ideally have functionality to unpack bands, and optionally combine into a binary raster.
* Tool should automatically populate input interface with sensor and band, based on input band name.
* Tool needs an icon besides the QGIS default.
* General code cleanup needed once complete.
* Documentation needs re-worked to be compliant with standards of host institution.
 
* (Optional) Include any other features included in [Landsat QA ArcGIS Toolbox](https://github.com/USGS-EROS/landsat-qa-arcgis-toolbox).


## Installation
The Landsat QA QGIS Toolbox can be installed using the following steps:
1. Navigate to the QGIS Python plugins directory,
    * Windows, QGIS 2.14.1: C:\Users\YOUR_USERNAME\\.qgis2\python\plugins\
2. In the plugins directory, create directory "landsat-qa-qgis-toolbox",
3. Extract the contents of the .zip file,
4. Copy all contents from inside the "src" directory to the "landsat-qa-qgis-toolbox" directory.


## Tool: Decode QA
Currently, the only tool in the toolbox is the "Decode QA" tool, which performs the following steps:
1. Builds an attribute table containing all unique values in the QA band,
2. Apply label and random color to each unique raster value, and
3. Add layer to QGIS interface.
