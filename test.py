import sys 
import datetime
import time

currentDT = datetime.datetime.now()
print (str(currentDT))

time.sleep(600)

print("hello")
currentDT = datetime.datetime.now()
print (str(currentDT))

sys.exit('cause an error')
