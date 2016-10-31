'''
create_scenelist_from_metdata.py


Purpose:  For all CSV files in a directory, open them, grab the first column
          of data, combine them, and output into a single text file.
          
          Useful if multiple metadata files created by EarthExplorer, and need
          a single text file to submit to ESPA.

          
Inputs:   Directory containing CSV file(s).


Output:   Single text file of Landsat scene IDs.


Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  31 October 2016


Changelog:
  31 OCT 2016 - Original creation.
  
'''
##############################################################################
import sys
def scene_from_meta(dir_in):
  
  import os
  import csv
  import glob
  
  ## find all text files
  fn_in = glob.glob(dir_in + os.sep + "*.csv")
  
  if len(fn_in) == 0:
    print("\nNo input CSV file(s) found!\n")
    sys.exit(1)
  
  ## allocate variable for scene ids
  sid = []
  
  ## read sceneID column from each text file
  it = 0
  for i in fn_in:
    
    ## open CSV file
    with open(i, 'rb') as f:
      
      ## open csv with csv.reader()
      reader = csv.reader(f, delimiter=',')
      
      ## grab fist column from each row
      sid.append([x[0] for x in reader])
  
      it = it + 1
      print("File {0} of {1} read.".format(str(it), str(len(fn_in))))
  
  ## flatten sid to single list
  sid = [item for sublist in sid for item in sublist]
  
  ## create output name (input_dir + <targetfolder>_combined.txt)
  dir_name = dir_in.split(os.sep)[-1]
  fn_out = dir_in + os.sep + dir_name + "_combined.txt"
  
  ## write out new text file
  print("Writing data to text file...\n")
  with open(fn_out, 'wb') as fo:
    
    for line in sid:
      
      if line != "Landsat Scene Identifier":
  
        fo.write(line + '\n')
  
  
  print("Data written to {0}.".format(fn_out))
  
  
###################################################################################  
if __name__ == "__main__":
  
  if len(sys.argv) != 2:
    
    print('Incorrect number of arguments. Example: \n'
          'python create_scenelist_from_metadata.py /path/to/csvfiles/')
    sys.exit(1)
    
  else:
    
    scene_from_meta(sys.argv[1])