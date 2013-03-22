#  -*- coding: utf-8 -*- 
import webapp2
import urllib2
import math
from datetime import datetime, timedelta
import jinja2
import os
from logica_report import *

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

DEBUG = False

turmas_default = {'TT1':[1,1], 'TT2':[2,1], 'TT3':[3,1], 'TP1':[1,2], 'TP2':[2,2], 'TP3':[3,2], 'TP4':[4,2], 'TP5':[5,2]}

class Report(webapp2.RequestHandler):
	def get(self):
		acesso = True
		if not DEBUG:
			try:
				self.resultados = get_data()
			except:
				self.resultados = open('recursos/resultados_teste.txt')
				acesso = False
		else:
			self.resultados = open('recursos/resultados_teste.txt')

		self.matriculas = self.request.get("matriculas",default_value = '')
		self.data = self.request.get("data",default_value = '')
		self.df = self.request.get("df",default_value = '')
		self.dia = self.request.get("dia",default_value = '')
		self.semana = self.request.get("semana",default_value = '')
		self.questoes = self.request.get("questoes", default_value = '')
		self.lista_de_resultados = abre_resultado(self.resultados)
		self.nome_alunos = cria_dict_alunos()
		self.filtro = 'geral'
		self.safe = self.questoes
		if self.data != '':
			self.data = datetime.strptime(self.data, "%d%m%Y").date()
		if self.df != '':
			self.df = datetime.strptime(self.df, "%d%m%Y").date()
		self.response.headers['Content-Type'] = 'text/html ; charset=utf-8'
		
		navigation = jinja_environment.get_template('static/templates/navigation.html')
		self.response.out.write(navigation.render())
		if not self.matriculas:
			self.inicial_page()
		else:
			titulo_values = {}
			titulo = jinja_environment.get_template('reporttemplates/titulo.html')
			self.response.out.write(titulo.render(titulo_values))
			
			if self.questoes:
				self.questoes = self.questoes.split(',')
				for i in range(len(self.questoes)):
					self.questoes[i] = self.questoes[i].strip(' ')
					
			if len(self.matriculas.split(',')) > 1 or self.matriculas.upper() in turmas_default.keys():
				self.imprime_sumarizacao()	
					
			for matricula_aluno in self.matriculas.split(','):
				
				self.matricula_aluno = matricula_aluno.strip(' ')
				self.imprime_header()
				if len(self.questoes) > 0:
					self.filtro_questoes()			
				self.grafico()						
				if self.eh_turma:
					self.alunos_da_turma()
				else:
					self.resultados_grafico()
				self.form_aluno()
					
	def inicial_page(self):
		matriculas = matriculas_last_results(self.lista_de_resultados, self.data, self.df, self.nome_alunos, self.questoes)
		inicial_page_values = {
			'data' : self.data,
			'df' : self.df,
			'dia' : self.dia,
			'semana' : self.semana,
			'matriculas' : matriculas,
			'count' : len(matriculas)/2,
			'questoes' : self.questoes,
		}
		if self.data:
			inicial_page_values['data'] = self.data.strftime("%d%m%Y")
		if self.df:
			inicial_page_values['df'] = self.df.strftime("%d%m%Y")
		inicial_page = jinja_environment.get_template('reporttemplates/inicial_page.html')
		self.response.out.write(inicial_page.render(inicial_page_values))
	
	def imprime_sumarizacao(self):
		dic = {}
		for aluno in self.matriculas.split(','):
			aluno = aluno.strip(' ').upper()
			turma = []
			if aluno in turmas_default.keys():
				for matricula in self.nome_alunos.keys():
					if self.nome_alunos[matricula][turmas_default[aluno][1]] == str(turmas_default[aluno][0]):
						turma.append(matricula)
			else:
				turma = [aluno]
			for student in turma:
				student_list = [student]
				dic[student] = float(relatorio_sub(self.lista_de_resultados, student_list, self.data, self.df, self.semana)[0])
		
		dados = sumarizacao(dic)
		dados_sumarizados_values = {
		'dados' : dados,				
		}
		dados_sumarizados = jinja_environment.get_template('reporttemplates/dados_sumarizados.html')
		self.response.out.write(dados_sumarizados.render(dados_sumarizados_values))
	
	def imprime_header(self):
		self.matricula_aluno = self.matricula_aluno.upper()
		if self.matricula_aluno in turmas_default.keys():
			self.turma = []
			self.t = 0
			for matricula in self.nome_alunos.keys():
				if self.nome_alunos[matricula][turmas_default[self.matricula_aluno][1]] == str(turmas_default[self.matricula_aluno][0]):
					self.turma.append(matricula)
			self.eh_turma = True
		else:
			self.t = int(self.nome_alunos[self.matricula_aluno][2])
			self.turma = [self.matricula_aluno]
			self.eh_turma = False
	
		for ind in range(len(self.turma)):
			self.turma[ind] = self.turma[ind].rstrip('\n')
		
		self.dados_grafico = resultados_por_dia(self.lista_de_resultados, self.turma, self.data, self.df, self.questoes, self.filtro, self.t)
		resolver = ""
		certas = ""
		erradas = ""
		if not self.eh_turma:
			if self.matricula_aluno in self.nome_alunos.keys():
				self.cabecalho = "Aluno: "  +  self.nome_alunos[self.matricula_aluno][IND_NOME] + " - " + self.matricula_aluno
				
				self.results = resultado_submissoes(self.lista_de_resultados, self.turma, self.data, self.df, self.questoes)
				
				for q in sorted(self.results[1]):
					resolver += zero_complete(str(q)) + " "
				for questao in sorted(self.results[2].keys()):
					if self.results[2][questao]:
						certas += zero_complete(str(questao)) + " "
					else:
						erradas += zero_complete(str(questao)) + " "
					
			else:
				self.cabecalho = u"Aluno não existente" + " - " + self.matricula_aluno
				self.results = [[], [], {}]
 		else:
			self.cabecalho = str(self.matricula_aluno)
		
		if self.semana == '1':
			med = u"submissões por semana"
		else:
			med = u"submissões por dia" 
			
		self.relatorio = relatorio_sub(self.lista_de_resultados, self.turma, self.data, self.df, self.semana)
		
		self.media = u'Média: ' + str(self.relatorio[0]) + ' ' + med + '\n'
		
		if len(self.relatorio[1]) > 0:
			self.intervalo = 'Intervalo: ' + str(self.relatorio[1][0]) + ' - ' + str(self.relatorio[1][1])
		else:
			self.intervalo = ''
			
		header_values = {
			'tamanho' : '100%',
			'cabecalho' : self.cabecalho,
			'media' : self.media,
			'intervalo' : self.intervalo,
			'porfazer' : resolver,	
			'ehturma' : self.eh_turma,	
			'q_certas' : certas,
			'q_erradas' : erradas,		
		}
		header = jinja_environment.get_template('reporttemplates/header.html')
		self.response.out.write(header.render(header_values))
		
	def grafico(self):
		if self.semana:
			self.graf = resultados_por_semana(resultados_por_dia(self.lista_de_resultados, self.turma, self.data, self.df, self.questoes, self.filtro, self.t))
			self.lista_grafico = coordenadas(self.graf, 'week', 'Semana ')
		else:
			self.graf = resultados_por_dia(self.lista_de_resultados, self.turma, self.data, self.df, self.questoes, self.filtro, self.t)
			self.lista_grafico =  coordenadas(self.graf, 'day', 'Dia ')
		self.iden = 'grafico' + str(self.matricula_aluno)
		self.div = str(self.matricula_aluno) + 'grafico'
			
	def alunos_da_turma(self):
		alunos_turma_values = {
			'turma' : self.turma,
			'data' : self.data,
			'df' : self.df,
			'dia' : self.dia,
			'semana' : self.semana,
			'nomes' : self.nome_alunos,
			'grafico' : self.grafico(),
			'tamanho' :'100%',
			'matricula_aluno' : self.matricula_aluno,
			'coordenadas' : self.lista_grafico,
			'iden' : self.iden,
			'div' : self.div,
			'questoes' : self.safe,		
		}
		if self.data:
			alunos_turma_values['data'] = self.data.strftime("%d%m%Y")
		if self.df:
			alunos_turma_values['df'] = self.df.strftime("%d%m%Y")
		alunos_turma = jinja_environment.get_template('reporttemplates/alunos_turma.html')
		self.response.out.write(alunos_turma.render(alunos_turma_values))
	
	def form_aluno(self):
		form_aluno_values = {
			'aluno' : self.matricula_aluno,
		}
		form_aluno = jinja_environment.get_template('reporttemplates/form_aluno.html')
		self.response.out.write(form_aluno.render(form_aluno_values))
		
	def filtro_questoes(self):
		self.questoes_parametros = ""
		for questao in self.questoes:
			self.questoes_parametros += questao + ", "
			
		self.certas = u'Submissões certas: ' + str(dic_resultados(self.dados_grafico)['c']) + '\n'
		self.erradas = u'Submissões erradas: ' + str(dic_resultados(self.dados_grafico)['e']) + '\n' + '\n'
		questoes_values = {
		'tamanho' : '100%',
		'questoes' : self.questoes_parametros[:-2],
		'certas' : self.certas,
		'erradas' : self.erradas,
		}
		questoes = jinja_environment.get_template('reporttemplates/questoes.html')
		self.response.out.write(questoes.render(questoes_values))
		
	def resultados_grafico(self):
		resultados_grafico_values = {
			'tamanho' :'100%',
			'resultados' : self.results,
			'matricula_aluno' : self.matricula_aluno,
			'grafico' : self.grafico(),
			'coordenadas' : self.lista_grafico,
			'iden' : self.iden,
			'div' : self.div,
		}
		resultados_grafico = jinja_environment.get_template('reporttemplates/resultados_grafico.html')
		self.response.out.write(resultados_grafico.render(resultados_grafico_values))
	
app = webapp2.WSGIApplication([('/report', Report)],
                              debug=DEBUG)
