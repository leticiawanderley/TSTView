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

    def sumario_grafico(self, questao):
        # creating graphical summary of one question only
        nao_fizeram = []
        fizeram_certo = []
        fizeram_errado = []
        for aluno in self.turma_analisada:
            if questao not in aluno.questions:
                nao_fizeram.append(aluno)
            elif aluno.questions[questao].success:
                fizeram_certo.append(aluno)
            else:
                fizeram_errado.append(aluno)

        return fizeram_certo, fizeram_errado, nao_fizeram
