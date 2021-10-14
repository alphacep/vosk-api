# Twisted lazy computations
# (from rmo-sketchbook/cyst/cyst.py)

import mimetypes
import os

from twisted.web.static import File
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.internet import reactor

class Insist(Resource):
    isLeaf = True

    def __init__(self, cacheloc):
        self.cacheloc = cacheloc
        self.cachefile = None
        if os.path.exists(cacheloc):
            self.cachefile = File(cacheloc)
        self.reqs_waiting = []
        self.started = False
        Resource.__init__(self)

    def render_GET(self, req):
        # Check if someone else has created the file somehow
        if self.cachefile is None and os.path.exists(self.cacheloc):
            self.cachefile = File(self.cacheloc)
        # Check if someone else has *deleted* the file
        elif self.cachefile is not None and not os.path.exists(self.cacheloc):
            self.cachefile = None

        if self.cachefile is not None:
            return self.cachefile.render_GET(req)
        else:
            self.reqs_waiting.append(req)
            req.notifyFinish().addErrback(
                self._nevermind, req)
            if not self.started:
                self.started = True
                reactor.callInThread(self.desist)
            return NOT_DONE_YET

    def _nevermind(self, _err, req):
        self.reqs_waiting.remove(req)

    def desist(self):
        self.serialize_computation(self.cacheloc)
        reactor.callFromThread(self.resist)

    def _get_mime(self):
        return mimetypes.guess_type(self.cacheloc)[0]

    def resist(self):
        if not os.path.exists(self.cacheloc):
            # Error!
            print("%s does not exist - rendering fail!" % (self.cacheloc))
            for req in self.reqs_waiting:
                req.headers[b"Content-Type"] = b"text/plain"
                req.write(b"cyst error")
                req.finish()
            return

        self.cachefile = File(self.cacheloc)

        # Send content to all interested parties
        for req in self.reqs_waiting:
            self.cachefile.render(req)

    def serialize_computation(self, outpath):
        raise NotImplemented

class HelloCyst(Insist):
    def serialize_computation(self, outpath):
        import time
        time.sleep(10)
        open(outpath, "w").write("Hello, World")

if __name__=='__main__':
    import sys
    c = HelloCyst(sys.argv[1])
    site = Site(c)
    port = 7984
    reactor.listenTCP(port, site)
    print("http://localhost:%d" % (port))
    reactor.run()
