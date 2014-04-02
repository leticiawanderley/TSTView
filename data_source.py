#  -*- coding: utf-8 -*-
import urllib2
import gzip
import json
import StringIO
from google.appengine.api import memcache

DEMO = False


def _gzip_json(data):
    stream = StringIO.StringIO()
    gzipper = gzip.GzipFile(mode='wb', fileobj=stream)
    gzipper.write(json.dumps(data))
    gzipper.close()
    return stream.getvalue()


def _gunzip_json(data):
    stream = StringIO.StringIO(data)
    gzipper = gzip.GzipFile(mode='rb', fileobj=stream)
    data = gzipper.read()
    return json.loads(data)


def get_students_data(demo=DEMO):
    if not demo:
        return open("recursos/dados_alunos.txt").readlines()  # FIXME use web.

    return open("recursos/demo/dados_alunos_demo.txt").readlines()


def get_test_data(demo=DEMO):
    if not demo:
        try:
            data = memcache.get("results")
            if data is not None:
                return _gunzip_json(data)
            req = urllib2.Request(
                'https://dl.dropboxusercontent.com/u/74287933/2013.2/tst-results.dat')
                #'http://dl.dropbox.com/u/74287933/2012.2/reports/tst-results.dat')
            #if data is not None:
            #    data, size = data
            #    req.headers['Range'] = 'bytes=%s-' % (size)
            #    dados = urllib2.urlopen(req).read().strip()
            #    if dados != "":
            #        data = _gzip_json(_gunzip_json(data) + dados.split("\n"))
            #    memcache.add("results", (data, len(dados) + size))
            #    return _gunzip_json(data)
            #else:
            dados = urllib2.urlopen(req).read().strip()
            #size = len(dados)
            data = _gzip_json(dados.split("\n"))
            memcache.add("results", data, 600)

        except Exception, e:
            raise e
        return _gunzip_json(data)
    return open("recursos/demo/resultados_teste_demo.txt").readlines()
