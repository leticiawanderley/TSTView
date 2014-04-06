#  -*- coding: utf-8 -*-
import urllib2

from util import cached

DEMO = False


@cached(time=2400)
def get_students_data(demo=DEMO):
    if not demo:
        return open("recursos/dados_alunos.txt").readlines()  # FIXME use web.

    return open("recursos/demo/dados_alunos_demo.txt").readlines()


@cached(time=300)
def get_test_data(demo=DEMO):
    if not demo:
        try:
            req = urllib2.Request(
                'https://dl.dropboxusercontent.com/u/74287933/2013.2/tst-results.dat')
            data = urllib2.urlopen(req).read().strip().split('\n')
        except Exception, e:
            raise e
        return data
    return open("recursos/demo/resultados_teste_demo.txt").readlines()
