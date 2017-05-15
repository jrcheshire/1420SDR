# 1420SDR
Python utilities for 21 cm hydrogen line observations using RTL-SDR software-defined radio
James Cheshire 2017

Requires the RTL-SDR driver, as well as Roger's pyrtlsdr wrapper and standard scientific Python packages (numpy, matplotlib).

1420_cont.py is a gui-based application that plots continuum power of the 2.4 MHz band centered at 1420.4 MHz in real time, and outputs pdf plots and csv data tables, with the first column being local time and the second being measured power in dB.

1420_pdf.py is a command line application that integrates the power spectral density for a user-specified amount of time, and outputs pdf polots and csv data tables, with the first column being frequency, the second power in dB at that frequency, and the third being the relative velocity of the 21 cm line when observed at the frequency in column 1.
