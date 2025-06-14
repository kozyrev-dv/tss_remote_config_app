def disableChildren(parent):
    for child in parent.winfo_children():
        wtype = child.winfo_class()
        # print(wtype)
        if wtype not in ('Frame','Labelframe','TFrame','TLabelframe', 'Canvas', 'TScrollbar'):
            child.configure(state='disable')
        else:
            disableChildren(child)

def enableChildren(parent):
    for child in parent.winfo_children():
        wtype = child.winfo_class()
        # print(wtype)
        if wtype not in ('Frame','Labelframe','TFrame','TLabelframe', 'Canvas', 'TScrollbar'):
            child.configure(state='normal')
        else:
            enableChildren(child)