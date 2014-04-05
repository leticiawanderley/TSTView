#  -*- coding: utf-8 -*-

# import logging
from google.appengine.api import mail
from google.appengine.api import users
import webapp2
from datetime import datetime, timedelta
from logica_console import Console
import model
import os
import jinja2
import util

DEBUG = False

jinja_environment = jinja2.Environment(extensions=['jinja2.ext.i18n', 'jinja2.ext.loopcontrols'], loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class Fields(dict):

    def __new_setitem__(self, value):
        raise Exception("frozen dict")

    def __init__(self, request):
        self['datainicio'] = request.get("di", default_value="")
        self['datafim'] = request.get("df", default_value="")
        self['horainicio'] = request.get("hi", default_value="")
        self['horafim'] = request.get("hf", default_value="")
        self['tabela_grafico'] = request.get("tg", default_value="")
        self['turma'] = request.get("trm", default_value="")
        self['questoes'] = request.get("qts", default_value="")
        self.__setitem__ = self.__new_setitem__


def trata_parametros(datainicio, horainicio, datafim, horafim, questoes):

    hoje = datetime.now() - timedelta(0, 3 * 3600)
    if not horainicio:
        if 8 <= hoje.hour <= 17:
            horainicial = timedelta(0, (hoje.hour - (hoje.hour % 2)) * 3600)
        else:
            horainicial = timedelta(0, 0)
    else:
        hora = horainicio[0:2]
        minutos = horainicio[2:4]
        horainicial = timedelta(0, (int(hora) * 3600) + (int(minutos) * 60))

    """ Tratamento Parametro Hora Fim """
    if not horafim:
        horafinal = timedelta(0, (hoje.hour * 3600) + (hoje.minute * 60) + hoje.second)
    else:
        hora = horafim[0:2]
        minutos = horafim[2:4]
        horafinal = timedelta(0, (int(hora) * 3600) + (int(minutos) * 60))

    """ Tratamento Parametro Data Fim """
    if not datafim:
        datafinal = datetime(hoje.year, hoje.month, hoje.day) + horafinal
    else:
        datafinal = datetime.strptime(datafim, "%d%m%Y") + horafinal

    """ Tratamento Parametro Data Inicio """
    if not datainicio:
        datainicial = datetime(hoje.year, hoje.month, hoje.day) + horainicial
    else:
        if horafim and not datafim:
            datainicial = datetime.strptime(datainicio, "%d%m%Y") + horainicial
            datafinal = datetime.strptime(datainicio, "%d%m%Y") + horafinal
        else:
            datainicial = datetime.strptime(datainicio, "%d%m%Y") + horainicial

    if questoes:
        questoes = questoes.replace(" ", "").split(",")
    else:
        questoes = []

    return datainicial, datafinal, questoes


class WebApp(util.AppRequestHandler):

    def grafico(self, console, datainicial, datafinal):

        sumario = console.sumario_grafico()
        grafico_values = {
            "certas": sumario[0],
            "erradas": sumario[2],
            "num_nao_fizeram": sumario[4],
            "questao_sumarizada": sumario[6],
            "fizeram_certo": sumario[1],
            "fizeram_errado": sumario[3],
            "nao_fizeram": sumario[5],
            "data_report": datetime.strftime(datainicial, "%d%m%Y"),
            "dataf_report": datetime.strftime(datafinal, "%d%m%Y")
        }
        grafico_env = jinja_environment.get_template(
            "templates/grafico.html")

        self.response.out.write(grafico_env.render(grafico_values))

    def get(self):

        self.response.headers["Content-Type"] = "text/html; charset=utf-8"

        user, is_adm, email = model.info(users.get_current_user())
        fields = Fields(self.request)

        self.login(user is not None, fields['datainicio'], fields['datafim'], fields['horainicio'],
                   fields['horafim'], fields['tabela_grafico'], fields['turma'], fields['questoes'])

        datainicial, datafinal, lista_questoes = trata_parametros(fields['datainicio'], fields['horainicio'],
                                                                  fields['datafim'], fields['horafim'],
                                                                  fields['questoes'])

        console = Console(datainicial, datafinal, fields['turma'], lista_questoes)

        # cabecalho
        self.render("templates/cabecalho.html",
                    {"print_intervalo": u"Submissões no intervalo (Das %s de %s às %s):" % (datetime.strftime(datainicial, "%H:%M"),
                                                                                              datetime.strftime(datainicial, "%d/%m/%Y"),
                                                                                              datetime.strftime(datafinal, "%H:%M de %d/%m/%Y"))})
        # main
        if fields['tabela_grafico'] == "graph":
            self.grafico(console, datainicial, datafinal)
        else:
            # This will create a RefreshData.get call:
            self.render("templates/ajax.html", fields)

        # forms
        formularios_values = dict(fields)
        formularios_values["checkg"] = fields['tabela_grafico'] and "true" or "false"
        formularios_values["checkt"] = fields['tabela_grafico'] and "false" or "true"

        self.render("templates/formularios.html", formularios_values)

    def login(self, loged, datainicio, datafim, horainicio, horafim, tabela_grafico, turma, questoes):
        url = str(("/?trm=%s&di=%s&hi=%s&df=%s&hf=%s&tg=%s&qts=%s") %
                  (turma, datainicio, horainicio, datafim, horafim, tabela_grafico, questoes))

        if loged:
            log = '\"%s\"' % users.create_logout_url(url)
            loger = "Logout"
        else:
            log = '\"%s\"' % users.create_login_url(url)
            loger = "Login"

        login_values = {
            "log": log,
            "loger": loger
        }
        login = jinja_environment.get_template("templates/login.html")
        self.response.out.write(login.render(login_values))

        navigation = jinja_environment.get_template('static/templates/navigation.html')
        self.response.out.write(navigation.render())


class RefreshData(WebApp, util.AppRequestHandler):

    def get(self):
        user, is_adm, email = model.info(users.get_current_user())
        self.response.headers["Content-Type"] = "text/html; charset=utf-8"
        fields = Fields(self.request)

        datainicial, datafinal, lista_questoes = trata_parametros(fields['datainicio'], fields['horainicio'],
                                                                  fields['datafim'], fields['horafim'],
                                                                  fields['questoes'])

        console = Console(datainicial, datafinal, fields['turma'], lista_questoes)

        if console.lista_questoes:
            if fields['tabela_grafico'] == "table":
                values = dict(fields)
                values.update({
                    "lista_questoes": sorted(console.lista_questoes),
                    "alunos": console.turma_analisada,
                    "alunos_sessao": console.alunos_set,
                    "tabela_grafico": "graph",
                    "email": email,
                    "admin": is_adm
                })
                self.render("templates/tabela.html", values)
        else:
            values = {
                "alunos": console.turma_analisada,
                "alunos_sessao": console.alunos_set,
                "data_report": datetime.strftime(datainicial, "%d%m%Y"),
                "dataf_report": datetime.strftime(datafinal, "%d%m%Y"),
                "email": email,
                "admin": is_adm
            }
            self.render("templates/lista_submissoes.html", values)


class Codigo(webapp2.RequestHandler):

    def get(self):

        matricula_emails = model.create_students_questions_and_classes()[0]

        user, is_adm, email = model.info(users.get_current_user())

        #questao = self.request.get("questao", default_value="")
        #submissao = self.request.get("submissao", default_value="")
        matricula = self.request.get("matricula", default_value="")

        # Service is down and we are missing k field password (it is a secret)
        if is_adm or email == matricula_emails[matricula]:
            pass
            #self.response.out.write(cgi.escape((urllib2.urlopen(
            #    ("http://download-webshell.appspot.com/download?view=true&questao=%s&submissao=%s&matricula=%s&k=") % (questao, submissao, matricula))).read()))


class Email(webapp2.RequestHandler):

    def post(self):

        user = users.get_current_user()

        send = user.email()
        receiver = self.request.get("receiver")
        subj = self.request.get("subject")
        body = self.request.get("body")

        message = mail.EmailMessage(sender=send,
                                    subject=subj)
        message.to = receiver
        message.body = body

        message.send()
        self.redirect("/")

app = webapp2.WSGIApplication(
    [("/", WebApp), ("/refreshdata", RefreshData), ("/codigos", Codigo), ("/email", Email)], debug=True)
