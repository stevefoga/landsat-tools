'''
download_files.py

Purpose:  script to pull files from HTTP webpage, maintain file structure.


Example usage:
  
  python download_files.py service://domain/path/to/files/ 
                           /path/to/local/output 


Caveats:

  a) Only goes one directory strcuture deep. Perhaps need to add depth option.


Author:   Steve Foga
Created:  26 October 2016
Modified: 26 October 2016


Revision history:
  26 OCT 2016:  Original creation

'''
##############################################################################
import sys

def dl_files(url, dir_out):
  
  import os
  import requests
  from bs4 import BeautifulSoup

  ############################################################################
  ## define functions

  ## use this function to find dirs 
  def get_files(url):
  
    soup = BeautifulSoup(requests.get(url).text, "lxml")
  
    hrefs = []
  
    for a in soup.find_all('a'):
      hrefs.append(a['href'])
    
    return(hrefs)

  
  ## use this function to download data to your local machine  
  def download_file(url, dir_out):
    
    r = requests.get(url, stream=True)
    
    print("Writing {0} to {1}...\n".format(str(url), str(dir_out)))
    
    with open(dir_out, 'wb') as f:
        
      for chunk in r.iter_content(chunk_size=1024): 
            
        if chunk: # filter out keep-alive new chunks
                
          f.write(chunk)
    
    
  ############################################################################
  ## script
        
  ## get all directories on target webpage        
  dirs = get_files(url)

  ## go into every directory (skip first entry) and grab all the files
  for i in dirs[1:]:
    
    ## create output directory on your system
    dir_out_fn = dir_out + os.sep + i.split('/')[0] + os.sep
    
    ## create output directory (if it doesn't already exist)
    if not os.path.exists(dir_out_fn):
      os.mkdir(dir_out_fn)
      
    ## create path to directory
    urls = url + '/' + i
    
    ## get all the files in "urls" directory
    fns = get_files(urls)
    
    ## for each file in the directory...
    for j in fns[1:]:
      
      ## create target download url
      dl_url = url + '/' + i + j
      
      ## create target output file
      dir_out_file = dir_out_fn + os.sep + j
      
      ## call download_file function to get files
      download_file(dl_url, dir_out_file)


##############################################################################
if __name__ == "__main__":
  
  if len(sys.argv) != 3:
    
    print("Incorrect number of inputs. Required: source_url, target_dir")
    sys.exit(1)

  else:
    
    dl_files(sys.argv[1], sys.argv[2])
