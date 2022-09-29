# This Python file uses the following encoding: utf-8
import sys
from Corona import covdb, covidchart
import os
import schedule
import time
import common.oracle_db as oradb

def job():
   schedule.every(2).seconds.do(covdb.regional_db)
   schedule.every(2).seconds.do(covdb.domestic_db)
   schedule.every(2).seconds.do(covidchart.region_chart)
   schedule.every(2).seconds.do(covidchart.domcase_chart)
   schedule.every(2).seconds.do(covidchart.domdeath_chart)
   schedule.every(2).seconds.do(covidchart.totcase_chart)

   # schedule.every().day.at('17:22').do(covdb.regional_db)
   # schedule.every().day.at('17:22').do(covdb.domestic_db)
   # schedule.every().day.at('17:22').do(covidchart.region_chart)
   # schedule.every().day.at('17:22').do(covidchart.domcase_chart)
   # schedule.every().day.at('17:22').do(covidchart.domdeath_chart)
   # schedule.every().day.at('17:22').do(covidchart.totcase_chart)

   while True:
      schedule.run_pending()
      time.sleep(1)

if __name__ == '__main__':
   try:
      os.chdir(sys._MEIPASS)
      print(sys._MEIPASS)
   except:
      os.chdir(os.getcwd())
   oradb.oracle_init()
   job()