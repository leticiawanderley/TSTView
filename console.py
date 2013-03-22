#  -*- coding: utf-8 -*-

import webapp2
from logica_report import get_data
from datetime import datetime, timedelta
import os
import jinja2
jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

DEBUG = False
IND_MATRICULA, IND_QUESTAO, NOME, IND_SUBMISSAO, IND_DATAHORA, IND_TESTE = 1, 2, 3, 3, 4, 5

alunos = open("recursos/dados_alunos.txt")
dict_alunos = {}
for info_aluno in alunos:
	info_aluno = info_aluno.strip("\n\r").split(",")
	mat = info_aluno[0]
	dict_alunos[mat] = info_aluno

def processa_dados(datainicio, datafim, info):

	"""
	Recebe um pacote de dados (de um arquivo ou url) e processa
	transformando em 2 dicionarios. Dicionario matricula:
	'dicionario = {matricula: [submissao_total,matricula,questao,submissao,data+hora,teste]}'
	Dicionario questao:
	'dicionario = {questao: [sequencia de matriculas]}'
	"""

	dict_matriculas = {}
	dict_questoes = {}
	for linha in info:
		linha = linha.strip("\r\n").split(",")
		datahora_submissao = datetime(int(linha[IND_DATAHORA][6:10]), int(linha[IND_DATAHORA][3:5]), int(linha[IND_DATAHORA][:2]), int(linha[IND_DATAHORA][11:13]), int(linha[IND_DATAHORA][14:16]))
		if datainicio <= datahora_submissao <= datafim:

			matricula = linha[IND_MATRICULA]
			resultados = dict_matriculas.get(matricula, [])
			resultados.append(linha)
			dict_matriculas[matricula] = resultados

			questao = linha[IND_QUESTAO]
			submissoes = dict_questoes.get(questao, [])
			submissoes.append(linha[IND_MATRICULA])
			dict_questoes[questao] = submissoes

	return dict_matriculas, dict_questoes

def erro(string_teste):

	"""
	Checa, através da string do teste,
	se a questão tem erro
	"""

	error = False
	for caractere in string_teste:
		if caractere != ".":
			return True

	return error

def lista_submissoes(dict_mat, datainicio, datafim, turma_analisada, dict_alunos, turma, hoje):
	
	"""
	Processa os dicionarios retornando uma tabela html
	com os dados das submissoes no periodo de tempo
	passado pelo usuario. No formato:
	'- Aluno:  sequencia de questoes'
	"""
	
	df = datetime.strftime(datafim, "%d%m%Y")
	lista_template = jinja_environment.get_template("consoletemplates/lista_submissoes.html")
	print_string = lista_template.render()
	for aluno in turma_analisada:
		nome_aluno = dict_alunos[aluno][NOME]
		print_string += """<tr onMouseover="this.bgColor='#DBDBDB';" onMouseout="this.bgColor='#FFFFFF';"><dl><dd><td onClick="document.location.href='/report?data=%s&df=%s&matriculas=%s';" style="vertical-align:top;cursor:pointer;cursor:hand" title="%s"><img src="http://cdn1.iconfinder.com/data/icons/splashyIcons/arrow_state_grey_right.png"><a style="vertical-align:top;color:blue; text-decoration:none">&nbsp;%s</a>:</td></dd></dl><td>""" % (datetime.strftime(datainicio, "%d%m%Y"), df, aluno, u"Matrícula: " + aluno + ". TT" + dict_alunos[aluno][1] + ", TP" + dict_alunos[aluno][2], nome_aluno)
		if aluno in dict_mat:
			for indice in range(len(dict_mat[aluno])-1,-1,-1):
				questao = "%03d" % int(dict_mat[aluno][indice][IND_QUESTAO])
				teste = dict_mat[aluno][indice][IND_TESTE]
				if erro(teste):
					print_string += """<font color="red">%s</font> """ % questao
				else:
					print_string += """%s """ % questao
		print_string += """</td></tr>"""
	print_string += """</table></body></div>"""

	return print_string

