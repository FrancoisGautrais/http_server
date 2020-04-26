from . import utils
from .httprequest import HTTPRequest, HTTPResponse

class HttpUser:

    def __init__(self, req : HTTPRequest, res : HTTPResponse):
        self.id = utils.new_id()
        self.info = req.header("")