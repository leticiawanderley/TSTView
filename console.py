#  -*- coding: utf-8 -*-

# import logging
import cgi
from google.appengine.api import mail
from google.appengine.api import users
import webapp2
import urllib2
from datetime import datetime, timedelta
from logica_console import Console
import model
import os
import jinja2

DEBUG = False

jinja_environment = jinja2.Environment(extensions=['jinja2.ext.i18n', 'jinja2.ext.loopcontrols'], loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


def checa_erros(datainicio, datafim, horainicio, horafim, tabela_grafico, turma):

    erros = []
    erro = False

    if datainicio:
        try:
            datetime.strptime(datainicio, "%d%m%Y")
        except ValueError:
            erros.append("Data Inicial: " + datainicio)
            erro = True
    if datafim:
        try:
            datetime.strptime(datafim, "%d%m%Y")
        except ValueError:
            erros.append("Data Final: " + datafim)
            erro = True
    if horainicio:
        try:
            hora = "%02d" % int(horainicio[0:2])
            minutos = "%02d" % int(horainicio[2:4])
            timedelta(0, (int(hora) * 3600) + (int(minutos) * 60))  # hora_inicial
        except ValueError:
            erros.append("Hora Inicial: " + horainicio)
            erro = True
    if horafim:
        try:
            hora = horafim[0:2]
            minutos = horafim[2:4]
            timedelta(0, (int(hora) * 3600) + (int(minutos) * 60))  # hora_final
        except ValueError:
            erros.append("Hora Final: " + horafim)
            erro = True
    if tabela_grafico:
        if tabela_grafico != "graph" and tabela_grafico != "table":
            erros.append(u"Visualização: " + tabela_grafico)
            erro = True
    if turma:
        # FIXME this search is wrong. Redo.
        pass
        #matriculas = model.create_matricula_email_dict()
        #nome_igual = False
        #for elemento in turma:
        #    if elemento not in matriculas.keys() and elemento not in turmas:
        #        nome_lista = elemento.split(" ")
        #        for i in range(len(nomes)):
        #            for j in range(len(nome_lista)):
        #                if nomes[i][j] == nome_lista[j]:
        #                    nome_igual = True
        #        if not nome_igual:
        #            erros.append("Turma/Matricula: " + elemento)
        #            erro = True

    return erro, erros


class WebApp(webapp2.RequestHandler):

    def cabecalho(self, console):
        cabecalho_values = {
            "print_intervalo": u"Submissões no intervalo (Das %s de %s às %s):" % (datetime.strftime(console.datainicio, "%H:%M"),
                                                                                     datetime.strftime(console.datainicio, "%d/%m/%Y"),
                                                                                     datetime.strftime(console.datafim, "%H:%M de %d/%m/%Y"))}

        jinja_env = jinja_environment.get_template("templates/cabecalho.html")
        self.response.out.write(jinja_env.render(cabecalho_values))

    def grafico(self, console):

        sumario = console.sumario_grafico()
        grafico_values = {
            "certas": sumario[0],
            "erradas": sumario[2],
            "num_nao_fizeram": sumario[4],
            "questao_sumarizada": sumario[6],
            "fizeram_certo": sumario[1],
            "fizeram_errado": sumario[3],
            "nao_fizeram": sumario[5],
            "data_report": datetime.strftime(console.datainicio, "%d%m%Y"),
            "dataf_report": datetime.strftime(console.datafim, "%d%m%Y")
        }
        grafico_env = jinja_environment.get_template(
            "templates/grafico.html")

        self.response.out.write(grafico_env.render(grafico_values))

    def ajax_replace(self, console, tabela_grafico):

        ajax_values = {
            "turma": console.lista_matriculas,
            "questoes": ",".join(console.lista_questoes),
            "datainicio": datetime.strftime(console.datainicio, "%d%m%Y"),
            "horainicio": console.horainicio,
            "datafim": datetime.strftime(console.datafim, "%d%m%Y"),
            "horafim": console.horafim,
            "tabela_grafico": tabela_grafico
        }
        ajax = jinja_environment.get_template("templates/ajax.html")

        self.response.out.write(ajax.render(ajax_values))

    def get(self):

        self.response.headers["Content-Type"] = "text/html; charset=utf-8"

        user, is_adm, email = model.info(users.get_current_user())
        datainicio = self.request.get("di", default_value="")
        datafim = self.request.get("df", default_value="")
        horainicio = self.request.get("hi", default_value="")
        horafim = self.request.get("hf", default_value="")
        tabela_grafico = self.request.get("tg", default_value="")
        turma = self.request.get("trm", default_value="")
        questoes = self.request.get("qts", default_value="")

        if user:
            self.response.out.write(self.login(
                True, datainicio, datafim, horainicio, horafim, tabela_grafico, turma, questoes))
        else:
            self.response.out.write(self.login(
                False, datainicio, datafim, horainicio, horafim, tabela_grafico, turma, questoes))

        lista_turma, lista_questoes = self.trata_parametros(turma, questoes)
        erro, erros = checa_erros(
            datainicio, datafim, horainicio, horafim, tabela_grafico, lista_turma)

        self.response.out.write(self.navegacao())
        if erro:
            self.response.out.write(self.erros(erros))
        else:
            console = Console(is_adm, email,
                              datainicio, datafim, horainicio, horafim, lista_turma, lista_questoes)
            if not console.alunos_set:  # FIXME check this later.. what to do in an access error
                self.response.out.write(self.erro_acesso())
            self.cabecalho(console)
            if tabela_grafico == "graph":
                self.grafico(console)
            else:
                self.ajax_replace(console, tabela_grafico)

        self.response.out.write(self.formularios(
            datainicio, datafim, horainicio, horafim, tabela_grafico, turma, questoes))

    def trata_parametros(self, turma, questoes):

        # FIXME This validation was invalid... turmas was always an empty set.
        #if turma:
        #    if turma in turmas:
        #        turma = turma.replace(" ", "").split(",")
        #    else:
        #        turma = turma.split(" ")
        #else:
        #    turma = []

        if questoes:
            questoes = questoes.replace(" ", "").split(",")
        else:
            questoes = []

        return turma, questoes

    def erros(self, erros):

        erro_values = {
            "erros": erros
        }

        erro = jinja_environment.get_template("templates/erro.html")

        return erro.render(erro_values)

    def erro_acesso(self):

        erro_acesso = jinja_environment.get_template(
            "templates/erro_acesso.html")

        return erro_acesso.render()

    def navegacao(self):

        navigation = jinja_environment.get_template(
            "/static/templates/navigation.html")

        return navigation.render()

    def formularios(self, datainicio, datafim, horainicio, horafim, tabela_grafico, turma, questoes):

        checkg = "false"
        checkt = "true"
        if tabela_grafico == "graph":
            checkg = "true"
            checkt = "false"

        formularios_values = {
            "datainicio": datainicio,
            "datafim": datafim,
            "horainicio": horainicio,
            "horafim": horafim,
            "checkg": checkg,
            "checkt": checkt,
            "turma": turma,
            "questoes": questoes
        }

        formularios = jinja_environment.get_template(
            "templates/formularios.html")

        return formularios.render(formularios_values)

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

        return login.render(login_values)


class RefreshData(WebApp, webapp2.RequestHandler):

    def tabela_submissoes(self, console):
        lista_submissoes_values = {
            "alunos": console.turma_analisada,
            "alunos_sessao": console.alunos_set,
            "data_report": datetime.strftime(console.datainicio, "%d%m%Y"),
            "dataf_report": datetime.strftime(console.datafim, "%d%m%Y"),
            "email": console.email,
            "admin": console.admin
        }
        lista_submissoes = jinja_environment.get_template(
            "templates/lista_submissoes.html")

        self.response.out.write(lista_submissoes.render(lista_submissoes_values))

    def tabela(self, console):
        tabela_values = {
            "lista_questoes": sorted(console.lista_questoes),
            "alunos": console.turma_analisada,
            "alunos_sessao": console.alunos_set,
            "datainicio": datetime.strftime(console.datainicio, "%d%m%Y"),
            "horainicio": console.horainicio,
            "datafim": datetime.strftime(console.datafim, "%d%m%Y"),
            "horafim": console.horafim,
            "tabela_grafico": "graph",
            "email": console.email,
            "admin": console.admin
        }
        tabela_env = jinja_environment.get_template("templates/tabela.html")
        self.response.out.write(tabela_env.render(tabela_values))

    def get(self):

        user, is_adm, email = model.info(users.get_current_user())

        self.response.headers["Content-Type"] = "text/html; charset=utf-8"
        datainicio = self.request.get("di", default_value="")
        datafim = self.request.get("df", default_value="")
        horainicio = self.request.get("hi", default_value="")
        horafim = self.request.get("hf", default_value="")
        turma = self.request.get("trm", default_value="")
        tabela_grafico = self.request.get("tg", default_value="")

        questoes = self.request.get("qts", default_value="")
        if questoes:
            questoes = questoes.replace(" ", "").split(",")
        else:
            questoes = []

        console = Console(is_adm, email,
                          datainicio, datafim, horainicio, horafim, turma, questoes)

        if console.lista_questoes:
            if tabela_grafico == "table":
                self.response.out.write(self.tabela(console))
        else:
            self.tabela_submissoes(console)


class Codigo(webapp2.RequestHandler):

    def get(self):

        matricula_emails = model.create_students_questions_and_classes()[0]

        user, is_adm, email = model.info(users.get_current_user())

        questao = self.request.get("questao", default_value="")
        submissao = self.request.get("submissao", default_value="")
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
