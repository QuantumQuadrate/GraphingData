import multiprocessing
import datetime
import time
import sys
import logging
import ConfigParser
from origin.client import origin_reciever,origin_reader
import readStream
import zmq
import os
import pandas as pd

def poller_loop(sub_addr,sub_list,data_queue,cmd_queue):
    context = zmq.Context()
    sub_sock = context.socket(zmq.SUB)
    sub_sock.setsockopt(zmq.RCVTIMEO,1000)
    sub_sock.connect(sub_addr)
    cmd = None

    for sub in sub_list:
        sub_sock.setsockopt_string(zmq.SUBSCRIBE,sub)
    while True:
        try:
            cmd = cmd_queue.get_nowait()
        except:
            pass
        try:
            [streamID,content]= sub_sock.recv_multipart()

            data_queue.put((streamID,pd.Series(content)))
        except zmq.ZMQError as e:
            if e.errno != zmq.EAGAIN:
                print e
        if cmd == 'close':
            break

    sub_sock.close()
    context.term()


class HybridSubscriber(origin_reciever.Reciever):

    def __init__(self,config,logger,data_queue,sub_list=None,loop=poller_loop):
        super(HybridSubscriber, self).__init__(config,logger)
        self.connect(self.read_sock, self.read_port)
        self.get_available_streams()
        self.cmd_queue = multiprocessing.Queue()
        sub_addr = "tcp://{}:{}".format(self.ip,self.sub_port)
        if sub_list is None:
            sub_list = ['0038'.decode('ascii'),'0013'.decode('ascii')]
        self.loop = multiprocessing.Process(
            target = loop,
            args=(sub_addr,sub_list,data_queue,self.cmd_queue)
        )
        self.loop.start()
        self.initialTime = time.time()

    def get_stream_filter(self, stream):
        """!@brief Make the appropriate stream filter to subscribe to a stream
        @param stream A string holding the stream name
        @return stream_filter A string holding the filter to subscribe to the
            resquested data stream
        """
        stream_id = str(self.known_streams[stream]['id'])
        # ascii to unicode str
        stream_id = stream_id.zfill(self.filter_len)
        stream_id = stream_id.decode('ascii')
        self.log.info(stream_id)
        return stream_id

    def close(self):
        super(HybridSubscriber,self).close()
        self.cmd_queue.put('close')





if __name__ == '__main__':
# first find ourself
    fullBinPath  = os.path.abspath(os.getcwd() + "/" + sys.argv[0])
    fullBasePath = os.path.dirname(os.path.dirname(fullBinPath))
    fullLibPath  = os.path.join(fullBasePath, "lib")
    fullCfgPath  = os.path.join(fullBasePath, "config")
    sys.path.append(fullLibPath)

    configfile = "origin-server.cfg"
    config = ConfigParser.ConfigParser()
    config.read(configfile)

    print "getting reader"
    read = readStream.readStream(logging.getLogger(__name__))
    print "getting data"
    stream = "Hybrid_Beam_Balances"
    timeValue = 60
    data = {}
    data[stream] = read.read_streams(stream,stop = time.time()-timeValue)
    read.close()
    print "got data and closed read"
    print data

    data_queue = multiprocessing.Queue()
    sub = HybridSubscriber(config,logging.getLogger(__name__),data_queue)
    time.sleep(1)
    while not data_queue.empty():
        print data_queue.get()
    time.sleep(10)
    while not data_queue.empty():
        print data_queue.get()
    sub.close()
