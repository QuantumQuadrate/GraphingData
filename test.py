import pandas as pd
import readStream as read
import logging
import time
import timeit

STOP = 60*60*24#24hrs in seconds
READ = read.readStream(logging.getLogger("__read__"))
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

stream_list = 'Hybrid_Mux'
df = READ.read_streams(stream_list,start = time.time(), stop = time.time() - STOP)
df.head()
length = len(df.index)
log.debug(length)
#now datetime and respample
df['measurement_time'] = pd.to_datetime(df['measurement_time']/float(2**32),unit="s")
df = df.resample('5S',on='measurement_time').mean()
length = len(df.index)
log.debug(length)
log.debug(df.head())
