import sys
from PyQt4 import QtGui, uic
import numpy
import matplotlib.pyplot as plt
import os
import scipy.signal

"""
TO RUN THE PROGRAM:
- It will likely say 'No Python interpreter configured for the project' above, to solve this:
 o Press 'Configure Python Interpreter'
 o In the window that appears, press the cogwheel to the right of the Project Interpreter box
 o Select 'Add local'
 o Press 'OK' (You should see a python.exe file selected, if this is not the case, see First time set-up instructions)
 o Press Apply and OK, wait for the program to update itself (up to a couple of minutes)
- Select 'Run' from the option at the top of the page, then press 'Run...', 'SIMS_UI' will be selected, press it
 o If you want to run the code again, and PyCharm is still open, you can now just press the green play button in top right.
"""

# Global variables initialised for use by the program
des_pk = []                         # List for desired peaks
all_names = []                      # List for peaks available in file
files = []                          # List for desired filepaths
converter_switch = False            # Switch for converting sputter time to depth
nb_norm_switch = False              # Switch to use Nb normalisation
tot_norm_switch = False             # Switch to use normalisation by total counts
SG_switch = False                   # Switch for Savitsky-Golay filtering

#plt.rcParams["font.family"] = "Times New Roman" # Can be used to change the font in graphs

