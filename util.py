import os
import functools
import gzip
import pickle
import StringIO

import webapp2
import jinja2
from google.appengine.api import memcache

jinja_environment = jinja2.Environment(extensions=['jinja2.ext.i18n', 'jinja2.ext.loopcontrols'], loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class AppRequestHandler(webapp2.RequestHandler):

    def render(self, page, values):
        jinja_env = jinja_environment.get_template(page)
        self.response.out.write(jinja_env.render(values))


def _gzip_pickle(data):
    stream = StringIO.StringIO()
    gzipper = gzip.GzipFile(mode='wb', fileobj=stream)
    p = pickle.Pickler(gzipper)
    p.dump(data)
    gzipper.close()
    return stream.getvalue()


def _gunzip_pickle(data):
    stream = StringIO.StringIO(data)
    gzipper = gzip.GzipFile(mode='rb', fileobj=stream)
    p = pickle.Unpickler(gzipper)
    data = p.load()
    return data


def cached(time=1200):
    """
    Source: https://gist.github.com/abahgat/1395810
    Decorator that caches the result of a method for the specified time in seconds.

    Use it as:

        @cached(time=1200)
        def functionToCache(arguments):
            ...
    """
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            key = '%s%s%s' % (function.__name__, str(args), str(kwargs))
            value = memcache.get(key)
            if not value:
                value = function(*args, **kwargs)
                memcache.set(key, _gzip_pickle(value), time=time)
            else:
                value = _gunzip_pickle(value)
            return value
        return wrapper
    return decorator