def sumarizacao(dict_mat, dict_quest, datainicio, datafim, questao_sumarizada, turma_analisada):
	
	"""
	Processa os dados dos dicionarios, retornando
	uma sumarizacao (acertos, erros, nao_submissoes) 
	sobre uma determinada questao no periodo de tempo passado.
	"""
	
	submissoes_aluno, fizeram_certa, fizeram_errada, nao_fizeram = [], set(), set(), set()
	for aluno in turma_analisada:
		if questao_sumarizada not in dict_quest or aluno not in dict_quest[questao_sumarizada]:
			nao_fizeram.add(aluno)
			continue
		for indice in range(len(dict_mat[aluno])-1,-1,-1):

			questao = dict_mat[aluno][indice][IND_QUESTAO]
			teste = dict_mat[aluno][indice][IND_TESTE]
			if questao == questao_sumarizada:

				if erro(teste):
					submissoes_aluno.append("%sE" % questao)
					if aluno not in fizeram_certa:
						fizeram_errada.add(aluno)
				else:
					submissoes_aluno.append("%s" % questao)
					if aluno not in fizeram_errada:
						fizeram_certa.add(aluno)

	certas = len(fizeram_certa)
	erradas = len(fizeram_errada)
	num_nao_fizeram = len(nao_fizeram)
	sumario = [certas, fizeram_certa, erradas, fizeram_errada, num_nao_fizeram, nao_fizeram]

	return sumario

def grafico(sumario, questao_sumarizada, datainicio, datafim, dict_alunos):
	
	"""
	Template que gera a string html do grafico da questao
	cujos dados foram sumarizados por sumarizacao().
	"""
	
	grafico_values = {
	"certas" : sumario[0],
	"erradas" : sumario[2],
	"num_nao_fizeram" : sumario[4],
	"questao_sumarizada" : questao_sumarizada,
	"sumario1" : sumario[1],
	"sumario3" : sumario[3],
	"sumario5" : sumario[5],
	"datainicial" : datetime.strftime(datainicio, "%d%m%Y"),
	"df" : datetime.strftime(datafim, "%d%m%Y"),
	"alunos" : dict_alunos
	}
	grafico = jinja_environment.get_template("consoletemplates/grafico.html")

	return grafico.render(grafico_values)

def tabela(dict_mat, dict_quest, horainicio, datainicio, datafim, horafim, lista_questoes, turma, turma_analisada, dict_alunos):
	
	"""
	Processa os dados retornando uma tabela html que indica
	o acerto ou erro da ultima submissao de questoes especificas
	"""
	
	df = datetime.strftime(datafim, "%d%m%Y")
	questoes_tabela = set()
	for question in lista_questoes:
		questoes_tabela.add(int(question))

	lista_ordenada = sorted(questoes_tabela)
	tabelahtml_values = {
	"lista_ordenada" : lista_ordenada,
	"datainicio" : datetime.strftime(datainicio, "%d%m%Y"),
	"horainicio" : horainicio,
	"datafim" : datetime.strftime(datafim, "%d%m%Y"),
	"horafim" : horafim,
	"turma" : turma
	}        
	tabelahtml = jinja_environment.get_template("consoletemplates/tabela.html")
	tabela_head = tabelahtml.render(tabelahtml_values)

	tabela_body = """"""
	for aluno in turma_analisada:
		tabela_body += """<tr><td onClick="document.location.href='/report?data=%s&df=%s&matriculas=%s';" style="cursor:pointer;cursor:hand" title="%s" onMouseover="this.bgColor='#DBDBDB';"onMouseout="this.bgColor='#FFFFFF';" width="300" align="center"><p class="helvetica" style="line-height:14px; font-size:12.5px;"><a style="color:blue; font-weight:bold; text-decoration: none;">%s</a></td>""" % (datetime.strftime(datainicio, "%d%m%Y"), df, aluno, u"Matrícula: " + aluno + ". TT" + dict_alunos[aluno][1] + ", TP" + dict_alunos[aluno][2], dict_alunos[aluno][NOME])
		for questao in sorted(questoes_tabela):
			if str(questao) not in dict_quest or aluno not in dict_quest[str(questao)]:
				tabela_body += """<td bgcolor=#5C5C5C></td>"""
			else:
				for indice in range(len(dict_mat[aluno])-1,-1,-1):
					quest = int(dict_mat[aluno][indice][IND_QUESTAO])
					submissao = int(dict_mat[aluno][indice][IND_SUBMISSAO])
					teste = dict_mat[aluno][indice][IND_TESTE]
					if quest == questao:
						if erro(teste):
							tabela_body += """<td align="center" bgcolor=#FF0000><b>%s</b></td>""" % submissao
						else:
							tabela_body += """<td align="center" bgcolor=#00FF00><b>%s</b></td>""" % submissao
						break
		tabela_body += """</tr>"""
	tabela_end = """</table></div></body></html>"""
	tabela = """<div align="center">""" + tabela_head + tabela_body + tabela_end + """</div>"""

	return tabela