class MyWindow(QtGui.QMainWindow):
    def __init__(self):
        """ Initialisation of main window"""
        super(MyWindow, self).__init__()

        # Load the UI file which contains all the graphical information on window layout etc.
        uic.loadUi(r'C:\Users\lewisg\Desktop\SIMS UI\SIMS_Designer_UI.ui', self)  # UPDATE to correct filepath

        # Set up general parameters
        self.show()
        self.setWindowIcon(QtGui.QIcon(r'C:\Users\lewisg\Desktop\SIMS UI\fermi_logo.png'))  # UPDATE
        self.setWindowTitle("SIMS Analyser")
        self.converting_k = 1.0
        self.desired_peaks = []
        self.all_data = []

        # Button connections
        self.file_browser_button.clicked.connect(self.openbrowser)
        self.peak_select_button.clicked.connect(self.open_popup)
        self.convert_button.clicked.connect(self.converter)
        self.plot_button.clicked.connect(self.plot)
        self.file_reset.clicked.connect(self.reset)
        self.plot_Nb.clicked.connect(self.nb_norm)
        self.plot_tot.clicked.connect(self.tot_norm)
        self.auto_button.clicked.connect(self.auto_name)
        self.SGswitch.clicked.connect(self.SG_filter)

        # Set hover-over tips
        self.file_browser_button.setToolTip(
            'Choose files (select again to choose multiple files from different folders)')
        self.file_reset.setToolTip('Clears all previously selected files from program')
        self.peak_select_button.setToolTip(
            'Choose the peaks that you want to plot (displays peaks in last selected file)')
        self.horizontalSlider.setToolTip(
            'Smooths by convolution of data with box containing desired number of data points (set =1 for no smoothing)')
        self.SGswitch.setToolTip(
            'For each point does a least-square fit with a polynomial over an odd-sized window centered at the point')
        self.window_length.setToolTip('Automatically set to 10% the number of data points, must be an odd integer')
        self.poly_order.setToolTip('Must be less than the window length, lower values produce more smoothing')
        self.auto_button.setToolTip('Names each file by its filename, these will appear in the graph legend')
        self.convert_button.setToolTip('Uses depth at 10 000 s to convert between time and depth (assumes linear rate)')
        ls = [self.cv1, self.cv2, self.cv3, self.cv4, self.cv5, self.cv6, self.cv7, self.cv8,
              self.cv8, self.cv99]
        for i in ls:
            i.setToolTip(
                'Conversion factor is calculated depth at 10 000 s (Roughly 300 for 1 keV and 425 for 2 keV, use IONTOF calculator)')
        ls2 = [self.file1, self.file2, self.file3, self.file4, self.file5, self.file6, self.file7, self.file8,
              self.file9, self.file99]
        for i in ls2:
            i.setToolTip(
                'Choose label to be displayed in graph legend')
        self.auto_extent.setToolTip('Auto will set graph to display all data points')
        self.extent.setToolTip(
            'If not in auto, graph will display data for the number of specified seconds and cut off later data')
        self.plot_Nb.setToolTip(
            'This will normalise the plotted data by the niobium signal (ie plots [Selected peak signal]/[Niobium signal]')
        self.plot_tot.setToolTip(
            'This will normalise the plotted data by the total signal (ie plots [Selected peak signal]/[Total signal]')
        self.plot_button.setToolTip('Plot the graph (if no graph appears, check error display below)')

    def SG_filter(self):
        """Switches Savitsky-Golay filtering on/off"""
        global SG_switch

        if SG_switch == False: # Turns it on
            global files

            # Handles errors
            if self.all_data == []:
                self.error_bar.setText('Error: Select files first to automatically set parameters')
            else:
                self.error_bar.setText(' ')

            # Controls visual changes
            SG_switch = True
            self.SGswitch.setText('Switch off')
            self.window_length.setDisabled(False)
            self.poly_order.setDisabled(False)
            self.horizontalSlider.setDisabled(True)

            # Code to calculate window length (at 10% of no. of data points)
            all_d = self.all_data
            d = all_d[0]

            wl = int(0.1 * len(d['Time']))      # Selects the closest odd integer
            if wl % 2 == 0:
                wl += 1

            self.window_length.setText(str(wl))
            self.poly_order.setText('1')

        else:
            SG_switch = False # Turns it off
            self.SGswitch.setText('Switch on')
            self.window_length.setText(' ')
            self.poly_order.setText(' ')

            self.window_length.setDisabled(True)
            self.poly_order.setDisabled(True)
            self.horizontalSlider.setDisabled(False)

    def auto_name(self):
        """ Automatically provides names from filepath """
        ls = [self.file1, self.file2, self.file3, self.file4, self.file5, self.file6, self.file7, self.file8,
              self.file9, self.file99]

        for i, file in enumerate(self.list):
            filename = os.path.basename(file).rsplit('.TXT', 1)[0]
            ls[i].setText(filename)

    def reset(self):
        """ Clears selected files """
        self.error_bar.setText(' ')

        global files, SG_switch
        files = []
        self.list = files
        self.all_data = []

        # Resets to default names
        ls = [self.file1, self.file2, self.file3, self.file4, self.file5, self.file6, self.file7, self.file8,
              self.file9, self.file99]
        default_names = ['Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5', 'Set 6', 'Set 7', 'Set 8', 'Set 9', 'Set 10']
        if len(self.list)<10:
            for i in range(10):
                if i >= len(self.list):
                    ls[i].setText(default_names[i])

        # Turn SG filter off
        SG_switch = False
        self.SGswitch.setText('Switch on')
        self.window_length.setText(' ')
        self.poly_order.setText(' ')

        self.window_length.setDisabled(True)
        self.poly_order.setDisabled(True)
        self.horizontalSlider.setDisabled(False)

    def nb_norm(self):
        """ Nb normalisation switch """
        global nb_norm_switch, tot_norm_switch

        if nb_norm_switch == False:   # Switches it on
            nb_norm_switch = True
            self.plot_Nb.setText('Nb (on)')

            tot_norm_switch = False  # Ensures only 1 normalisation
            self.plot_tot.setText('Total (off)')

        else:
            nb_norm_switch = False   # Switches it off
            self.plot_Nb.setText('Nb (off)')

    def tot_norm(self):
        """ Total normalisation switch """
        global tot_norm_switch, nb_norm_switch
        if tot_norm_switch == False:   # Switches it on
            tot_norm_switch = True
            self.plot_tot.setText('Total (on)')

            nb_norm_switch = False  # Ensures only 1 normalisation
            self.plot_Nb.setText('Nb (off)')

        else:
            tot_norm_switch = False   # Switches it off
            self.plot_tot.setText('Total (off)')

    def openbrowser(self):
        """ Opens file browser to choose desired txt files and runs data extractor"""
        self.error_bar.setText('Loading...')  # Displays loading progress in UI

        global files

        # This will open a file explorer add the filepaths selected by the user to a list. Only text files valid.
        # UPDATE to relevant filepath
        for path in QtGui.QFileDialog.getOpenFileNames(self, 'Select files',
                                                       r'C:\Users\lewisg\OneDrive\Work\Fermilab\Data',
                                                       '*.txt'):
            files.append(path)
        self.list = files
        MyWindow.data_extractor(self)

    def data_extractor(self):
        """ Takes the useful data from the SIMS txt files, returns a list of dictionaries """
        all_data = []

        for f in self.list:
            data_file = f
            data = numpy.genfromtxt(data_file, dtype=None, names=None,
                                    skip_header=2)  # Puts all data from given file into huge list

            # Reads the first line of the file
            text = list(numpy.genfromtxt(data_file, invalid_raise=False,skip_footer=(len(data)+3), comments='None', dtype=str))
            # NOTE error warning 'got x columns instead of y' may appear depending on file time, can ignore

            # If/Else uses first line of file to figure out where names are stored (ie in line 2 or 3)
            if text[2]=='Compression':
                names = list(
                    numpy.genfromtxt(data_file, invalid_raise=False, skip_header=2, skip_footer=(len(data) + 2),
                                     comments='None', dtype=str))  # Creates list of column headings

            else:
                names = list(
                    numpy.genfromtxt(data_file, invalid_raise=False, skip_header=1, skip_footer=(len(data) + 2),
                                     comments='None', dtype=str))  # Creates list of column headings

            names[0] = 'Time'

            if '#' in names:
                names.remove('#')

            # Creates dictionary in the form of {Peak name : Intensity values}
            d = {}

            # This try and except deals with some SIMS files which for whatever reason genfromtxt can't handle properly
            try:
                if len(names) == len(data[1])+1 and 'total' in names:
                    names.remove('total')
                    for i, name in enumerate(names):
                        while i<len(names):
                            if i == 0:
                              d[name] = data[:, i]
                            else:
                                d[name] = data[:, i+1]
                            i += 1

                else:
                    for i, name in enumerate(names):
                          d[name] = data[:, i]

            except IndexError:
                d = {}
                for i, name in enumerate(names):
                    ls = []
                    for x in range(len(data)):
                        ls.append(data[x][i])

                    d[name] = numpy.array(ls)

            all_data.append(d)
        names = list(d.keys())
        names.remove('Time')

        # Ensures that Nb and NbN are first peaks to choose from so that it's easier to find them
        ordered_names=[]
        for name in names:
            if name == 'Nb-':
                ordered_names = [name] + ordered_names
            elif name == 'NbN':
                ordered_names = [name] + ordered_names
            else:
                ordered_names.append(name)

        global all_names
        all_names = ordered_names

        self.all_data = all_data

        self.error_bar.setText('   ')

    def open_popup(self):
        """ Opens the popup window for choosing desired peaks """
        global files
        if files == []:
            self.error_bar.setText('Error: Please select file before choosing peaks')
        else:
            self.error_bar.setText(' ')
        self.dialogTextBrowser = PopupClass(self)
        self.dialogTextBrowser.exec_()
        self.desired_peaks = des_pk

    def smooth(self, y, box_pts):
        """ Smooths data """

        if SG_switch == False:
            # Smooths based on moving average (ie convolution with 'box-shaped' pulse)
            # Note that setting the smooth value to 1 will display raw data with no smoothing
            box = numpy.ones(box_pts)/box_pts  # Box is an array with 'box_pts' number of entries, each with value 1/box_pts
            y_smooth = numpy.convolve(y, box, mode='valid')  # Takes convolution of signal with box
                                                              #  'Valid' only returns data data with full overlap

        elif SG_switch == True:     # If selected, will used Savitsky Golay filter instead of moving average to smooth
            if float(self.window_length.text()) %2 == 0:
                self.error_bar.setText('Error: Window length must be an odd number')
            if float(self.poly_order.text()) > float(self.window_length.text()):
                self.error_bar.setText('Error: Polynomial order must be less than window length')
            y_smooth = scipy.signal.savgol_filter(y, float(self.window_length.text()), float(self.poly_order.text()))

        return y_smooth


    def plot(self):
        """ Plots the selected data """
        # Display error message
        global files
        if files == []:
            self.error_bar.setText('Error: Please select file before plotting')
        elif self.desired_peaks == []:
            self.error_bar.setText('Error: Please select desired peaks before plotting')
        else:
            self.error_bar.setText(' ')


        fig, ax = plt.subplots()    # Set up graph
        all_d = self.all_data       # Import all the data

        # Create list of user-defined file labels
        self.file_labels = [self.file1.text(), self.file2.text(), self.file3.text(),
                            self.file4.text(), self.file5.text(), self.file6.text(),
                            self.file7.text(), self.file8.text(), self.file9.text(),
                            self.file99.text()]

        # There is an if/else statement to plot differently if converted from time to depth
        if converter_switch == True:
            # Loops through plotting each file
            converting_ks= [10000/float(self.cv1.text()), 10000/float(self.cv2.text()), 10000/float(self.cv3.text()),
                            10000 /float(self.cv4.text()), 10000/float(self.cv5.text()), 10000/float(self.cv6.text()),
                            10000 /float(self.cv7.text()), 10000/float(self.cv8.text()), 10000/float(self.cv9.text()),
                            10000 /float(self.cv99.text())]

            for f in range(len(self.list)):
                d = all_d[f]

                # Loops through each desired peak
                for i, name in enumerate(self.desired_peaks):
                    y_smooth = self.smooth(d[str(name)],
                                           float(self.smooth_value.text()))  # Calls the data smoothing function

                    # Make the labels have nicer names
                    n = str(name)
                    n = n.rstrip('-')
                    n = n.replace("_2", "$_2$")
                    n = n.replace("_5", "$_5$")

                    if nb_norm_switch == True:
                        ax.semilogy(d['Time'][0:len(y_smooth)] / converting_ks[f] , y_smooth / self.smooth(d[str('Nb-')],
                                           float(self.smooth_value.text())), label=n + ' - ' + self.file_labels[f])
                    elif tot_norm_switch == True:
                        try:
                            ax.semilogy(d['Time'][0:len(y_smooth)] / converting_ks[f] , y_smooth / self.smooth(d[str('total')],
                                               float(self.smooth_value.text())), label=n + ' - ' + self.file_labels[f])
                        except:
                            self.error_bar.setText('Error: Not all files contain total data column')
                    else:
                        ax.semilogy(d['Time'][0:len(y_smooth)]/converting_ks[f], y_smooth, label=n + ' - ' + self.file_labels[f])

                    ax.set_xlabel('Depth / nm', fontsize='15')
                    ax.set_ylabel('Intensity', fontsize='15')
                    plt.legend(fancybox='true', shadow='true')

                    if self.auto_extent.isChecked() == False:
                        plt.xlim((0,(float(self.extent.text()))//converting_ks[f]))
                plt.show()

        elif converter_switch == False:
            # Loops through plotting each file
            for f in range(len(self.list)):
                d = all_d[f]

                # Loops through each desired peak
                for i, name in enumerate(self.desired_peaks):
                    y_smooth = self.smooth(d[str(name)],
                                           float(self.smooth_value.text()))  # Calls the data smoothing function

                    # Make the labels have nicer names
                    n = str(name)
                    n = n.rstrip('-')
                    n = n.replace("_2", "$_2$")
                    n = n.replace("_5", "$_5$")

                    if nb_norm_switch == True:
                        ax.semilogy(d['Time'][0:len(y_smooth)], y_smooth / self.smooth(d[str('Nb-')],
                                           float(self.smooth_value.text())), label=n + ' - ' + self.file_labels[f])

                    elif tot_norm_switch == True:
                        try:
                            ax.semilogy(d['Time'][0:len(y_smooth)], y_smooth / self.smooth(d[str('total')],
                                           float(self.smooth_value.text())), label=n + ' - ' + self.file_labels[f])
                        except:
                            self.error_bar.setText('Error: Not all files contain total data column')

                    else:
                        ax.semilogy(d['Time'][0:len(y_smooth)], y_smooth , label=n + ' - ' + self.file_labels[f])

                    ax.set_xlabel('Sputter time / s', fontsize='15')
                    ax.set_ylabel('Intensity', fontsize='15')
                    plt.legend(fancybox='true', shadow='true')

                    if self.auto_extent.isChecked() == False:
                        plt.xlim((0,(float(self.extent.text()))))
                plt.show()

    def converter(self):
        """ Function controls conversion switch """
        global converter_switch

        if converter_switch == True:
            converter_switch = False
            self.convert_button.setText('Convert')
            self.cv1.setDisabled(True)
            self.cv2.setDisabled(True)
            self.cv3.setDisabled(True)
            self.cv4.setDisabled(True)
            self.cv5.setDisabled(True)
            self.cv6.setDisabled(True)
            self.cv7.setDisabled(True)
            self.cv8.setDisabled(True)
            self.cv9.setDisabled(True)
            self.cv99.setDisabled(True)
        else:
            converter_switch = True
            self.convert_button.setText('Switch back')
            self.cv1.setDisabled(False)
            self.cv2.setDisabled(False)
            self.cv3.setDisabled(False)
            self.cv4.setDisabled(False)
            self.cv5.setDisabled(False)
            self.cv6.setDisabled(False)
            self.cv7.setDisabled(False)
            self.cv8.setDisabled(False)
            self.cv9.setDisabled(False)
            self.cv99.setDisabled(False)


class PopupClass(QtGui.QDialog):
    """ This class is for the properties of the pop-up window of peaks """

    def __init__(self, parent=None):
        """Initiates the class, contains all window parameters"""
        super(PopupClass, self).__init__(parent)
        self.dp = []
        layout = QtGui.QHBoxLayout()

        self.setLayout(layout)
        self.setWindowTitle("Select desired peaks")

        self.setGeometry(600, 300, 100, 100)

        self.okbutton = QtGui.QPushButton('OK', self)
        self.okbutton.move(400, 60)

        self.okbutton.clicked.connect(self.reset)

        global all_names

        # Define all of the checkboxes for peaks
        self.b1 = QtGui.QCheckBox('%s' % all_names[0])  # Create checkbox with name from list of names
        layout.addWidget(self.b1)   # Add checkbox to layout style
        self.okbutton.clicked.connect(lambda: self.btnstate(self.b1))   # Define action to perform when button clicked
        if len(all_names) > 1:  # If statements allow for varying numbers of peaks to be used
            self.b2 = QtGui.QCheckBox('%s' % all_names[1])
            layout.addWidget(self.b2)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b2))
        if len(all_names) > 2:
            self.b3 = QtGui.QCheckBox('%s' % all_names[2])
            layout.addWidget(self.b3)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b3))
        if len(all_names) > 3:
            self.b4 = QtGui.QCheckBox('%s' % all_names[3])
            layout.addWidget(self.b4)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b4))
        if len(all_names) > 4:
            self.b5 = QtGui.QCheckBox('%s' % all_names[4])
            layout.addWidget(self.b5)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b5))
        if len(all_names) > 5:
            self.b6 = QtGui.QCheckBox('%s' % all_names[5])
            layout.addWidget(self.b6)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b6))
        if len(all_names) > 6:
            self.b7 = QtGui.QCheckBox('%s' % all_names[6])
            layout.addWidget(self.b7)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b7))
        if len(all_names) > 7:
            self.b8 = QtGui.QCheckBox('%s' % all_names[7])
            layout.addWidget(self.b8)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b8))
        if len(all_names) > 8:
            self.b9 = QtGui.QCheckBox('%s' % all_names[8])
            layout.addWidget(self.b9)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b9))
        if len(all_names) > 9:
            self.b10 = QtGui.QCheckBox('%s' % all_names[9])
            layout.addWidget(self.b10)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b10))
        if len(all_names) > 10:
            self.b11 = QtGui.QCheckBox('%s' % all_names[10])
            layout.addWidget(self.b11)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b11))
        if len(all_names) > 11:
            self.b12 = QtGui.QCheckBox('%s' % all_names[11])
            layout.addWidget(self.b12)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b12))
        if len(all_names) > 12:
            self.b13 = QtGui.QCheckBox('%s' % all_names[12])
            layout.addWidget(self.b13)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b13))
        if len(all_names) > 13:
            self.b14 = QtGui.QCheckBox('%s' % all_names[13])
            layout.addWidget(self.b14)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b14))
        if len(all_names) > 14:
            self.b15 = QtGui.QCheckBox('%s' % all_names[14])
            layout.addWidget(self.b15)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b15))
        if len(all_names) > 15:
            self.b16 = QtGui.QCheckBox('%s' % all_names[15])
            layout.addWidget(self.b16)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b16))
        if len(all_names) > 16:
            self.b17 = QtGui.QCheckBox('%s' % all_names[16])
            layout.addWidget(self.b17)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b17))
        if len(all_names) > 17:
            self.b18 = QtGui.QCheckBox('%s' % all_names[17])
            layout.addWidget(self.b18)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b18))
        if len(all_names) > 18:
            self.b19 = QtGui.QCheckBox('%s' % all_names[18])
            layout.addWidget(self.b19)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b19))
        if len(all_names) > 19:
             self.b20 = QtGui.QCheckBox('%s' % all_names[19])
             layout.addWidget(self.b20)
             self.okbutton.clicked.connect(lambda: self.btnstate(self.b20))
        if len(all_names) > 20:
            self.b21 = QtGui.QCheckBox('%s' % all_names[20])
            layout.addWidget(self.b19)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b21))
        if len(all_names) > 21:
            self.b22 = QtGui.QCheckBox('%s' % all_names[21])
            layout.addWidget(self.b19)
            self.okbutton.clicked.connect(lambda: self.btnstate(self.b22))
        if len(all_names) > 22:
            print('Too many peaks')
            self.error_bar.setText("Error: Too many peaks in file, not all will be displayed")

        self.okbutton.clicked.connect(self.dp_value)
        self.okbutton.clicked.connect(self.close)

    def reset(self):
        """ Resets the desired peak list in case peaks change """
        self.dp = []

    def btnstate(self, b):
        """ Adds checked peaks to list """
        if b.isChecked() == True:
            self.dp.append(b.text())

    def dp_value(self):
        """ Sets the global 'desired peak list' to the one selected by the user """
        global des_pk
        des_pk = self.dp

if __name__ == '__main__':
    # Runs the program when called
    app = QtGui.QApplication(sys.argv)
    window = MyWindow()
    sys.exit(app.exec_())
