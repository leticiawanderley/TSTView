#  -*- coding: utf-8 -*-
import model


class Console():

    def __init__(self, datainicial, datafinal, lista_matriculas, lista_questoes):
        self.lista_questoes = lista_questoes
        self.lista_matriculas = lista_matriculas

        # FIXME Alunos_set was already removing submissions that where not
        # from data inicio and data fim.. this must be done here now.
        alunos, _, self.turmas = model.create_students_questions_and_classes(datainicial, datafinal)
        self.alunos_set = alunos.values()
        self.turma_analisada = model.search_name(alunos.values(), self.turmas, lista_matriculas)

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
