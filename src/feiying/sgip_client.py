#! /usr/bin/env python
# coding: gbk

"""
SGIP Message Send
"""

from datetime import datetime
import eventlet
from eventlet.green import socket
from sgip import *
from binascii import *

class SMSClient(object):

    def __init__(self, host, port, node_id, username, pwd, sp_number):
        self._host = host
        self._port = port
        self._node_id = node_id
        self._username = username
        self._pwd = pwd
        self._seq_id = 0
        self._sp_number = sp_number 

    def _init_sgip_connection(self):
        self.__csock = socket.socket()
        ip = socket.gethostbyname(self._host)
        self.__csock.connect((ip, self._port))
        print '%s connected' % self._host

    def _close_sgip_connection(self):
        if self.__csock != None:
            self.__csock.close()
        print 'connection to %s closed' % self._host

    def gen_seq_number(self):
        seq_num1 = int(self._node_id)
        today = datetime.today()
        seq_num2 = (((today.month * 100 + today.day) * 100 + today.hour) * 100 + today.minute) * 100 + today.second
        self._seq_id += 1
        seq_num3 = self._seq_id
        return [seq_num1, seq_num2, seq_num3]

    def send_data(self, data):
        fd = self.__csock.makefile('w')
        fd.write(data)
        fd.flush()
        fd.close()

    def recv_data(self, size):
        fd = self.__csock.makefile('r')
        data = fd.read(size)
        print 'recv raw data: ', hexlify(data) 
        while len(data) < size:
            nleft = size - len(data)
            t_data = fd.read(nleft)
            #print 'data: ', hexlify(data) 
            data = data + t_data
        fd.close()
        return data

    def _bind(self):
        print 'do bind'
        # send bind msg
        bindMsg = SGIPBind(1, self._username, self._pwd)
        header = SGIPHeader(SGIPHeader.size() + bindMsg.size(), SGIPBind.ID, self.gen_seq_number())
        bindMsg.header = header
        raw_data = bindMsg.pack()
        self.send_data(raw_data)
        # recv bind resp msg
        resp_header_data = self.recv_data(SGIPHeader.size())
        print 'header raw data: ', hexlify(resp_header_data) 
        
        respHeader = SGIPHeader()
        respHeader.unpack(resp_header_data)
        print 'resp command id: {0}'.format(respHeader.CommandID)
        resp_body_data = self.recv_data(SGIPBindResp.size())
        bindRespMsg = SGIPBindResp()
        bindRespMsg.unpackBody(resp_body_data)
        if respHeader.CommandID == SGIPBindResp.ID and bindRespMsg.Result == 0:
            return True
        else:
            return False
    
    def _unbind(self):
        print 'do unbind'
        unbindMsg = SGIPUnbind()
        header = SGIPHeader(SGIPHeader.size() + unbindMsg.size(), SGIPUnbind.ID)
        unbindMsg.header = header
        raw_data = unbindMsg.pack()
        self.send_data(raw_data)

    def _submit(self, userNumber, message):
        print 'do submit'
        # send submit msg
        submitMsg = SGIPSubmit(sp_number = self._sp_number, user_number = userNumber, corp_id = self._node_id, msg_len = len(message), msg_content = message)
        header = SGIPHeader(SGIPHeader.size() + submitMsg.mySize(), SGIPSubmit.ID)
        submitMsg.header = header
        raw_data = submitMsg.pack()
        self.send_data(raw_data)
        # recv submit msg
        resp_header_data = self.recv_data(SGIPHeader.size())
        resp_body_data = self.recv_data(SGIPSubmitResp.size())
        submitRespMsg = SGIPSubmitResp()
        submitRespMsg.unpackBody(resp_body_data)
        respheader = SGIPHeader()
        respheader.unpack(resp_header_data)
        if respheader.CommandID == SGIPSubmitResp.ID and submitRespMsg.Result == 0:
            print 'sms submitted ok'

    def send_sms(self, user_number, message):
        try:
            self._init_sgip_connection()
            bindRet =self._bind() 
            if bindRet:
                # submit msg
                self._submit(user_number, message)
            else:
                print 'bind failed'
            self._unbind()
        except socket.error as (errno, strerror):
            print "socket error({0}): {1}".format(errno, strerror)
        finally:
            self._close_sgip_connection()
   

## for test
if __name__ == "__main__":
    client = SMSClient(host = '220.195.192.85', port = 8801, node_id = '22870', username = 'fy', pwd = 'f75y', sp_number = '1065583398')
    client.send_sms('18655165434', '你好China')

