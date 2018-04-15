The MDI Market Analysis Tool implements the Signal to Noise Ratio (SNR)
and Market Divergence Index (MDI) algorithms described in "Trend
Following with Managed Futures: The Search for Crisis Alpha" (Wiley,
2014) by Alex Greyserman and Kathryn M. Kaminski.  It reads in a set of
CSV form spreadsheets containing daily historical market data (one per
market to be analyzed) with the following columns in the following order
in each spreadsheet:

  + date (MM/DD/YYY)
  + open price
  + high price
  + low price
  + close price
  + Open Interest

It produces the SNR value computed over a given period (default 97 days,
can be specified on the command line using the '-p' option) of days for
each set of market data, then computes the MDI value across the markets
for each day.  It produces two output files, one containing the entire
set of historical results, the other containing only the results for the
past single period (default 97 days, settable using the '-p' option).
