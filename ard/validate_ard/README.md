
# validate_ard
Validates Landsat Analysis Ready Data (ARD) tile bundles.

## Overview
The validate_ard tool is designed to evaluate geospatial parameters, archive integrity, XML metadata, and file naming conventions of ARD tile bundles.

## Requirements
* Python 3.5.x or greater
* Non-standard modules:
  * pandas
  * gdal (osgeo)
  * lxml
  * numpy

## Inputs
1) Tar bundle directory - directory containing all tar bundles and md5 hashes in single directory (i.e., not nested.)

2) CSV with tile extents - CSV file with tile coordinates and tile extents, in the following format:

| region | h | v | hv | ulx |	uly	| lrx | lry |
| --- | --- | --- | --- | --- | --- | --- | --- |
| HI | 0 | 0 | h0v0 | -444345 | 2168895 | -294345 |	2018895 |

where:
* **region**: can be **HI** (Hawaii), **AK** (Alaska), or **CU** (Conterminous United States (CONUS)),
* **h, v**: any tile coordinate, as integers,
* **ulx, uly, lrx, lry**: tile corner coordinates, as integers,
* hv (optional): string designation for h and v tile coordinates.

Note the input CSV file is provided here as **[ard_extents.csv](ard_extents.csv)**.

3) XML schema - schema file for ARD. Currently located at https://landsat.usgs.gov/sites/default/files/documents/ard_metadata_v1_0.xsd. 

## Outputs
All outputs delivered as plain text file. Examples shown in the [example_output](./example_output/) folder. 
1) No verbose
	* List of every file tested.
	* Only disagreements (False) shown in output.
2) Verbose
	* List of every file tested.
	* Both agreements (True) and disagreements (False) shown in output.

## Using validate_ard tool
validate.py 
  
  * Required:
    * -d /path/to/tar_bundle_directory/
    * -c /path/to/ard_extents.csv
    * -x /path/to/xml_schema.xsd
    * -o /path/to/output_directory/
  
  * Optional
    * --verbose 

## Example use
```bash
$ python validate.py -d /path/to/tar_bundle_directory/ -c /path/to/ard_extents.csv -x /path/to/xml_schema.xsd -o /path/to/output_directory/ --verbose
```
