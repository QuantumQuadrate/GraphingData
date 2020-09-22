import multiprocessing
import time
import sys
import logging
import ConfigParser
from origin.client import origin_reciever
import zmq
import os
import json

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
            [streamID, content] = sub_sock.recv_multipart()
            data_queue.put(json.loads(content))
        except zmq.ZMQError as e:
            if e.errno != zmq.EAGAIN:
                print e
        if cmd == 'close':
            break

    sub_sock.close()
    context.term()

class HybridSubscriber(origin_reciever.Reciever):

    def __init__(self,config,logger,data_queue,loop=poller_loop):
        super(HybridSubscriber, self).__init__(config,logger)
        self.connect(self.read_sock, self.read_port)
        self.get_available_streams()
        self.cmd_queue = multiprocessing.Queue()
        sub_addr = "tcp://{}:{}".format(self.ip,self.sub_port)
        sub_list = ['0038'.decode('ascii'),'0013'.decode('ascii')]
        self.loop = multiprocessing.Process(
            target = loop,
            args=(sub_addr,sub_list,data_queue,self.cmd_queue)
        )
        self.loop.start()


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
    data_queue = multiprocessing.Queue()
    sub = HybridSubscriber(config,logging.getLogger(__name__),data_queue)
    time.sleep(9)
    while not data_queue.empty():
        print data_queue.get()
    time.sleep(10)
    while not data_queue.empty():
        print data_queue.get()
    sub.close()
