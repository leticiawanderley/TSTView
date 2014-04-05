import os

import webapp2
import jinja2

jinja_environment = jinja2.Environment(extensions=['jinja2.ext.i18n', 'jinja2.ext.loopcontrols'], loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class AppRequestHandler(webapp2.RequestHandler):

    def render(self, page, values):
        jinja_env = jinja_environment.get_template(page)
        self.response.out.write(jinja_env.render(values))
