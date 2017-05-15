# James Cheshire
# Last updated 5/15/17

from PyQt4 import QtCore, QtGui
from ui.contui import Ui_MainWindow
from PyQt4.QtCore import *
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from pylab import *
from rtlsdr import *
from time import sleep
import datetime, csv, serial, sys, getopt, scipy as S, numpy as np, matplotlib.pyplot as plt

# initialize output arrays as global variables

times = []
powers = []

# determine whether the SDR is reading

running = True

class sdrWorker(QThread):
    global times
    global powers
    global running
    
    def __init__(self):
        QThread.__init__(self)

    def __del__(self):
        self.wait()

    @QtCore.pyqtSlot()
    def run(self):
        while(running):
            #self.wait(200)
            self.read()

    def read(self):

        # begin reading samples from SDR

        samples = astroSDR.sdr.read_samples(256*1024)
        
        n = len(samples)
        frq = np.fft.fftfreq(n)
        idx = np.argsort(frq)
        freq = astroSDR.sdr.fc + astroSDR.sdr.rs * frq[idx]

        Y = S.fft(samples)/n

        power = abs(Y)**2
        power = power[idx]

        # remove DC spike

        power[np.argmax(power)] = np.mean(power)

        # get peak frequency data
        
        peak_freq = freq[np.argmax(power)]
        powersum = np.sum(power)

        # append values to output arrays
        
        times.append(datetime.datetime.now())
        powers.append(10*np.log10(powersum))

        # signal to update matplotlibwidget in gui

        self.emit(SIGNAL('updatePlot()'))
        self.emit(SIGNAL('updateVals()'))

class astroSDR(QtGui.QMainWindow, Ui_MainWindow):

    global powers
    global times

    # set SDR parameters
    
    try:
        sdr = RtlSdr()
    except:
        sys.exit('Error: RTL-SDR not found')
        
    sdr.sample_rate = 2.4e6
    sdr.center_freq = 1420.405751786e6
    sdr.gain = 50
    sdr.set_freq_correction(55)
    
    def __init__(self):
        
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('1420.4 MHz Hydrogen Line Continuum Power')

        self.threadInstance = QThread()
        self.mySDRWorker = sdrWorker()

        self.connect(self.mySDRWorker, SIGNAL('updatePlot()'), self.updatePlot)
        self.connect(self.mySDRWorker, SIGNAL('updateVals()'), self.updateVals)

        self.timeIntervalMS = 100
        self.time = 0
        self.matplotlibwidget.draw()
        
        self.startButton.clicked.connect(self.captureSDR)
        self.CSVButton.clicked.connect(self.writeToCSV)
        self.PDFButton.clicked.connect(self.writePlot)
        self.clearButton.clicked.connect(self.clearData)
        self.stopButton.setEnabled(False)
        self.CSVButton.setEnabled(False)
        self.PDFButton.setEnabled(False)
        self.clearButton.setEnabled(False)
        self.fcLabel.setText('Center Frequency: ' + str(self.sdr.fc/1e6) + ' MHz')
        self.rsLabel.setText('Sample Rate: ' + str(self.sdr.rs/1e6) + ' MHz')
        self.offsetBox.setValue(self.sdr.get_freq_correction())

    def captureSDR(self):
        global running

        running = True

        if(self.sdr.get_freq_correction() != self.offsetBox.value()):
            self.sdr.set_freq_correction(self.offsetBox.value())
        self.mySDRWorker.daemon = True
        QtCore.QMetaObject.invokeMethod(self.mySDRWorker, 'run', Qt.QueuedConnection,)
        
        self.stopButton.setEnabled(True)
        self.stopButton.clicked.connect(self.stop)
        self.startButton.setEnabled(False)
        self.CSVButton.setEnabled(False)
        self.PDFButton.setEnabled(False)
        
        self.mySDRWorker.moveToThread(self.threadInstance)
        self.threadInstance.start()

    def updateVals(self):
        self.powerLabel.setText('Measured Power: ' + str(powers[len(powers)-1]) + ' dB')
        
    def updatePlot(self):
        
        self.matplotlibwidget.axes.plot(times, powers, 'r-')
        self.matplotlibwidget.axes.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
        self.matplotlibwidget.axes.tick_params(labelsize=6)
        self.matplotlibwidget.axes.get_yaxis().get_major_formatter().set_useOffset(False)
        self.matplotlibwidget.axes.set_xlabel('Local Time')
        self.matplotlibwidget.axes.set_ylabel('Continuum Power (dB)')
            
        self.matplotlibwidget.draw()
                
    def stop(self):
        global running
        running = False
        self.threadInstance.wait(1)
        self.threadInstance.quit()
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.CSVButton.setEnabled(True)
        self.PDFButton.setEnabled(True)
        self.clearButton.setEnabled(True)

    def cleanup(self):
        global running
        running = False
        self.threadInstance.wait(100)
        self.threadInstance.quit()
        
    def clearData(self):
        
        del times[:]
        del powers[:]

        self.clearButton.setEnabled(False)
        self.CSVButton.setEnabled(False)
        self.PDFButton.setEnabled(False)
        self.updatePlot()
        
    def writeToCSV(self):

        with open('mapper_output_' + str(datetime.datetime.now()) + '.csv', 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            for i in range(len(powers)):
                writer.writerow([times[i], powers[i]])

    def writePlot(self):

        fig, ax = plt.subplots()
        ax.plot(times, powers, 'r-')
        ax.tick_params(labelsize=6)
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M:%S'))
        ax.get_yaxis().get_major_formatter().set_useOffset(False)
        ax.set_xlabel('Local Time')
        ax.set_ylabel('Continuum Power (dB)')
        fig.savefig('cont_plot_' + str(datetime.datetime.now()) + '.pdf')

    def closeEvent(self, event):
        global running

        running = False
        self.threadInstance.wait(100)
        self.threadInstance.quit()
    
        
if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    # setup stylesheet

    form = astroSDR()
    form.show()
    ret = app.exec_()
    sys.exit(ret)
