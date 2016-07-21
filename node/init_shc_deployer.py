import os

import cherrypy

import init_helpers


def configurations():
    return {
        "components": {
            "kvstore": False,
            "web": False,
            "indexing": False
        }
    }


def substitution():
    return {
        "@SHCLUSTERING_PASS_4_SYMM_KEY@": os.environ.get("INIT_SHCLUSTERING_PASS_4_SYMM_KEY", "shclustering-changeme")
    }


def after_start():
    auto_bootstrap = splunk.util.normalizeBoolean(os.environ.get("INIT_AUTO_BOOTSTRAP_SHC", "false"))
    if auto_bootstrap:
        autobootstrap_number = int(os.environ.get("INIT_AUTO_BOOTSTRAP_SHC_NUMBER", "3"))
        print "Waiting for %n members to be up before bootstrapping." % autobootstrap_number
        cherrypy.quickstart(SHCHandler(autobootstrap_number), "/")


class SHCBootstrapperHandler(object):
    exposed = True

    def __init__(self, autobootstrap_number):
        self.autobootstrap_number = autobootstrap_number
        self.members = []

    @cherrypy.expose
    def POST(self, member_uri):
        self.members.append(member_uri)
        print "SHC Members: " + ", ".join(members)
        if len(self.members) == self.autobootstrap_number:
            cherrypy.engine.exit()
            return self.members
        return []
        