#! /usr/bin/python

# Copyright 2018 Eric Lund
#
# The MDI Market Analysis Tool by Eric Lund is licensed under a
# Creative Commons Attribution-ShareAlike 4.0 International License.
# Under this license you have the right to use and distribute copies
# of this work and modify them for other purposes as long as you
# preserve this notice in all copies or derivatives and as long as you
# do not restrict the terms of the original license further.
#
# The foregoing is not a legal description of the licence, for the
# full legal description, please read the actual license here:
#
#    http://creativecommons.org/licenses/by-sa/4.0/
#
# This software is provided for research purposes only. The author
# assumes no responsibility for damages resulting from its use in any
# capacity.  No warranty or claim of suitability for any purpose is
# given.

# Bring in the needed modules
import os          # provides some operating system tools
import os.path as path # Provides pathname manipulation tools
import sys         # provides system tools and data including command arguments
import getopt      # provides command line parsing tools
import datetime    # provides tools for manipulating dates
import csv         # provides tools for manipulating CSV input
import re          # provides regular expression matching tools

def error(str):
    sys.stderr.write("%s\n" % str)

class Row:
    def __init__(self, cname, d, o, h, l, c, v, oi, snr = None):
        self.column_name = cname
        self.date = datetime.datetime.strptime(d, '%m/%d/%Y')
        self.open = float(o)
        self.low = float(l)
        self.high = float(h)
        self.close = float(c)
        self.volume = v
        self.open_interest = oi
        self.diff = 0
        self.signal_to_noise = snr

    # Check the sanity of an open (o), high (h), low (l), and close (c)
    # set.  The high should be greater than or equal to the low.  The open
    # should be greater than or equal to the low and less than or equal to
    # the high and the close should be greater than or equal to the low
    # and less than or equal to the high.  If any of these is not true,
    # return an error string describing the first problem found.
    def sanity_check(self, previous = None):
        if self.high < self.low:
            return "high (%.2f) is less than low (%.2f)" % (self.high,
                                                            self.low)
        if self.open > self.high:
            return "open (%.2f) is greater than high (%.2f)" % (self.open,
                                                                self.high)
        if self.open < self.low:
            return "open (%.2f) is less than low (%.2f)" % (self.open,
                                                            self.low)
        if self.close > self.high:
            return "close (%.2f) is greater than high (%.2f)" % (self.close,
                                                                 self.high)
        if self.close < self.low:
            return "close (%.2f) is less than low (%.2f)" % (self.close,
                                                             self.low)
        if previous != None:
            if self.date == previous.date:
                return "duplicate date in input data"
            elif self.date < previous.date:
                return "descending date in input data"

        # If we got here, no problems were found, return None to indicate
        # "no error was found"
        return None

    def difference(self, previous = None):
        if previous == None:
            # Diff is initialized to 0 and there is nothing else to do
            # here, so leave it zero and return.
            return
        self.diff = float(abs(self.close - previous.close))
        return self.diff
        
            

# Function to read in a CSV file into an array.  The first element of
# the array is a string with the base name of the file (minus the .csv
# extension) in it.  The remaining elements of the array are
# Row objects containing the data found in the CSV data.
# The value returned is the array of Rows.
#
# Each row of data is sanity checked on the way in.  The following
# conditions are looked for:
#
# + Date not strictly increasing
# + High greater than low
# + Open less than low
# + Open greater than high
# + Close less than low
# + Close greater than high
#
# If any of these conditions are found, the row is omitted from the
# data set and recorded in a separate file.
def read_csv_file(name):
    # Set up an empty array to return
    ret = []

    # Strip off the '.csv' from the name for other use...
    base = path.basename(name)[:-4]

    # Set up an empty array of error rows as well...
    errors = []

    # Open the file in a way that will automatically close the file if
    # we leave unceremoniously.  This is better than opening the file
    # and assigning it to a variable.
    with open(name, 'r') as infile:
        # Construct a CSV reader object from the input file, which
        # will let us scan through the rows of data one at a time.
        data = csv.reader(infile)

        # Walk through the CSV input data, picking up all of the columns:
        #
        #    date         ('d')
        #    open         ('o')
        #    high         ('h')
        #    low          ('l')
        #    close        ('c')
        #    openInterest ('oi')
        #
        # and build the output array.
        previous_row = None
        r = 0
        d,o,h,l,c,v,oi = 7 * [None]
        try:
            for d,o,h,l,c,v,oi in data:
                # Advance 'row' to the current row number for error
                # reporting purposes
                r += 1

                row = Row(base, d, o, h, l, c, v, oi)

                # Check that the open (o), high (h), low (l), and
                # close (c) values seems to be sane, since they can be
                # compared to detect data anomalies.  Remember any
                # error returned.
                err = row.sanity_check(previous_row)
                if err != None:
                    # There was an error. Record it in the errors
                    # array for later saving
                    errors += [[d,o,h,l,c,v,oi,r,err]]
                    continue

                # Compute the difference value for the close of this
                # row to its previous row here to save work later on.
                row.difference(previous_row)

                # Remember this row as the 'previous' row for the next
                # iteration.
                previous_row = row

                # Add the newly created and validated row to the column.
                ret += [row]
        except Exception as e:
            error("error detected in file '%s' at row %d - %s" % (name, r, str(e)))
            err = "error detected in file '%s' at row %d - %s" % (name, r, str(e))
            errors += [[d,o,h,l,c,v,oi,r,err]]
    if len(errors) > 0:
        # There were errors seen, produce a .txt file (so it won't
        # show up as a .csv file) that contains the errors found).
        #
        # First, add a heading row
        error_row = ["date", "open", "high", "low", "close",
                     "volume", "open interest",
                     "row number", "error description"]
        errors = [error_row] + errors
        with open("%s_errors.txt" % name[:-4], 'w') as out:
            wr = csv.writer(out)
            wr.writerows(errors)
    return ret

