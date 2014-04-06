#  -*- coding: utf-8 -*-
import webapp2
import jinja2
import os
from datetime import datetime
from google.appengine.api import users
from logica_report import Report_Logic
import model

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

DEBUG = False

TURMAS_DEFAULT = {'TT1': [1, 1], 'TT2': [2, 1], 'TT3': [3, 1], 'TP1': [
    1, 2], 'TP2': [2, 2], 'TP3': [3, 2], 'TP4': [4, 2], 'TP5': [5, 2]}


class Fields(dict):

    def __new_setitem__(self, value):
        raise Exception("frozen dict")

    def __init__(self, request):
        self['matriculas'] = request.get("matriculas", default_value='')
        self['data'] = request.get("data", default_value='')
        self['df'] = request.get("df", default_value='')
        self['dia'] = request.get("dia", default_value='')
        self['semana'] = request.get("semana", default_value='')
        self['questoes'] = request.get("questoes", default_value='')
        self.__setitem__ = self.__new_setitem__


class Report(webapp2.RequestHandler):

    def get(self):

        report = Report_Logic()
        fields = Fields(self.request)

        # Render title
        titulo_values = {}
        titulo = jinja_environment.get_template('templates/titulo.html')
        self.response.out.write(titulo.render(titulo_values))

        user, is_admin, email = model.info(users.get_current_user())

        # There is no user
        if user is None:
            self.login(fields, False)
            self.not_logged()
            return

        # User is logged.. let's do it!
        self.login(fields, True)

        try:
            # FIXME Refactor validation.
            if fields['data'] != '':
                data = datetime.strptime(fields['data'], "%d%m%Y").date()
            else:
                data = None

            if fields['df'] != '':
                df = datetime.strptime(fields['df'], "%d%m%Y").date()
            else:
                df = None
        except ValueError:
            self.response.out.write(
                u"""<p class="helvetica" style="text-align:center; font-size:30px; font-weight:bold; color:red">Parâmetro(s) de data inválido(s)""")
            self.inicial_page(fields, report, data, df)
            return

        self.response.headers['Content-Type'] = 'text/html ; charset=utf-8'

        if fields['questoes'] != '':
            questoes = [str(questao).strip() for questao in fields['questoes'].split(',')]
        else:
            questoes = []

        turma = []  # students to be analysed

        if is_admin:
            for matricula in [matricula.strip() for matricula in fields['matriculas'].split(',')]:
                if matricula in TURMAS_DEFAULT:
                    turma.extend(report.classes[matricula].alunos)
                elif matricula in report.students:
                    turma.append(report.students[matricula])
        else:
            for student in report.students.values():
                if student.email == email:
                    turma = [student]
                    break

        # It's an admin:
        if is_admin:
            # Empty matriculas field:
            if not fields['matriculas']:
                self.inicial_page(fields, report, data, df)
                return

            # name searched is not one of the classes or students
            # matriculas...
            if not turma:
                self.alunos_pesquisados(report.search_name(fields['matriculas']), fields)
                return

            # more than one student. First we create a summary...
            if len(turma) > 1:
                self.imprime_sumarizacao(fields, report, turma, data, df)

            # then we show stats for each student
            for aluno in turma:
                geral, aula, naoaula, results = self.imprime_header(fields, report, turma, aluno, data, df, questoes)
                if len(questoes) > 0:
                    self.filtro_questoes(report, questoes, geral)
                if len(turma) > 1:
                    self.alunos_da_turma(fields, report, turma, aluno, geral)
                else:
                    # TODO check this. FIXME
                    self.resultados_grafico(fields, report, geral, aula, naoaula, aluno, data, df, questoes, results)
                self.form_aluno(fields, aluno)
                return

        # It's a normal user:

        # But it's empty... (we don't know this user)
        if not turma:
            self.not_logged()
            return

        matricula, aluno = turma[0].matricula, turma[0]
        geral, aula, naoaula, results = self.imprime_header(fields, report, turma, aluno, data, df, questoes)
        self.resultados_grafico(fields, report, geral, aula, naoaula, aluno, data, df, questoes, results)
        self.form_aluno(fields, aluno)

    # logged checks if it is logged in a google account (doesn't test for
    # authorization in our app)
    def login(self, fields, logged):

        url = ("/report?matriculas=%s&data=%s&df=%s&questoes=%s") % \
            (fields['matriculas'], fields['data'], fields['df'], fields['questoes'])

        if logged:
            log = '\"%s\"' % users.create_logout_url(url)
            logger = "Logout"
        else:
            log = '\"%s\"' % users.create_login_url(url)
            logger = "Login"

        login_values = {"log": log, "loger": logger}
        login = jinja_environment.get_template("templates/login.html")
        self.response.out.write(login.render(login_values))

        navigation = jinja_environment.get_template('static/templates/navigation.html')
        self.response.out.write(navigation.render())

    def inicial_page(self, fields, report, data, df):
        matriculas = report.students

        values = dict(fields)
        values['mat'] = fields['matriculas']
        values['matriculas'] = matriculas
        values['count'] = len(matriculas) / 2

        inicial_page = jinja_environment.get_template(
            'templates/inicial_page.html')
        self.response.out.write(inicial_page.render(values))

    def alunos_pesquisados(self, matriculas, fields):
        values = dict(fields)
        values['matriculas'] = matriculas
        values['count'] = len(matriculas) / 2

        pesquisa = jinja_environment.get_template(
            'templates/pesquisa.html')
        self.response.out.write(pesquisa.render(values))

    def imprime_sumarizacao(self, fields, report, turma, data, df):

        dic = {}

        for aluno in turma:
            dic[aluno] = float(report.submission_report([aluno], data, df, fields['semana'])[0])

        dados = report.summarization(dic)
        dados_sumarizados_values = {'dados': dados}
        dados_sumarizados = jinja_environment.get_template(
            'templates/dados_sumarizados.html')
        self.response.out.write(
            dados_sumarizados.render(dados_sumarizados_values))

    def imprime_header(self, fields, report, turma, aluno, data, df, questoes):

        resolver = ""
        certas = ""
        erradas = ""
        geral, aula, naoaula, results = None, None, None, None

        if len(turma) == 1:  # one student...
            geral, aula, naoaula = report.results_day(
                turma, data, df, questoes, aluno.tp)[0:4]
            cabecalho = ["Aluno: " + aluno.name + " - " + aluno.matricula, u"Turma teórica: " + aluno.tt, u"Turma prática: " + aluno.tp]
            results = report.submissions_results(turma, data, df, questoes)

            for q in sorted(results[1]):
                resolver += (3 - len(str(q))) * '0' + str(q) + " "
            for questao in sorted(results[2].keys()):
                if results[2][questao]:
                    certas += (3 - len(str(questao))) * \
                        '0' + str(questao) + " "
                else:
                    erradas += (3 - len(str(questao))) * \
                        '0' + str(questao) + " "

            top_aluno, dic_turma = report.top_submited(aluno)[0:2]
            if len(dic_turma["done"]) > 5:
                dic_turma["done"] = dic_turma["done"][0:5]
            if len(dic_turma["not_done"]) > 5:
                dic_turma["not_done"] = dic_turma["not_done"][0:5]
            if len(dic_turma["merge"]) > 5:
                dic_turma["merge"] = dic_turma["merge"][0:5]
        else:
            geral = report.results_day(
                turma, data, df, questoes, aluno.tp)[0]
            cabecalho = [fields['matriculas']]

        if fields['semana'] == '1':
            med = u"submissões por semana"
        else:
            med = u"submissões por dia"

        relatorio = report.submission_report(
            turma, data, df, fields['semana'])

        media = u'Média: ' + str(relatorio[0]) + ' ' + med + '\n'

        if len(relatorio[1]) > 0:
            intervalo = 'Intervalo: ' + \
                str(relatorio[1][0]) + ' - ' + str(relatorio[1][1])
        else:
            media, intervalo = '', ""

        header_values = {
            'tamanho': '100%',
            'cabecalho': cabecalho,
            'media': media,
            'intervalo': intervalo,
            'porfazer': resolver,
            'ehturma': len(turma) > 1,
            'q_certas': certas,
            'q_erradas': erradas,
        }
        if len(turma) == 1:
            header_values["top_aluno"] = self.top_sub(top_aluno)
            header_values["done"] = self.top_sub(dic_turma["done"])
            header_values["not_done"] = self.top_sub(dic_turma["not_done"])
            header_values["merge"] = self.top_sub(dic_turma["merge"])
        header = jinja_environment.get_template('templates/header.html')
        self.response.out.write(header.render(header_values))

        return geral, aula, naoaula, results

    def alunos_da_turma(self, fields, report, turma, aluno, geral):
        if fields['semana']:
            lista_grafico = report.coordinates(
                report.results_week(self.geral), 'week', 'Semana ')
        else:
            lista_grafico = report.coordinates(geral, 'day', 'Dia ')

        alunos_turma_values = dict(fields)

        alunos_turma_values['turma'] = turma
        alunos_turma_values['nomes'] = report.students
        alunos_turma_values['tamanho'] = '100%'
        alunos_turma_values['matricula_aluno'] = aluno.matricula
        alunos_turma_values['coordenadas'] = lista_grafico

        alunos_turma = jinja_environment.get_template(
            'templates/alunos_turma.html')

        self.response.out.write(alunos_turma.render(alunos_turma_values))

    def form_aluno(self, fields, aluno):
        form_aluno_values = {
            'aluno': aluno.matricula,
            'data_inicial': fields['data'],
            'data_final': fields['df'],
            'questoes': fields['questoes'],
        }
        form_aluno = jinja_environment.get_template(
            'templates/form_aluno.html')
        self.response.out.write(form_aluno.render(form_aluno_values))

    def filtro_questoes(self, report, questoes, geral):
        questoes_parametros = ""
        for questao in questoes:
            questoes_parametros += questao + ", "
        right_wrong = report.right_wrong_results(geral)
        certas = u'Submissões certas: ' + str(right_wrong['c']) + '\n'
        erradas = u'Submissões erradas: ' + \
            str(right_wrong['e']) + '\n' + '\n'
        questoes_values = {
            'tamanho': '100%',
            'questoes': questoes_parametros[:-2],
            'certas': certas,
            'erradas': erradas,
        }
        questoes = jinja_environment.get_template(
            'templates/questoes.html')
        self.response.out.write(questoes.render(questoes_values))

    def resultados_grafico(self, fields, report, geral, aula, naoaula, aluno, data, df, questoes, results):
        tp_alunos = report.classes["TP" + str(aluno.tp)].alunos
        turma_geral, turma_aula, turma_naoaula = report.results_day(tp_alunos, data, df, questoes, "TP" + str(aluno.tp))

        if fields['semana'] == "1":
            turma_geral = report.coordinates(
                report.results_week(turma_geral), "week", "Semana ")
            turma_aula = report.coordinates(
                report.results_week(turma_aula), "week", "Semana ")
            turma_naoaula = report.coordinates(
                report.results_week(turma_naoaula), "week", "Semana ")
            aluno_geral = report.coordinates(
                report.results_week(geral), "week", "Semana ")
            aluno_aula = report.coordinates(
                report.results_week(aula), "week", "Semana ")
            aluno_naoaula = report.coordinates(
                report.results_week(naoaula), "week", "Semana ")
        else:
            turma_geral = report.coordinates(turma_geral, "day", "Dia ")
            turma_aula = report.coordinates(turma_aula, "day", "Dia ")
            turma_naoaula = report.coordinates(
                turma_naoaula, "day", "Dia ")
            aluno_geral = report.coordinates(geral, "day", "Dia ")
            aluno_aula = report.coordinates(aula, "day", "Dia ")
            aluno_naoaula = report.coordinates(
                naoaula, "day", "Dia ")

        resultados_grafico_values = {
            'tamanho': '100%',
            'resultados': results,
            'matricula_aluno': aluno.matricula,
            'tp': aluno.tp,
        }

        resultados_grafico_values['grafico_geral'] = report.merge_coordinates(
            aluno_geral, turma_geral, len(tp_alunos))
        resultados_grafico_values['grafico_aula'] = report.merge_coordinates(
            aluno_aula, turma_aula, len(tp_alunos))
        resultados_grafico_values['grafico_naoaula'] = report.merge_coordinates(
            aluno_naoaula, turma_naoaula, len(tp_alunos))
        resultados_grafico_values[
            'iden'] = 'grafico' + str(aluno.matricula)
        resultados_grafico_values['div'] = str(aluno.matricula) + 'grafico'

        resultados_grafico = jinja_environment.get_template(
            'templates/resultados_grafico.html')
        self.response.out.write(
            resultados_grafico.render(resultados_grafico_values))

    def erro(self):
        erro_values = {
        }
        erro = jinja_environment.get_template('templates/erro.html')
        self.response.out.write(erro.render(erro_values))

    def top_sub(self, lista):
        string = ""
        for elem in lista:
            string += " " + elem + " "
        return string

    def not_logged(self):
        not_values = {}
        no_log = jinja_environment.get_template(
            'templates/not_logged.html')
        self.response.out.write(no_log.render(not_values))

app = webapp2.WSGIApplication([('/report', Report)],
                              debug=True)
