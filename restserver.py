
from . import utils, cache
from .cache import Cache
from .htmltemplate.htmlgen import html_meta
from .httpserver import HTTPServer
from .httprequest import HTTPRequest, HTTPResponse
from .afdurl import testurl
from .utils import Callback, new_id
import os
import time
import datetime
from .utils import dictassign, dictget

def _default_session_schem():
    return {
        "username" : "username",
        "password" : "password"
    }
class RESTUser:
    def get_name(self): raise NotImplementedError("Not implemented")
    def check_password(self, password): raise NotImplementedError("Not implemented")
    def get_api_key(self): return None
    def get_data(self): raise NotImplementedError("Not implemented")



def get_base(url, file):
    if not url: return "."
    url=url[1:] if url[0]=="/" else url
    url=url[:-1] if url and url[-1]=="/" else url
    nurl=len(url.split("/"))
    file = os.path.dirname(file)
    file = file if file else "."
    nfile=len(file.split("/"))-1
    return os.path.join(file,"/".join([".."]*(nfile-nurl)))


class StaticDir:

    def __init__(self, dir, needauth, authcb):
        self.dir = dir
        self.needauth = needauth
        self.authcb = authcb
        self.gen = None
        self.meta = None
        self.cache = None

    def set_meta(self, x):
        self.meta = x
        return self

    def set_gen(self, x):
        self.gen = x
        return self

    def set_cache(self, x):
        self.cache = x
        return self

