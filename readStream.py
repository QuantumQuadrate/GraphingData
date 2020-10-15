import time
import pandas as pd
import logging
import zmq
import json


import ConfigParser

class readStream():
    def __init__(self,logger,configFile = 'origin-server.cfg',debug = True):
        self.logger = logger
        if debug:
            self.logger.basicConfig(level = logging.DEBUG)
        else:
            self.logger.basicConfig(level = logging.WARNING)

        self.configfile = configFile
        config = ConfigParser.ConfigParser()
        config.read(self.configfile)
        host = config.get('Server','ip')
        port = config.getint('Server','read_port')

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

        try:
            self.socket.connect("tcp://%s:%s" % (host,port))
        except:
            self.logger.debug("Error on socket connect, clsoing object")
            try:
                self.close()
            except:
                self.logger.debug("closing debig failed, no big deal tho i think")



    def read_streams(self,stream,start=None,stop=None):
        data = None
        self.logger.debug("sending raw read request for stream `{}`....".format(stream))
        request_obj = { 'stream': stream, 'raw': True,'start' : start,'stop' : stop } 
        try:
            self.socket.send(json.dumps(request_obj))
            response = self.socket.recv()
            data = json.loads(response)
        except:
            self.logger.debug("Error on read object")    
        self.logger.debug(data[0])
        df =  pd.DataFrame(data[1])
        self.logger.debug("The response is\n {}".format(df.head()))
        #check data[0] to see if what was sent back is okay??? i think 
        #ill look more into it
        return df

    def close(self):
        self.socket.close()
        self.context.term()

if __name__ == "__main__":
    logging.basicConfig(level = logging.DEBUG) 
    read = readStream(logging.getLogger(__name__))
    read.read_streams("Hybrid_Mux",start = time.time(),stop=time.time()-60)
    read.close()