# Read in either a CSV file or a directory full of CSV files and
# return an array of columns containing the data from each file read.
def read_columns(filename):
    ret = []
    if path.isdir(filename):
        # This is a directory.
        try:
            files = os.listdir(filename)
        except OSError as e:
            error("unable to read directory '%s' - %s" % str(e))
            return ret
        for f in files:
            if f[:15] == 'signal_to_noise':
                continue
            ret += read_columns(path.join(filename, f))
    elif path.isfile(filename) and filename[-4:].lower() == '.csv':
        # This is a CSV file, read in the data.  We build a list for
        # each column which contains the column and its active row
        # (which we will use later when building the output).  For
        # now, all the active rows are 0.
        ret += [[read_csv_file(filename), 0]]
    return ret

# Compute the rolling signal to noise for the current row in the given
# column of data, by looking back 'period' entries from the current
# row and computing the ratio of the sum of the absolute differences
# between each pair of sequential close values in each entry and the
# absolute difference between the first entry and the current entry.
# If the current row has less than 'period' rows preceding it, return
# 'insufficient data' for a value.  Otherwise return the signal to
# noise ratio value as a floating point value.
def rolling_snr(column, row_number, period):
    # Check whether the condition for insufficient data is met, in
    # which case don't bother processing anything, just return
    # 'insufficient data'.
    if row_number < period:
        # The current row number is too early in the column to
        # have sufficient data, bail out...
        return 'insufficient data'

    # Figure out the start and end of the range of rows for which we
    # are computing the SNR.  The array is zero based and the range
    # function produces the values 'start' to 'end' - 1.  We want to
    # add up the last 'period' difference values including the current
    # one.  So, if I am at row 10 and I have a period of 5, I want the
    # values in 6, 7, 8, 9 and 10.  To get that, I want to add 1 to
    # both ends of the range.  At the beginning, 10 - 5 would give me
    # 5, but I want 6.  At the end, range(6, 10) would give me 6, 7,
    # 8, 9 but I want 6, 7, 8, 9, 10.  Set 'start' and 'end'
    # accordingly.
    start = (row_number - period) + 1
    end = row_number + 1

    # Now go through the previous 'period' entries and compute the sum
    # of the differences between the elements.
    small_change_sum = 0.0
    for row in column[start:end]:
        small_change_sum += row.diff
    big_change = float(abs(column[row_number].close -
                   column[row_number - period].close))
    return big_change / small_change_sum

# Compute the rolling SNRs on a column and return a new column with (
# date, close, snr ) in each row.
def compute_snrs(column, period):
    for r in range(0, len(column)):
        column[r].signal_to_noise = rolling_snr(column, r, period)
    return

def first_date(element):
    # The first element of a column (c[0]) is the name, so the first
    # data element is c[1].  Return the date from the first data
    # element.
    column,active_row = element
    return column[0].date

# Compute the lowest date for the current collection of rows that are
# candidates for consumption.  This is done by going through the
# candidates and finding the lowest date.  If no date is found then
# all of the candidate columns have been exhausted, so return None.
def lowest_date(columns):
    date = None
    for column,active_row in columns:
        if active_row < len(column):
            if date == None or column[active_row].date < date:
                date = column[active_row].date
    return date

