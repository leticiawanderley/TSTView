#  -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import model


class Console():

    def __init__(self, admin, email, datainicio, datafim, horainicio, horafim, lista_matriculas, lista_questoes):

        self.admin = admin
        self.email = email
        self.datainicio = datainicio
        self.datafim = datafim
        self.horainicio = horainicio
        self.horafim = horafim

        self._trata_parametros()

        self.questoes = lista_questoes
        self.lista_questoes = lista_questoes
        self.lista_matriculas = lista_matriculas
        # FIXME Alunos_set was already removing submissions that where not
        # from data inicio and data fim.. this must be done here now.
        alunos, _, self.turmas = model.create_students_questions_and_classes(self.datainicio, self.datafim)
        self.alunos_set = alunos.values()
        self.turma_analisada = model.search_name(alunos.values(), self.turmas, lista_matriculas)

    def _trata_parametros(self):

        hoje = datetime.now() - timedelta(0, 3 * 3600)
        if not self.horainicio:
            if 8 <= hoje.hour <= 17:
                horainicial = timedelta(
                    0, (hoje.hour - (hoje.hour % 2)) * 3600)
            else:
                horainicial = timedelta(0, 0)
        else:
            hora = "%02d" % int(self.horainicio[0:2])
            minutos = "%02d" % int(self.horainicio[2:4])
            horainicial = timedelta(
                0, (int(hora) * 3600) + (int(minutos) * 60))

        """ Tratamento Parametro Hora Fim """

        if not self.horafim:
            horafinal = timedelta(
                0, (hoje.hour * 3600) + (hoje.minute * 60) + hoje.second)
        else:
            hora = self.horafim[0:2]
            minutos = self.horafim[2:4]
            horafinal = timedelta(0, (int(hora) * 3600) + (int(minutos) * 60))

        """ Tratamento Parametro Data Fim """

        if not self.datafim:
            datafinal = datetime(hoje.year, hoje.month, hoje.day) + horafinal
        else:
            datafinal = datetime.strptime(self.datafim, "%d%m%Y") + horafinal

        """ Tratamento Parametro Data Inicio """

        if not self.datainicio:
            datainicial = datetime(
                hoje.year, hoje.month, hoje.day) + horainicial
        else:
            if self.horafim and not self.datafim:
                datainicial = datetime.strptime(
                    self.datainicio, "%d%m%Y") + horainicial
                datafinal = datetime.strptime(
                    self.datainicio, "%d%m%Y") + horafinal
            else:
                datainicial = datetime.strptime(
                    self.datainicio, "%d%m%Y") + horainicial

        self.datainicio = datainicial
        self.datafim = datafinal

    def sumario_grafico(self):
        # creating graphical summary of one question only
        nao_fizeram = set()
        fizeram_certo = set()
        fizeram_errado = set()
        for aluno in self.turma_analisada:
            if aluno not in self.alunos_set or self.lista_questoes[0] not in aluno.questions:
                nao_fizeram.add(aluno)
                continue
            for submission in aluno.submissions:
                if submission.question == self.lista_questoes[0]:
                    if submission.success:
                        if aluno not in fizeram_errado:
                            fizeram_certo.add(aluno)
                    else:
                        if aluno not in fizeram_certo:
                            fizeram_errado.add(aluno)

        return [len(fizeram_certo), fizeram_certo, len(fizeram_errado), fizeram_errado, len(nao_fizeram), nao_fizeram, self.lista_questoes[0]]
