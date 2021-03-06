import socket,threading,time,queue,json,os,sys
##################################################################
def port_avaliable(port:int):
    """判断端口是否可用"""
    if port<1024 or 65535<port:return False
    if 'win32'==sys.platform: cmd='netstat -aon|findstr ":%s "'%port
    elif 'linux'==sys.platform: cmd='netstat -aon|grep ":%s "'%port
    else: raise NotImplementedError('Unsupported system type %s'%sys.platform)
    with os.popen(cmd, 'r') as f:
        if ''!=f.read():return False
        else:return True
##################################################################
def makepkt(msg:str,s_name:str,t_name:str):
    return json.dumps({
        "s_name":s_name,
        "t_name":t_name,
        "time":time.time(),
        "content":msg
    })
##################################################################
def listen(port:int,recv_buffer:queue.Queue):
    server = socket.socket()
    server.bind((socket.gethostbyname(socket.gethostname()),port))
    server.listen(4)
    serObj,address=server.accept()
    while True:
        re_data = serObj.recv(1024).decode('utf-8')
        if re_data=="QUIT":break
        recv_buffer.put(re_data)
        serObj.send("ok".encode('utf-8'))
    serObj.close()
    server.close()
###################################################################
def send(peer:tuple,sender_buffer:queue.Queue):
    client = socket.socket()
    client.connect(peer)
    while True:
        if sender_buffer.empty():
            time.sleep(0.05)
            continue
        send_data=sender_buffer.get()
        client.send(send_data.encode('utf-8'))
        if send_data == 'QUIT':break
        print,("reply: ",client.recv(1024).decode('utf-8'))
    client.close()
###################################################################
class PeerHandler:
    def __init__(self,name:str):
        self.name=name
        """主机标识"""
        self.peers={}
        """{(ip,port):(recv_buffer,sender_buffer)}"""
        self.storage=set()
        """见过的消息的hash值"""
        self.msg=queue.Queue()
        """待发送信息"""

    def ip(self):
        """返回自身ip字符串"""
        return socket.gethostbyname(socket.gethostname())

    def addpeer(self,port:int,peer:list):
        """添加 peer 
        参数 peer 的格式：[ip,port]
        """
        self.peers[peer]=(queue.Queue(),queue.Queue()) # (recv_buffer,sender_buffer)
        t_listen=threading.Thread(target=listen,args=(port,self.peers[peer][0]))
        t_listen.setDaemon(True)
        t_listen.start()
        t_send=threading.Thread(target=send,args=(peer,self.peers[peer][1]))
        t_send.setDaemon(True)
        t_send.start()
        return self.peers[peer]

    def send(self,msg:str,t_name:str):
        """对 t_name 发送 msg"""
        self.msg.put(makepkt(msg,self.name,t_name))

    def me_event(self,pkt:str):
        """收到发给自己或广播的消息时触发"""
        print(self.name+" received:"+pkt+"\n\n",end='')
        data=json.loads(pkt)
        if data["content"]=="Hello guys!":
            self.send("Hi, {}".format(data["s_name"]),data["s_name"])

    def run(self):
        """消息接收及转发等"""
        while True:
            for p in self.peers:
                if self.peers[p][0].empty():continue
                _=self.peers[p][0].get()
                if hash(_) in self.storage:continue
                self.storage.add(hash(_))
                __=json.loads(_)
                s_name,t_name=__["s_name"],__["t_name"]
                if t_name==self.name or (t_name==None and s_name!=self.name):self.me_event(_)
                if t_name!=self.name:self.msg.put(_)
            if self.msg.empty():
                time.sleep(0.05)
                continue
            while not self.msg.empty():
                tmp=self.msg.get()
                for p in self.peers:
                    self.peers[p][1].put(tmp)