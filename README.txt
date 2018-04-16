The MDI Market Analysis Tool implements the Signal to Noise Ratio (SNR)
and Market Divergence Index (MDI) algorithms described in "Trend
Following with Managed Futures: The Search for Crisis Alpha" (Wiley,
2014) by Alex Greyserman and Kathryn M. Kaminski.  It reads in a set of
CSV form spreadsheets containing daily historical market data (one per
market to be analyzed) with the following columns in the following order
in each spreadsheet:

  - date (MM/DD/YYY)
  - open price
  - high price
  - low price
  - close price
  - Open Interest

It produces the SNR value computed over a given period (default 97 days,
can be specified on the command line using the '-p' option) of days for
each set of market data, then computes the MDI value across the markets
for each day.  It produces two output files, one containing the entire
set of historical results, the other containing only the results for the
past single period (default 97 days, settable using the '-p' option).

The two output files are either placed in the top level of the
directory (folder) specified as an argument (or dropped when used with
Windows drag and drop) or the current working directory (folder) if
the command line arguments are non-directory filenames.  The output
files are called:

   - signal_to_noise_historical.csv
   - signal_to_noise_current.csv

The output CSV files have the following columns:

  - Date
  - For each set of data analyzed:
    + Close Price
    + Computed Signal to Noise Ratio
  - Computed MDI Value

The Signal to Noise Ration and MDI columns may contain a number
indicating a computed result or the string "Insufficient Data" if the
necessary data to complete the computation is missing.

Row by row sanity checking is performed on all input files to catch
obvious data corruption or error conditions.  If errors are found they
are placed in a CSV format 'text' file named with the name (no
extension) of the input file with '_errors.txt' appended to it.  For
example, if the input file was called "gold.csv" the error report
would be in "gold_errors.txt".  The columns in the error report file are:

  - date (MM/DD/YYY)
  - open price
  - high price
  - low price
  - close price
  - Open Interest
  - Row Number in the input file
  - Reported error reason

Only rows with errors are included in the error report.  Rows with
errors are not included in the computation of SNR or MDI.