def acessa_dados():

	acesso = True
	if not DEBUG:
		try:
			info = get_data()
		except:
			info = open("recursos/resultados_teste.txt")
			acesso = False
	else:
		info = open("recursos/resultados_teste.txt")	
	
	return info, acesso

def tratamento_parametros_data(hoje, horainicio, datainicio, horafim, datafim):
		
	try:
		
		
		""" Tratamento Parametro Hora Inicio"""
		
		if not horainicio:
			if 8 <= hoje.hour <= 17:
				horainicial = timedelta(0, (hoje.hour - (hoje.hour % 2)) * 3600)
			else:
				horainicial = timedelta(0, 0)
		else:
			if len(horainicio) != 4:
				raise ValueError
			hora = "%02d" % int(horainicio[0:2])
			minutos = "%02d" % int(horainicio[2:4])
			horainicial = timedelta(0, (int(hora) * 3600) + (int(minutos) * 60))
		
		""" Tratamento Parametro Hora Fim """
		
		if not horafim:
			horafinal = timedelta(0, (hoje.hour * 3600) + (hoje.minute * 60) + hoje.second)
		else:
			if len(horafim) != 4:
				raise ValueError
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
			if horafim:
				datainicial = datetime.strptime(datainicio, "%d%m%Y") + horainicial
				datafinal = datetime.strptime(datainicio, "%d%m%Y") + horafinal
			else:
				datainicial = datetime.strptime(datainicio, "%d%m%Y") + horainicial
				
	except ValueError:
		return False

	else:
		return (datetime.strftime(datainicial, "%H%M"), datainicial, datafinal)

def tratamento_parametros_alunos(questoes, turma, dict_alunos, dict_mat):
	
	""" Tratamento Parametro Questoes """
	

	lista_questoes = []
	for question in questoes.strip(" ").split(","):
		lista_questoes.append(question)
	
	""" Tratamento Parametro Turma """
	
	matricula_inexistente = False
	turma_analisada = []
	bad_mat = ""

	if turma:
		lista_turma = turma.split(",")
		for t in lista_turma:
			t = t.upper().strip(" ")
			if "T" in t:
				for aluno in sorted(dict_alunos, key = lambda aluno: dict_alunos[aluno][3]):
					if t in ["TP1","TP2","TP3","TP4","TP5"] and dict_alunos[aluno][2] == t[2]:
						turma_analisada.append(aluno)
					elif t in ["TT1","TT2","TT3"] and dict_alunos[aluno][1] == t[2]:
						turma_analisada.append(aluno)
			else:
				for aluno in sorted(lista_turma, key = lambda aluno: False if aluno.strip(" ") not in dict_alunos else dict_alunos[aluno.strip(" ")][3]):
					aluno = aluno.strip(" ")
					if aluno not in dict_alunos:
						matricula_inexistente = True
						bad_mat = aluno
						break
						
					else:
						if aluno not in turma_analisada:
							turma_analisada.append(aluno)
	else:
		for matricula in sorted(dict_mat.keys(), key = lambda aluno: dict_alunos[aluno][3]):
			turma_analisada.append(matricula)

	return lista_questoes, turma_analisada, matricula_inexistente, bad_mat

