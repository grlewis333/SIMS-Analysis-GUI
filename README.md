# SIMS-Analysis-GUI
Graphical user interface developed during internship at Fermilab to analyse SIMS depth profile data
<p align="center">
<img src="https://github.com/grlewis333/SIMS-Analysis-GUI/blob/master/UI%20screenshot.png?raw=true">
</p>

First time set-up:
- Download and install a python client, PyCharm was the one used to create this program
- Download and configure the additional imported modules, these are: NumPy, Matplotlib.Pyplot, OS and PyQt4. 
  PyCharm has a built-in module manager to help do this.
- Pycharm requires you to set the location of your python interpreter, this means setting the file where you have python and the extra modules installed.
  It is possible to set this up manually, but I found the easiest way was to install canopy (another python IDE and use its module manager to install PyQt,
  then in PyCharm, to select the python interpeter, click the cogwheel and then 'Add local' and select the 'python.exe' file saved amongst in your Canopy folder.
  Note that the Canopy folder may be hidden in an invisible AppData folder in your user folder which you must type for it to appear as a location.
- In the first class (MyWindow) you can see two file-paths which locate the SIMS_Designer_UI.ui and fermi_logo.png files, make sure these filepaths are updated to
  wherever you have saved the files. You may also update the filepath used in 'openbrowser' which will make it quicker to find your data.

Running the program:
- Load the SIMS_UI.py file in PyCharm
- It will likely say 'No Python interpreter configured for the project' to solve this:
	o Press 'Configure Python Interpreter'
	o In the window that appears, press the cogwheel to the right of the Project Interpreter box
	o Select 'Add local'
	o Press 'OK' (You should see a python.exe file selected, if this is not the case, see First time set-up instructions)
	o Press Apply and OK, wait for the program to update itself (up to a couple of minutes)
- Select 'Run' from the option at the top of the page, then press 'Run...', 'SIMS_UI' will be selected, press it
	o If you want to run the code again, and PyCharm is still open, you can now just press the green play button in top right.

Using the program:
- First, select the files you wish to plot:
	- You may choose multiple files by holding Ctrl
	- To choose files in different folders, select files from one folder, press Open, then click 'Select...' again to choose more
	- If you want a new set of files, make sure to press 'Reset' to clear the list of selected filepaths
	- If you have selected a lot of large files, they can take some time to load. A 'Loading...' indicator will appear in the window
- Next, select the peaks which you want to plot 
	- These peaks are loaded based on the files which you choose so you must load the file first
- At this point, you can press 'Plot' at the bottom right, but there are several optional settings to change:
	- Select extent of smoothing: This is set to 1 as default (no smoothing), but increasing the value will effectively plot each point averaged with 'x' closest points
	                              The program does this by convolving the raw data with a box function (see code for details)
	- Savitsky-Golay filter: This is a more sophisticated smoothing function which acts as a low pass filter. The main idea behind this approach is to make
     				 for each point a least-square fit with a polynomial of high order over an odd-sized window centered at the point.
				 The program will automatically choose a window-length of 10% the number of data points in your sample, and polynomial order 1.
				 Note that the window length must be an odd number, and the polynomial order must be less than the window length (lower = more smoothing).
	- Set name for each data set: By default these are named Set 1, Set 2 etc. Changing the text will change the labels in the legend when you plot your graph
				      Using the 'Auto name' button will automatically set the labels to the name of the file.
	- Convert sputtering time to depth: By default, this option is not selected, meaning that your graph will be 'Intensity' vs 'Sputtering time', selecting this
	                                    will automatically convert the x axis from Sputtering time to Depth. This calculation is done based on the calculated depth after 10 000s which can be 
	                                    easily calculated using prepackaged IONTOF software.
					    It initially assumes a depth of 300 nm (which is average for 1 keV), this can be changed individually for each file, to enable visualisation of data
					    run with different settings (eg 1 keV vs 2 keV)
	  				    CAUTION: This function assumes uniform sputtering rate, which is not a particularly great method.
	- Plot extent: The default option sets this to automatically plot the full range of data. 
	               If however you want the x axis to cut-off at a different value, then uncheck
	               the auto tickbox and set the sputtering time that you want the plot to stop at.
	- Normalisation: This will normalise all data by either the niobium or total signal of each file. Press again to turn off.
- Note that if you use the program wrong, an error message should appear to tell you how to fix it and there are also hover-over tips which summarise this information.

Editing the program:
- Source code can be directly edited using your python client, PyCharm is recommended for this.
- The GUI interface was created using Qt Creator community edition, so if you want to change the function of buttons/add new ones etc. then I would recommend downloading this
  and loading the .ui file into it. This provides a user-friendly interface for editing the design without having to code anything.

Help:
- Google can help resolve most coding issues, stackexchange and the Python/matplotlib/PyQt user manuals contain a wealth of information
- Contact George Lewis at grlewis333@hotmail.co.uk and I will do my best to assist!
