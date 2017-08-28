bit_flags = {
    "pixel_qa": {
        "L47": {
            "Fill": [0],
            "Clear": [1],
            "Water": [2],
            "Cloud Shadow": [3],
            "Snow": [4],
            "Cloud": [5],
            "Low Cloud Confidence": [6],
            "Medium Cloud Confidence": [7],
            "High Cloud Confidence": [6, 7]
        },
        "L8": {
            "Fill": [0],
            "Clear": [1],
            "Water": [2],
            "Cloud Shadow": [3],
            "Snow": [4],
            "Cloud": [5],
            "Low Cloud Confidence": [6],
            "Medium Cloud Confidence": [7],
            "High Cloud Confidence": [6, 7],
            "Low Cirrus Confidence": [8],
            "High Cirrus Confidence": [8, 9],
            "Terrain Occlusion": [10]
        }
    },

    "sr_cloud_qa": {
        "L47": {
            "DDV": [0],
            "Cloud": [1],
            "Cloud Shadow": [2],
            "Adjacent to Cloud": [3],
            "Snow": [4],
            "Water": [5]
        }
    },

    "radsat_qa": {
        "L47": {
            "Fill": [0],
            "Band 1 Data Saturation": [1],
            "Band 2 Data Saturation": [2],
            "Band 3 Data Saturation": [3],
            "Band 4 Data Saturation": [4],
            "Band 5 Data Saturation": [5],
            "Band 6 Data Saturation": [6],
            "Band 7 Data Saturation": [7]
        },
        "L8": {
            "Fill": [0],
            "Band 1 Data Saturation": [1],
            "Band 2 Data Saturation": [2],
            "Band 3 Data Saturation": [3],
            "Band 4 Data Saturation": [4],
            "Band 5 Data Saturation": [5],
            "Band 6 Data Saturation": [6],
            "Band 7 Data Saturation": [7],
            "Band 9 Data Saturation": [9],
            "Band 10 Data Saturation": [10],
            "Band 11 Data Saturation": [11]
        }
    },

    "BQA": {
        "L47": {
            "Fill": [0],
            "Dropped Pixel": [1],
            "Low Radiometric Saturation": [2],
            "Medium Radiometric Saturation": [3],
            "High Radiometric Saturation": [2, 3],
            "Cloud": [4],
            "Low Cloud Confidence": [5],
            "Medium Cloud Confidence": [6],
            "High Cloud Confidence": [5, 6],
            "Low Cloud Shadow Confidence": [7],
            "High Cloud Shadow Confidence": [7, 8],
            "Low Snow/Ice Confidence": [9],
            "High Snow/Ice Confidence": [9, 10]
        },
        "L8": {
            "Fill": [0],
            "Dropped Pixel": [1],
            "Low Radiometric Saturation": [2],
            "Medium Radiometric Saturation": [3],
            "High Radiometric Saturation": [2, 3],
            "Cloud": [4],
            "Low Cloud Confidence": [5],
            "Medium Cloud Confidence": [6],
            "High Cloud Confidence": [5, 6],
            "Low Cloud Shadow Confidence": [7],
            "High Cloud Shadow Confidence": [7, 8],
            "Low Snow/Ice Confidence": [9],
            "High Snow/Ice Confidence": [9, 10],
            "Low Cirrus Confidence": [11],
            "High Cirrus Confidence": [11, 12]
        }
    },

    "sr_aerosol": {
        "L8": {
            "Fill": [0],
            "Aerosol Retrieval - Valid": [1],
            "Aerosol Retrieval - Interpolated": [2],
            "Water": [3],
            "Low Aerosol": [6],
            "Medium Aerosol": [7],
            "High Aerosol": [6, 7]
        }
    }
}
