'''
plot_hist.py

Purpose: plot histogram, accept optional argument for split variable.

Inputs: a) input CSV file (csv_in)
        b) output dir + file name (fn_out)
        c) variable to be plotted (y_var)
        d) number of breaks for histogram (hist_n)
        e) split variable (generates boxplot for each category) (split_var)

Author:   Steve Foga
Contact:  steven.foga.ctr@usgs.gov
Created:  17 October 2016
Modified: 18 October 2016

'''
import sys
def do_plot(csv_in, fn_out, y_var, y_units, hist_n, split_var=None):
  
  import os
  import numpy as np
  import pandas as pd
  import matplotlib.pyplot as plt
  from matplotlib.offsetbox import AnchoredText
  
   
  ############################################################################
  ## read data
  c_in = pd.read_csv(csv_in)
  
  ## get data variable
  plot_var = c_in[y_var]
  
  ## filter out invalid entries (Excel-based nodata, etc.)
  nodata_vals = ['#VALUE!', 'NA', 'NaN', '#NULL!', '#NAME?', '#N/A', '#DIV/0',
                 '#REF!', '#NUM!', 'N/A']
  valid_var = plot_var[~plot_var.isin(nodata_vals)].astype('float64')
  
  
  ############################################################################
  ## if the variable is to be split into categories, plot a certain way
  if split_var:
    
    ## get categories
    c_var = c_in[split_var]
    
    ## remove nodata coincident with valid_var
    cat_var = c_var[~plot_var.isin(nodata_vals)]
    
    ## combine data (easier to work with in plot)
    all_var = pd.concat([valid_var, cat_var], axis=1)
    
    ## make histogram for data by split_var
    all_var.groupby(split_var).boxplot(return_type='axes')
               
    ## write plot out to PNG
    plt.savefig(fn_out + "_boxplot_combined.png",
                  bbox_inches= "tight",
                  dpi = 350)   
  
  
  ############################################################################
  ## regardless, write out histogram of valid data values (i.e., NOT split)
  ## plot histogram
  fig = plt.figure()
  ax = fig.add_subplot(111)
  
  ax.hist(valid_var, int(hist_n))
         
  ## use AnchoredText() to snap annotation to corner of graph
  anchored_text = AnchoredText("n=" + str(len(valid_var)) + "\n" +
                               "bins=" + str(hist_n) + "\n" +
                               "mean: " + str(round(np.mean(valid_var),3)) + "\n" +
                               "abs. mean diff: " + str(round(abs(np.mean(valid_var)),3)) + "\n",
                               prop=dict(size=8),
                               loc=1)
  
  ## add snapped text to axis
  ax.add_artist(anchored_text)
  ax.set_xlabel(y_units)
  ax.set_ylabel("Frequency")
               
  ## write plot out to PNG
  plt.savefig(fn_out + "_hist_alldata.png",
              bbox_inches = "tight",
              dpi = 350)
              
              
##############################################################################
if __name__ == "__main__":
  #print(str(len(sys.argv))) 
  if len(sys.argv) < 6 or len(sys.argv) > 7:
    print('One or more arguments missing/too many arguments!\n'
          'Example:\n'
          'plot_hist.py csv_file_in.csv /path/to/output/output_name\n'
          'y_variable_name histogram_breaks split_var=category\n')
    sys.exit(1)
  
  elif len(sys.argv) == 7: ## if split_var is passed in
    do_plot(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], 
            sys.argv[6])
    
  else: ## no split_var
    do_plot(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
