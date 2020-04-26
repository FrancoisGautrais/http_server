from .utils import path_to_list


class RESTParams(dict):

    def __init__(self):
        dict.__init__(self)

    def str(self, name):
        x=self[name]
        if isinstance(x, (list, tuple)): return "/".join(x)
        return x

class AfdUrl:

    def __init__(self, template):
        self.template=path_to_list(template)
        self.index=0
        self.args={}

    def curr(self):
        return self.template[self.index] if self.index < len(self.template) else None

    def get_var_name(self): return self.curr()[1:]

    def peak_next_state(self):
        if self.index+1<len(self.template):
            return self.template[self.index+1]
        return None

    def next_state(self):
        self.index += 1
        if self.index < len(self.template):
            return self.curr()
        return None

    def handle_star(self, name, url, args):
        c=self.peak_next_state()



        max=-1
        if c: # /[..]/*x/somthing
            if c[0] == "#": raise Exception("Forbidden url patern '*x/#y/'")
            for i in range(len(url)):
                if url[i]==c: max=i
            args[name] = url[:max]
            self.next_state()
            return self.next(url[max:], args)
        else:  # /[..]/*x
            args[name]=url
            return args

        return None


    def next(self, url, args):
        c = self.curr()
        if c==None and len(url)==0: return args
        if c == None: return None
        if c[0] == "*": return self.handle_star(c[1:], url, args)

        if len(url)==0: return None

        curl=url.pop(0)
        if c[0] == "#":
            args[c[1:]]=curl
        elif curl!=c: return None
        self.next_state()
        return self.next(url, args)

    def parse(self, url):
        return self.next(path_to_list(url), RESTParams())

def testurl(template, url):
    return AfdUrl(template).parse(url)


test= {
    #"/d/#b/c": [ "/d/bonjour/c"],
    #"/a/#b/c": [ "/a/bonjour", "bonjour/a/c", "/a/bonjour/c", "/a/bonjour/b/"],
    "/a/*b/fin": [ "/a/bonjour", "bonjour/a/c", "/a/bonjour/c/bc/fin", "/a/bonjour/b/fin"]
}
