from ast import arg
import hashlib
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as msgbox
from tkinter import scrolledtext
from message_tree import *
from peerhandler import PeerHandler
def md5(x:str):
    return hashlib.md5(x.encode("utf-8")).hexdigest()
#####################################################
this_ip,this_port="10.162.8.133",5001
tracker_ip,tracker_port="10.162.8.133",5000
#####################################################
if not os.path.exists("rsa_private_key.pem") or not os.path.exists("rsa_public_key.pem"):
    generate_keypair()
with open("rsa_public_key.pem","r") as f:
    name=md5(f.read())

mt=messageTree()
mt.constructTree()
this_peer=PeerHandler(name,this_ip,this_port,on_receive_message=mt.insert)
this_peer.login((tracker_ip,tracker_port))

def 发帖():
    title=e1.get()
    description=e2.get(0.0,tk.END)
    ################################
    ret=mt.insert({
        "level":1,
        "parent":mt.getTailSiblingId(mt.root.id) if mt.root!=None else "0",
        "content":title+"\n\n"+description,
        "source":name,
        "destination":None
    })
    with open("messages/{}.json".format(ret.id),"w") as f:
        f.write(_:=ret.makepkt())
    this_peer.send(_,None)
    # level 1
    ################################
    msgbox.showinfo('信息', '发帖成功')
    e1.delete(0,tk.END)
    e2.delete(0.0,tk.END)
    tabControl.select(tab2)
    treeview_update()
viewing_id=None
def 回帖(*args):
    content=text_input.get(0.0,tk.END)
    node=mt.getNode(viewing_id)
    ###############################
    # print(content)
    ret=mt.insert({
        "level":node.level+1,
        "parent":mt.getTailChildId(node.id) if mt.root!=None else "0",
        "content":content,
        "source":name,
        "destination":None
    })
    with open("messages/{}.json".format(ret.id),"w") as f:
        f.write(_:=ret.makepkt())
    this_peer.send(_,None)
    ###############################
    msgbox.showinfo('信息', '发帖成功')
    text_input.delete(0.0,tk.END)
    treeview_update()

def addnode(x:list,f=""):
    global tree_set
    for i in x:
        if not i["id"] in tree_set:
            tree_set.add(i["id"])
            print(f," --> ",i["id"])
            tree.insert(f,tk.END,text=i["content"].replace("\n"," "),iid=i["id"],values=i["id"],open=False)
        addnode(i["children"],i["id"])
def treeview_update():
    addnode(mt.getWholeTree())
    tree.update()
root =tk.Tk()
root.title(string = "title") 
tabControl = ttk.Notebook(root)  
tab1 = tk.Frame(tabControl) 
tabControl.add(tab1, text='发帖')  
tk.Label(tab1, text="标题：").grid(row=0,column=0)
tk.Label(tab1, text="正文：").grid(row=1,column=0)
e1 = tk.Entry(tab1)
e2 = tk.Text(tab1)
e1.grid(row=0, column=1)
e2.grid(row=1, column=1)
publish=tk.Button(tab1,text="发布",command=发帖)
publish.grid(row=1, column=2)

tab2 = tk.Frame(tabControl)
tabControl.add(tab2, text='看帖')
tree = ttk.Treeview(tab2)
tree_set=set()
treeview_update()

tree.grid(row=0, column=0,ipady=80,rowspan=2)
def select_tree():
    global viewing_id
    for item in tree.selection():
        id=tree.item(item, "values")[0]
        viewing_id=id
        node=mt.getNode(id)
        view.config(state='normal')
        view.delete(0.0,tk.END)
        view.insert(tk.END,node.content+"\n"+"-"*20+"\n"+" "*10+"User: "+node.source)
        view.config(state='disabled')


tree.bind("<<TreeviewSelect>>", lambda event: select_tree())
view=scrolledtext.ScrolledText(tab2)
view.config(state='disabled')
view.grid(row=0,column=1,padx=10)

text_input=scrolledtext.ScrolledText(tab2,height=5)
text_input.grid(row=1,column=1,padx=10)
text_input.bind("<Control-Return>",回帖)
tabControl.pack(expand=1, fill="both")
tabControl.select(tab1) 
# root.mainloop()
while True:
    treeview_update()