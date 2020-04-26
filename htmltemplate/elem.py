

class Elem:

    def __init__(self, tag, content=[], id=None, classes=[], attrs={}, after=None):
        self.attrs=dict(attrs)
        self.classes = list(classes) if isinstance(classes, (list, tuple)) else classes.split(" ")
        self.id=id
        self._after=after
        self.tag=tag
        self.content=list(content )if isinstance(content, (list, tuple)) else [content]

    def add_class(self, x):
        if isinstance(x, str): self.classes.append(x)
        else: self.classes+=x
        return self

    def html(self, space=""):
        out=space+"<"+self.tag
        for k in self.attrs:
            if k!="id" and k!="class":
                out+=" "+k+( ('="'+self.attrs[k]+'"') if self.attrs[k]!=None else "")
        if self.id: out+=' id="'+self.id+'"'
        if self.classes: out+=' class="'+" ".join(self.classes)+'"'
        out+=">\n"
        for obj in self.content:
            if isinstance(obj, str): out+=space+" "+obj
            elif isinstance(obj, (int, float)): out+=space+" "+str(obj)
            else: out+=obj.html(space+" ")
        out+="\n"+space+"</"+self.tag+">\n"
        if self._after: out+=self._after.html(space)
        return out

    def append(self, x): self.content.append(x)

    def after(self, x):
        curr=self
        while curr._after!=None:
            curr=curr.after
        curr._after=x
        return self

class Input:

    def __init__(self, id=None, type="text", classes=[], attrs={}, after=None):
        self.attrs = dict(attrs)
        self.type=type
        self.classes = list(classes) if isinstance(classes, (list, tuple)) else classes.split(" ")
        self.id = id
        self._after = after

    def html(self, space=""):
        out = space + '<input type="'+self.type+'"'
        for k in self.attrs:
            if k != "id" and k != "class":
                out += " " + k + (('="' + self.attrs[k] + '"') if self.attrs[k] != None else "")
        if self.id: out += ' id="' + self.id + '"'
        if self.classes: out += " ".join(self.classes)
        out += "/>\n"
        if self._after: out += self._after.html(space)
        return out

    def after(self, x):
        curr=self
        while curr._after!=None:
            curr=curr.after
        curr._after=x
        return self


def htmldiv(content=[], id=None, classes=[], attrs={}, after=None):
    return Elem("div", content, id, classes, attrs, after)

def htmlspan(content=[], id=None, classes=[], attrs={}, after=None):
    return Elem("span", content, id, classes, attrs, after)

def htmllabel(content=[], id=None, classes=[], attrs={}, after=None):
    return Elem("label", content, id, classes, attrs, after)

def htmlselect(content=[], id=None, classes=[], attrs={}, after=None):
    return Elem("select", content, id, classes, attrs, after)

def htmlselect(content=[], id=None, classes=[], attrs={}, after=None):
    return Elem("select", content, id, classes, attrs, after)

def htmloption(content=[], id=None, classes=[], attrs={}, after=None):
    return Elem("option", content, id, classes, attrs, after)

def htmli(content, id=None, classes=["material-icons"], attrs={}, after=None):
    return Elem("a", content, id, classes, attrs, after)

def htmla(href=None, content=[], id=None, classes=[], attrs={}, after=None):
    if href: attrs["href"]=href
    return Elem("a", content, id, classes, attrs, after)

def html_input( id=None, type="text", classes=[], attrs={}, after=None):
    return Input( id, type, classes, attrs, after)