class Console(webapp2.RequestHandler):
	def get(self):
		
		"""
		Coleta o pacote de dados (arquivo ou url)
		"""
		
		(info, acesso) = acessa_dados()
		navigation = jinja_environment.get_template("/static/templates/navigation.html")
		self.response.out.write(navigation.render())

		""" Parametros e tratamento de entrada """
		
		self.response.headers["Content-Type"] = "text/html; charset=utf-8"
		diferenca_tz = timedelta(0, 3 * 3600)
		hoje = datetime.now() - diferenca_tz
		
		""" Tratamento Parametro Hora Inicio"""
			
		horainicio = self.request.get("hi",default_value = "")
		datainicio = self.request.get("di",default_value = "")
		horafim = self.request.get("hf",default_value = "")
		datafim = self.request.get("df",default_value = "")
		
		teste = tratamento_parametros_data(hoje, horainicio, datainicio, horafim, datafim)		
		if teste:
			(param_horainicio, datainiciotratada, datafimtratada) = teste
			(dict_mat, dict_quest) = processa_dados(datainiciotratada, datafimtratada, info)
			
			""" Tratamento Parametro Alunos """
			
			questoes = self.request.get("qt",default_value = "")
			graph = False
			if not questoes:
				questoes = self.request.get("qg",default_value = "")
				if questoes:
					graph = True
			turma = self.request.get("trm",default_value = "")
			(lista_questoes, turma_analisada, matricula_inexistente, bad_mat) = tratamento_parametros_alunos(questoes, turma, dict_alunos, dict_mat)
			questao_sumarizada = lista_questoes[0]
			sumario = sumarizacao(dict_mat, dict_quest, datainiciotratada, datafimtratada, questao_sumarizada, turma_analisada)
			
			""" Prints layout e cabecalho """
			
			if not acesso:
				erro_acesso = jinja_environment.get_template("consoletemplates/erro_acesso.html")
				self.response.out.write(erro_acesso.render())
				
			print_intervalo = u"Submissões no intervalo (Das %s de %s às %s):" % (datetime.strftime(datainiciotratada, "%H:%M"), datetime.strftime(datainiciotratada, "%d/%m/%Y"), datetime.strftime(datafimtratada, "%H:%M de %d/%m/%Y"))
			cabecalho_values = {
				"print_intervalo" : print_intervalo
			}
			cabecalho = jinja_environment.get_template("consoletemplates/cabecalho.html")

			""" Logica de funcionamento """
			
			if matricula_inexistente:
				self.response.out.write(u"""<p class="helvetica" style="text-align:center; font-size:30px; font-weight:bold; color:red">Parâmetro Inválido - Matrícula: %s</a>""" % bad_mat)
			else:
				self.response.out.write(cabecalho.render(cabecalho_values))
				if graph:
					self.response.out.write(grafico(sumario, questao_sumarizada, datainiciotratada, datafimtratada, dict_alunos))
				else:	
					ajax_replace_values = {
					"turma" : turma,
					"datainicial" : datainicio,
					"datafinal" : datafim,
					"horainicial" : horainicio,
					"horafinal" : horafim,
					"questoes" : questoes
					}
					ajax_replace = jinja_environment.get_template("consoletemplates/ajax_replace.html")
					self.response.out.write(ajax_replace.render(ajax_replace_values))
		else:
			self.response.out.write(u"""<p class="helvetica" style="text-align:center; font-size:30px; font-weight:bold; color:red">Parâmetro(s) inválido(s)""")
			
		formularios = jinja_environment.get_template("consoletemplates/formularios.html")
		self.response.out.write(formularios.render())

class RefreshData(webapp2.RequestHandler):
	def get(self):
		
		"""
		Coleta o pacote de dados (arquivo ou url)
		"""
		
		(info, acesso) = acessa_dados()
		
		""" Parametros e tratamento de entrada """
		
		self.response.headers["Content-Type"] = "text/html; charset=utf-8"
		diferenca_tz = timedelta(0, 3 * 3600)
		hoje = datetime.now() - diferenca_tz
		
		""" Tratamento Parametro Hora Inicio"""
			
		horainicio = self.request.get("hi",default_value = "")
		datainicio = self.request.get("di",default_value = "")
		horafim = self.request.get("hf",default_value = "")
		datafim = self.request.get("df",default_value = "")
		
		(param_horainicio, datainiciotratada, datafimtratada) = tratamento_parametros_data(hoje, horainicio, datainicio, horafim, datafim)
		(dict_mat, dict_quest) = processa_dados(datainiciotratada, datafimtratada, info)
		
		""" Tratamento Parametro Alunos """
		
		questoes = self.request.get("qt",default_value = "")
		turma = self.request.get("trm",default_value = "")
		(lista_questoes, turma_analisada, matricula_inexistente, bad_mat) = tratamento_parametros_alunos(questoes, turma, dict_alunos, dict_mat)
		
		""" Logica de funcionamento """
		
		if not questoes:
			self.response.out.write(lista_submissoes(dict_mat, datainiciotratada, datafimtratada, turma_analisada, dict_alunos, turma, hoje))
		else:
			self.response.out.write(tabela(dict_mat, dict_quest, param_horainicio, datainiciotratada, datafimtratada, horafim, lista_questoes, turma, turma_analisada, dict_alunos))

app = webapp2.WSGIApplication([("/", Console), ("/refreshdata", RefreshData)], debug=DEBUG)