class RESTServer(HTTPServer):
    DEFAULT_SESSION_OPTION={
        "session_duration" : 3600*24,
        "auth_page" : "/login",
        "session_schem" : _default_session_schem(),
        "on_auth" : None,
        "users" : None,
        "url" : "/auth"
    }
    def __init__(self, ip="localhost", attrs={"mode" : HTTPServer.SPAWN_THREAD}, restoption={}):
        HTTPServer.__init__(self, ip, attrs)
        self._handlers={}
        self._defaulthandler=None
        self.default(RESTServer._404, self)
        self.static_dirs={}
        self.sessions={}
        self.cached=Cache()
        self.index=dictget(restoption, "index", "index.html")
        self.users={}
        if "auth" in restoption:
            obj=dictassign({}, restoption["auth"], RESTServer.DEFAULT_SESSION_OPTION)
            self.set_auth( obj["url"], obj["users"], obj["session_schem"], obj["auth_page"],
                           obj["session_duration"], obj["on_auth"])
        else:
            self._session_options=RESTServer.DEFAULT_SESSION_OPTION


    def get_req_session(self, req : HTTPRequest, res : HTTPResponse, isHtml=True, autorise=None, sendResp=True):
        if (not "SESSIONID" in req.cookies) or (not req.cookies["SESSIONID"] in self.sessions):
            if sendResp:
                if self._session_options["auth_page"] and isHtml:
                    res.serve302(self._session_options["auth_page"],{ "Content-Type" : "application/json"},{
                        "code": 400,
                        "message": "Unauthorised",
                        "data": "Aucune session n'est ouverte pas le client"
                    })
                else:
                    res.serv_json_unauthorized("Aucune session n'est ouverte pas le client")
            return None

        sessionid = req.cookies["SESSIONID"]
        session = self.sessions[sessionid]
        if autorise and not autorise(session.user):
            if sendResp:
                if self._auth_page and isHtml:
                    res.serve302(self._auth_page,{ "Content-Type" : "application/json"},{
                        "code": 400,
                        "message": "Unauthorised",
                        "data": "L'utilisateur '%s' n'a pas accès à cette ressource" % session.username
                    })
                else:
                    res.serv_json_unauthorized("L'utilisateur '%s' n'a pas accès à cette ressource" % session.username)
            return None
        return session

    def get_user_api(self, req : HTTPRequest, res : HTTPResponse,  autorise=None):
        return self.get_req_user(req, res, False, autorise)

    def get_user_html(self, req : HTTPRequest, res : HTTPResponse,  autorise=None):
        return self.get_req_user(req, res, True, autorise)

    def get_session_api(self, req : HTTPRequest, res : HTTPResponse,  autorise=None):
        return self.get_req_session(req, res, False, autorise)

    def get_session_html(self, req : HTTPRequest, res : HTTPResponse,  autorise=None):
        return self.get_req_session(req, res, True, autorise)

    def get_req_user(self, req : HTTPRequest, res : HTTPResponse, isHtml=True,  autorise=None, sendResp=True):
        apikey =  req.header("X-api-key")
        if not apikey:
            session = self.get_req_session(req, res, isHtml, autorise, sendResp)
            if session: return session.user
        else:
            found = False
            for username in self.users:
                user = self.users[username]
                userkey = user.get_api_key()
                if userkey and apikey == userkey:
                    username = user.get_name()
                    found = True
                    break

            if not found:
                if self._auth_page and isHtml:
                    res.serve302(self._auth_page, {"Content-Type": "application/json"}, {
                        "code": 400,
                        "message": "Unauthorised",
                        "data": "Mauvaise clé API"
                    })
                else:
                    res.serv_json_unauthorized("Mauvaise clé API")
                return None
        return None

    def set_index(self, index): self.index=index

    def set_auth(self, url, users, data=None, page=None, expires=3600*24, onAuth=None):
        dictassign(self._session_options["session_schem"], data if data else {})
        self._session_options["auth_page"]=page
        self._session_options["session_duration"]=expires
        self._session_options["on_auth"]=onAuth
        self._session_options["users"]=users
        self.users=users
        self.route("POST", url, self.__handle_auth)



    def __handle_auth(self, req : HTTPRequest, res : HTTPResponse):
        if not req.header("X-api-key"):
            body = req.body_json()
            if not self._session_options["session_schem"]["username"] in body:
                return res.serv_json_bad_request("Champ identifiant non présent")

            if not self._session_options["session_schem"]["password"] in body:
                return res.serv_json_bad_request("Champ identifiant non présent")

            username = body[self._session_options["session_schem"]["username"]]
            pwd = body[self._session_options["session_schem"]["password"]]
            if not username in self.users:
                return res.serv_json_unauthorized("Identifiant ou mot de pass incorrect")

            user = self.users[username]

            if not user.check_password(pwd):
                return res.serv_json_unauthorized("Identifiant ou mot de pass incorrect")

        else:
            apikey=req.header("X-api-key")
            found = False
            for username in self.users:
                user = self.users[username]
                userkey = user.get_api_key()
                if userkey and apikey==userkey:
                    username=user.get_name()
                    found = True
                    break

            if not found:
                return res.serv_json_unauthorized("Mauvaise clé API")

        id = new_id(32)
        t=time.time()
        t2 = self._session_options["session_duration"]+t
        dt = datetime.datetime.fromtimestamp(t2)
        sess = {
            "username" : username,
            "user" : user,
            "options" : {},
            "createion-date" : t,
            "validity-date" : t2
        }
        self.sessions[id] = sess

        res.set_cookie("SESSIONID", id, {
            "Path": "/",
            "Expires" : dt.strftime("%a, %d %b %Y %H:%M:%S GMT %Z")
        })

        if self._session_options["on_auth"]:
            self._session_options["on_auth"](req, res, sess)
        else:
            res.serv_json_ok()

    def precache(self, path, recursive=True):
        cache=self.cached
        utils.file_foreach(path, lambda path, idi: cache.cache_file(path) if not idi else None)


    """
        Ajoute une route statique
        :param baseUrl str Url pour acceder auc contenu
        :param dir str Dossier local contenant les fichiers
        :param authcb fct(req, res): Bool Callback pour déterminer si l'utilisateur est autorisé
        :param needauthcb fct(req, res): Bool Callback pour déterminer si la requete nécessite une autorisation
                        Par défaut à Faux
    """
    def static(self, baseUrl, dir, authcb=None, needauthcb=None, cached=True):
        dir=os.path.abspath(dir)
        if dir[-1]=="/": dir=dir[:-1]
        if baseUrl[-1]=="/": baseUrl=baseUrl[:-1]
        sd=StaticDir(dir, needauthcb, authcb)
        if cached: sd.set_cache(self.cached)
        self.static_dirs[baseUrl]=sd

    """
        Ajoute une route statique avec des imports statiques
        :param baseUrl str Url pour acceder auc contenu
        :param dir str Dossier local contenant les fichiers
        :param authcb fct(req, res): Bool Callback pour déterminer si l'utilisateur est autorisé
        :param needauthcb fct(req, res): Bool Callback pour déterminer si la requete nécessite une autorisation
                        Par défaut à Faux
    """
    def static_meta(self, baseUrl, dir, authcb=None, needauthcb=None, cached=True):
        dir=os.path.abspath(dir)
        if dir[-1]=="/": dir=dir[:-1]
        if baseUrl[-1]=="/": baseUrl=baseUrl[:-1]
        sd=StaticDir(dir, needauthcb, authcb).set_cache(self.cached)
        if cached: sd.set_cache(self.cached)
        self.static_dirs[baseUrl]=sd



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
        self.static_dirs[baseUrl] = StaticDir(dir, needauthcb, authcb).set_gen(gen)

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

    def ___route_file_handle(self, req: HTTPRequest, res: HTTPResponse, filename, ishtml, needAuth, authFail, autorise, cached):
        cache=self.cached if cached else None
        if needAuth:
            session = self.get_req_session(req, res, autorise=autorise, isHtml=ishtml, sendResp=not authFail)
            user = None
            if not session:
                user = self.get_req_user(req, res, autorise=autorise, isHtml=ishtml, sendResp=not authFail)
            else:
                user = session.user

            if not user:
                if authFail:
                    return authFail(req, res)
            else:
                return res.serve_file(filename, cache=cache)
        else:
            res.serve_file(filename, cache=cache)

    """
        Ajoute une route vers une génération de fichier depuis un fichier pattern
        :param methods (str, list, tuple) la ou les méthode à utiliser
        :param urls (str, list, tuple) La ou les urls à gérer
        :param filename (str) Le fichier à charger
        :param isHtml (bool) Renvoyer un réponse pour html ou pour api
        :param needAuth (bool) Une authentification est nécessaire pour avoir acces à la ressource
        :param authFail (fct(req, res) ou None) Callback a appeller en cas d'un utilisateur non identifié ou 
                    qui n'a pas les droits suffisants (None -> Réponse classique de get_req_user)
        :param autorise (fct(user) ou None) fonction qui permet de vérifier les droit de l'utilisateur
    """

    def route_file(self, methods, urls, filename, isHtml=True, needAuth=False, authFail=None, autorise=None, cached=None):
        return self.route(methods, urls,
                          lambda req, res: self.___route_file_handle(req, res, filename, isHtml, needAuth, authFail,
                                                                     autorise, cached))




    def ___route_file_handle_meta(self, req: HTTPRequest, res: HTTPResponse,
                                  filename,
                                  ishtml,
                                  needAuth,
                                  authFail,
                                  autorise,
                                  cached,
                                  base):
        cache=self.cached if cached else None
        if needAuth:
            session = self.get_req_session(req, res, autorise=autorise, isHtml=ishtml, sendResp=not authFail)
            user = None
            if not session:
                user = self.get_req_user(req, res, autorise=autorise, isHtml=ishtml, sendResp=not authFail)
            else:
                user = session.user
            if not user:
                if authFail:
                    return authFail(req, res)
            else:
                return res.serve_file_meta(base, filename, cache=cache)
        else:
            return res.serve_file_meta(base, filename, cache=cache)


    """
        Ajoute une route vers une génération de fichier meta (uniqument inclusion d'autres fichiers avec <#indeclude("")>
        :param methods (str, list, tuple) la ou les méthode à utiliser
        :param urls (str, list, tuple) La ou les urls à gérer
        :param filename (str) Le fichier à charger
        :param isHtml (bool) Renvoyer un réponse pour html ou pour api
        :param needAuth (bool) Une authentification est nécessaire pour avoir acces à la ressource
        :param authFail (fct(req, res) ou None) Callback a appeller en cas d'un utilisateur non identifié ou 
                    qui n'a pas les droits suffisants (None -> Réponse classique de get_req_user)
        :param autorise (fct(user) ou None) fonction qui permet de vérifier les droit de l'utilisateur
        :param cached (bool) 
        :param contentType (str) 
    """
    def route_file_meta(self, methods, urls, filename,
                        isHtml=True,
                        needAuth=False,
                        authFail=None,
                        autorise = None,
                        cached = True,
                        contentType="text/html"):
        if not isinstance(urls, (list, tuple)): urls=[urls]
        for url in urls:
            base=get_base(url, filename)
            if cached:
                data=html_meta(base, filename)
                self.cached.cache_data(filename, data, contentType)
            self.route(methods, url,
                          lambda req, res: self.___route_file_handle_meta(req, res, filename,
                                                                      isHtml,
                                                                      needAuth,
                                                                      authFail,
                                                                      autorise,
                                                                      cached,
                                                                      base
                                                                      ))




    def ___route_file_gen_handle(self, req : HTTPRequest, res : HTTPResponse, filename, ishtml, baseData, fct, authFail, autorise, needAuth):
        session = self.get_req_session(req, res, autorise=autorise, isHtml=ishtml, sendResp=(not authFail and needAuth))
        user = None
        baseData=dictassign({"page": req.path}, baseData)

        if not session:
            user = self.get_req_user(req, res, autorise=autorise, isHtml=ishtml, sendResp=(not authFail and needAuth) )
        else:
            user = session["user"]

        if not user and needAuth:
            if authFail:
                return authFail(req, res)
            else: return

        if fct:
            baseData=dictassign({}, baseData, fct(session, user))
            return res.serve_file_gen(filename, baseData)
        else:
            if session:
                baseData=dictassign( { "session" : session["options"]}, baseData)
                if user: baseData=dictassign(user.get_data(), baseData)
                return res.serve_file_gen(filename, baseData)
            else:
                baseData=dictassign( {"session": {}}, baseData)
                if user: baseData=dictassign(user.get_data(), baseData)
                return res.serve_file_gen(filename, baseData)

    """
        Ajoute une route vers une génération de fichier depuis un fichier pattern
        :param methods (str, list, tuple) la ou les méthode à utiliser
        :param urls (str, list, tuple) La ou les urls à gérer
        :param filename (str) Le fichier à charger
        :param baseData (dict) Le dictionnaire de base à envoyer
        :param getData (fct(session, user) ou None) La fonction qui va renvoyer le dictionnaire à envoyer à la génératin
        :param isHtml (bool) Renvoyer un réponse pour html ou pour api
        :param authFail (fct(req, res) ou None) Callback a appeller en cas d'un utilisateur non identifié ou 
                    qui n'a pas les droits suffisants (None -> Réponse classique de get_req_user)
        :param autorise (fct(user) ou None) Calback qui permet de vérifier les droits de l'utilisateur
        :param needAuth (bool) Renvoie vers la page de login si vrai et si l'utilisateur n'est pas identifé
    """
    def route_file_gen(self, methods, urls, filename, baseData={}, getData=None, isHtml=True, authFail=None, autorise = None, needAuth=True):
        self.route(methods, urls,
                  lambda req, res: self.___route_file_gen_handle(req, res, filename, isHtml, baseData, getData, authFail, autorise, needAuth))


    def ___route_auth_handle(self, req : HTTPRequest, res : HTTPResponse, callback, ishtml, authFail, autorise, needAuth):
        session = self.get_req_session(req, res, autorise=autorise, isHtml=ishtml, sendResp=not authFail)
        user = None
        if not session:
            user = self.get_req_user(req, res, autorise=autorise, isHtml=ishtml, sendResp=not authFail)
        else:
            user = session["user"]

        if not user and needAuth:
            if authFail:
                return authFail(req, res)
            else: return

        callback(req, res, session, user)



    def route_auth(self, medthods, urls, callback, ishtml=False, authFail=None, autorise=None):
        self.route(medthods, urls,
                   lambda req, res: self.___route_auth_handle(req, res, callback, ishtml, authFail, autorise, True))

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
                    sd = self.static_dirs[base]
                    gen = sd.gen
                    p=p[len(base):]
                    if len(p)==0: p=self.index
                    if p[0]=="/": p=p[1:]
                    path=os.path.join(sd.dir,p)
                    if  (not sd.authcb) \
                            or (not sd.needeauth) \
                            or (not sd.needeauth.call((req, res))) \
                            or sd.authcb.call((req, res)):
                        if sd.gen==None and sd.meta==None:
                            res.serve_file( path, base+"/"+p, cache=sd.cache)
                        elif sd.meta:
                            res.serv_file_meta(path, cache=sd.cache)
                        else:
                            if not isinstance(gen, object): gen=gen(req, res)
                            res.serve_file_gen(path, gen)
                    return

        # si il y a un handler par défaut général
        if found == None and self._defaulthandler:
            found = self._defaulthandler

        if found:
            found.call(prependParams=(req, res))




