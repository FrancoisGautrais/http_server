from .httpserver import HTTPServer
from .httprequest import HTTPRequest, HTTPResponse
from .afdurl import testurl
from .utils import Callback
import os

class RESTServer(HTTPServer):

    def __init__(self, ip="localhost", attrs={"mode" : HTTPServer.SPAWN_THREAD}):
        HTTPServer.__init__(self, ip, attrs)
        self._handlers={}
        self._defaulthandler=None
        self.default(RESTServer._404, self)
        self.static_dirs={}

    """
        Ajoute une route statique
        :param baseUrl str Url pour acceder auc contenu
        :param dir str Dossier local contenant les fichiers
        :param authcb fct(req, res): Bool Callback pour déterminer si l'utilisateur est autorisé
        :param needauthcb fct(req, res): Bool Callback pour déterminer si la requete nécessite une autorisation
                        Par défaut à Faux
    """
    def static(self, baseUrl, dir, authcb=None, needauthcb=None):
        dir=os.path.abspath(dir)
        if dir[-1]=="/": dir=dir[:-1]
        if baseUrl[-1]=="/": baseUrl=baseUrl[:-1]
        self.static_dirs[baseUrl]=(dir, needauthcb, authcb, None)

    """
            Ajoute une route statique
            :param baseUrl str Url pour acceder auc contenu
            :param dir str Dossier local contenant les fichiers
            :param authcb fct(req, res): Bool Callback pour déterminer si l'utilisateur est autorisé
            :param needauthcb fct(req, res): Bool Callback pour déterminer si la requete nécessite une autorisation
                            Par défaut à Faux
        """

    def static_gen(self, baseUrl, dir, authcb=None, needauthcb=None, gen={}):
        dir = os.path.abspath(dir)
        if dir[-1] == "/": dir = dir[:-1]
        if baseUrl[-1] == "/": baseUrl = baseUrl[:-1]
        self.static_dirs[baseUrl] = (dir, needauthcb, authcb, gen)

    """
        Ajoute une route pour gérer une requete REST
        :param methods list ou str contenant la/les méthode(s) HTTP  concernés
        :param urls list ou str urls la/les url(s) REST concernés
                
    """
    def route(self, methods, urls, fct, obj=None, data=None):
        if not isinstance(urls, (list, tuple)): urls=[urls]
        if isinstance(methods, str): methods = [methods]
        for method in methods:
            if not (method in self._handlers):
                self._handlers[method.upper()] = {}
            for url in urls:
                self._handlers[method.upper()][url] = Callback(fct, obj, data)

    """
        Ajoute une route par défaut (en général ou pour ne méhode)
        :param fct fct handler
        :param obj L'objet pour une méthode
        :param data Données supplémentaires à fournir
        :param methods (str ou list) La ou les méthodes HTTP à gérer ou None
    """
    def default(self, fct, obj=None, data=None, methods=None):
        if methods:
            self.route(methods, None, fct, obj, data)
        else:
            self._defaulthandler = Callback(fct, obj, data)

    def _404(self, req: HTTPRequest, res: HTTPResponse):
        res.code = 404
        res.msg = "Not Found"
        res.content_type("text/plain")
        res.end(req.path + " Not found")


    """
        Permet de router la requête
    """
    def handlerequest(self, req, res):
        m = req.method
        u = req.path

        found = None
        d={}

        # 1ere étape: Voir si la requete REST est enregistrée
        if m in self._handlers:
            d = self._handlers[m]

            for url in d:
                if url:
                    args = testurl(url, req.path)
                    if args != None:
                        found = d[url]
                        req.params = args

            # si il y a une requete par défaut (par méthode)
            if found == None:
                if None in d: found = d[None]

        # si ce n'est pas une requete REST enregistrée:
        # --> On regarde dans les enregistrements static
        if found == None:
            p=req.path
            for base in self.static_dirs:
                if p.startswith(base):
                    dir, needeauth, auth, gen = self.static_dirs[base]
                    p=p[len(base):]
                    if len(p)==0: p="login.html"
                    if p[0]=="/": p=p[1:]
                    path=os.path.join(dir,p)
                    if  (not auth) or (not needeauth) or (not needeauth.call((req, res))) or auth.call((req, res)):
                        if gen==None:
                            res.serve_file( path, base+"/"+p)
                        else:
                            if not isinstance(gen, object): gen=gen(req, res)
                            res.serve_file_gen(path, gen)
                    return

        # si il y a un handler par défaut général
        if found == None and self._defaulthandler:
            found = self._defaulthandler

        if found:
            found.call(prependParams=(req, res))