def merge_results(columns):
    # Sort the columns in the input by the first date present in each
    # column
    columns.sort(key = first_date)

    # Initialize the array to be returned
    ret = []
    
    # First row is file names for each column.  The first output
    # column is the date column, which is blank here.  This is
    # followed, for each input column, by the name of the column and
    # two blank columns.
    row = [None]
    for column,active_row in columns:
        row += [column[0].column_name, None]
    ret += [row]

    # Second row is headings for Date and each of the columns
    row = ["Date"]
    for column,active_row in columns:
        row += ["Close", "SNR"]
    row += ["MDI"]
    ret += [row]

    # Now, work through the rows by date, taking the lowest date in
    # the current set of active rows in each column, then placing data
    # in the output for all active rows that have that date.
    output = []
    date = lowest_date(columns)
    while date != None:
        row = [date.strftime('%m/%d/%Y')]
        mdi_sum = 0.0
        mdi_count = 0
        column_count = len(columns)
        for c in columns:
            column,active_row = c
            if active_row >= len(column):
                # The active row for this column is out of range, skip
                # it, there are no more data in this column.
                continue
            if column[active_row].date == date:
                # The active row in this column is for the current
                # date, put data in the output row for this column and
                # advance the active row in this column.
                row += [column[active_row].close,
                        column[active_row].signal_to_noise]
                c[1] = active_row + 1
                if type(column[active_row].signal_to_noise) == type(1.0):
                    mdi_sum += column[active_row].signal_to_noise
                    mdi_count += 1
            else:
                # The active row in this column is for a future date,
                # put empty data in the output for this column for
                # now, and do not advance the active row.  We will
                # pick it up with a later date.
                row += [None, None]
        if mdi_count == column_count:
            mdi = mdi_sum / float(mdi_count)
        else:
            mdi = "Insufficient Data"
        row += [mdi]
        ret += [row]
        date = lowest_date(columns)
    return ret

def usage(str):
    if str != None:
        error("%s\n" % str)
    error("""
usage: snr [-p | --period <rolling-period>] file [file ...]

Where:

    -p,--period

          Sets the number of samples over which the signal to
          noise function will be executed on a rolling basis to
          compute the results.

    <file>

          Is a text file in CSV format containing rows of 7 columns.
          The first column is the date of the sample in mm/dd/yyyy
          format.  The second column is the opening price, the third
          is the high price for the day, the fourth is the low price
          for the day, the fifth is the closing price for the day, the
          sixth is the volume of trades, the seventh is the opening
          interest for the day.
"""[1:])
    exit(1)

def main(argv):
    # By default, us a 97 day period for computing rolling SNRs.
    period = 97

    # Parse options and arguments...
    try:
        parsed_args = getopt.getopt(argv, "p:", "[period=]")
    except getopt.GetoptError as e:
        usage(str(e))

    # The thing returned from getopt is a pair of arrays.  The first
    # array has all of the options and their (optional) arguments
    # stored as tuples.  The second array has all of the non-option
    # arguments (should be filenames).
    opts = parsed_args[0]
    args = parsed_args[1]
    for opt,arg in opts:
        # First piece of the option is the option string to match
        if opt in ["-p", "--period"]:
            # The second piece should be a number in this case
            # indicating the number of samples to roll through when
            # computing SN ratios.
            try:
                period = int(arg)
            except ValueError as e:
                usage("invalid period value provided - %s" % str(e))

    # Figure out where to put the output files.  If there is only one
    # arguments and that argument identifies a directory (folder),
    # then the two output files will be
    # 'signal_to_noise_historical.csv' and
    # 'signal_to_noise_current.csv' in that directory.  If there is
    # more than one argument or the one argument is not a directory,
    # then the output files will be the same names in the current
    # working directory.
    output_historical = "signal_to_noise_historical.csv"
    output_current = "signal_to_noise_current.csv"
    if len(args) == 1 and path.isdir(args[0]):
        output_historical = path.join(args[0], output_historical)
        output_current =  path.join(args[0], output_current)

    # Okay, now collect the data we need.  Go through the non-option
    # arguments section of the parsed arguments.  For each argument,
    # collect the array of columns we get from that pathname and add
    # it to the list we already have.
    columns = []
    for a in args:
        try:
            columns += read_columns(a)
        except KeyboardInterrupt:
            return 1
        except OSError as e:
            error("error reading in data from '%s' - %s" % (a, str(e)))
            continue

    if len(columns) > 0:
        # Now compute the SNRs on all of the columns we read in.
        for column, active_row in columns:
            compute_snrs(column, period)

    # Now merge the results into a table with a single date column
    # followed by the close and SNR for each row in each table. The
    # columns are sorted by starting date, with the oldest starting
    # date at the left.  If there is no data for a given date, the
    # 'close' and 'snr' columns are left blank.  
    output_data = merge_results(columns)

    # Now, write out the merged results as CSV output to the
    # histroical output file.
    with open(output_historical, 'w') as out:
        wr = csv.writer(out)
        wr.writerows(output_data)

    # And write out the recent merged results as CSV output to the
    # current output file.  Pick up the first two lines (header lines)
    # and the last 'period' lines of the historical data.
    current_data = output_data[:2] + output_data[-period:]
    with open(output_current, 'w') as out:
        wr = csv.writer(out)
        wr.writerows(current_data)
    return 0

# Start Here
exit(main(sys.argv[1:]))
