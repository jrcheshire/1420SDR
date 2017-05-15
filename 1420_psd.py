# James Cheshire
# Last modified 5/11/17
# frequency dropoffs: (approx.) index 416 for redshift, 1631 for blueshift

from pylab import *
from rtlsdr import *
import datetime, time, csv, sys, numpy as np, matplotlib.pyplot as plt, getopt

def main(argv):

    if(not len(argv)):
        sys.exit("Usage:\n1420_psd.py -i <integration time(s)>")
    try:
        opts, args = getopt.getopt(argv, "hi:",["integrate="])
    except getopt.GetoptError:
        print('Usage:\n1420_psd.py -i <integration time (s)>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print('Usage:\n1420_psd.py -i <integration time (s)>')
            sys.exit()
        elif opt in ("-i", "--integrate"):
            if arg.isdigit():
                int_time = int(arg)
                if(int_time <= 0):
                    sys.exit("Integration time must be a positive integer number of seconds")
            else:
                sys.exit("Error: argument must be an integer number of seconds")


    # initialize SDR

    try:
        sdr = RtlSdr()
    except:
        sys.exit('Error: RTL-SDR not found')

    freqcorr = 55
        
    sdr.sample_rate = 2.4e6
    sdr.center_freq = 1420.405751786e6
    sdr.gain = 50
    sdr.set_freq_correction(freqcorr)

    numsamples = 2**11
    passes = int(int_time * sdr.rs / numsamples)
    

    # collect data

    power = []
    frequency = []

    print('Warning: expect execution to take 4-5x your integration time')
    print('Collecting Data...')
    for i in range(passes):
        samples = sdr.read_samples(numsamples)

        ps = np.abs(np.fft.fft(samples))**2

        frq = np.fft.fftfreq(samples.size)
        idx = np.argsort(frq)
        if i == 0:
            frequency = sdr.fc + sdr.rs * frq[idx]

        ps[0] = np.mean(ps)

        n = len(samples)
        power.append(ps[idx]/n)

    print('Averaging samples...')
    avgpower = []
    for i in range(numsamples):
        avg_i = 0
        for j in range(passes):
            avg_i += power[j][i]
        avgpower.append(avg_i/passes)

    rvel = (299792458*((1420.405751786e6 - frequency)/1420.405751786e6))/1000    

    print('Writing output files...')
    # write plot

    fig, ax = plt.subplots()
    ax.plot(rvel, 10*np.log10(avgpower), 'b-')
    ax.tick_params(labelsize=6)
    ax.get_xaxis().get_major_formatter().set_useOffset(False)
    ax.set_xlabel('Relative Velocity (km/s)')
    ax.set_ylabel('Measured Power (dB)')
    fig.savefig('psd_' + str(datetime.datetime.now()) + '.pdf')

    # write csv

    with open('psd_' + str(datetime.datetime.now()) + '.csv', 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in range(numsamples):
            writer.writerow([frequency[i], 10*np.log10(avgpower[i]), rvel[i]])
            
    plt.plot(rvel, 10*np.log10(avgpower))
    plt.xlabel('Relative Velocity (km/s)')
    plt.ylabel('Measured Power (dB)')
    plt.show()

if __name__ == "__main__":
    main(sys.argv[1:])
