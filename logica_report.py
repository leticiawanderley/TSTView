#  -*- coding: utf-8 -*- 
import math
import urllib2
import gzip
import json 
import StringIO
from datetime import datetime, timedelta
from google.appengine.api import memcache

IND_DATA = 3
IND_MATRICULA = 0
IND_QUESTAO = 1
IND_NOME = 3
dict_classes = {0:(0,0), 1:(0,3), 2:(0,3), 3:(1,4), 4:(1,4), 5:(2,4)}

def abre_resultado(result):
	lista_resultados = []
	for resultado in result:
		lista_resultados.append(resultado.split(',')[1:])
	return lista_resultados

def gzip_json(data):
    stream = StringIO.StringIO()
    gzipper = gzip.GzipFile(mode='wb', fileobj=stream)
    gzipper.write(json.dumps(data))
    gzipper.close()
    return stream.getvalue()
    
def gunzip_json(data):
    stream = StringIO.StringIO(data)
    gzipper = gzip.GzipFile(mode='rb', fileobj=stream)
    data = gzipper.read()
    return json.loads(data)
       
def get_data():
	try:
		data = memcache.get("results")
		if data is not None:
			return gunzip_json(data)
		else:
			data = urllib2.urlopen("https://dl.dropbox.com/u/74287933/2012.2/reports/tst-results.dat").readlines()
			data = gzip_json(data)
			memcache.add("results", data, 60)
	except urllib2.URLError, e:
		handleError(e)
	return gunzip_json(data)
	
def cria_dict_alunos():
	alunos = open('recursos/dados_alunos.txt')
	dict_alunos = {}
	for aluno in alunos:
		aluno = aluno.strip('\n\r').split(',')
		mat = aluno[IND_MATRICULA]
		dict_alunos[mat] = aluno
		
	return dict_alunos	
		
def define_intervalo(data, data_inicial, data_final):
	"""
	Verifica se o parametro data estah dentro do intervalo definido.
	Data eh uma string no formato DD/MM/YYYY HH:MM.
	Data_inicial pode ser opicional (vazio). Caso esteja ausente
	considere que o inicio eh no comeco do universo. Formato: DDMMYYYY.
	Data_final eh um parametro que representa o fim do intervalo. Eh
	tmb um campo opicional (vazio). Caso nao exista, considere o dia
	atual como o fim do intervalo. Segue o mesmo formato de data_inicial.
	"""
	data_questao = datetime(int(data[6:10]), int(data[3:5]), int(data[0:2])).date()
	
	if not data_inicial:
		data_inicial = data_questao
				
	if not data_final:
		data_final = (datetime.now() - timedelta(0, 3 * 3600)).date()
		
	return [data_inicial <= data_questao <= data_final, data_inicial, data_final]

def encontra_erro(string):
	return len(string.replace('.', '')) > 0
	
def zero_complete(string):
	return (3 - len(string)) * '0' + string
	
def matriculas_last_results(lista_resultados, data_inicial, data_final, dict_alunos, lista_questoes):
	""" 
	Cria lista de matriculas, a partir do last results de alunos que 
	enviaram questoes dentro do intervalo dos parametros 
	"""
	matriculas = {}
	for resultado in lista_resultados:
		if resultado[0] not in matriculas.keys() and filtra_por_questao(lista_questoes, resultado) and define_intervalo(resultado[IND_DATA], data_inicial, data_final)[0]:
			matriculas[resultado[0]] = dict_alunos[resultado[0]][IND_NOME]
			
	return matriculas

def resultado_submissoes(lista_resultados, lista_matriculas, data_inicial, data_final, lista_questoes):
	"""
	Cria lista com as questoes submetidas pelo aluno, ou por uma turma, 
	(dentro do intervalo passado no parametros), 
	data, hora e resultado nos testes concatenados
	"""
	questoes = []
	publicadas= []
	feitas = {}
	aresolver =[]
	for resultado in lista_resultados:
		if resultado[IND_QUESTAO] not in publicadas:
			publicadas.append(resultado[IND_QUESTAO])
		for matricula in lista_matriculas:
			if resultado[0] == matricula:
				if encontra_erro(resultado[4].rstrip('\n')):
					feitas[int(resultado[IND_QUESTAO])] = False
				elif not encontra_erro(resultado[4].rstrip('\n')):
					feitas[int(resultado[IND_QUESTAO])] = True
				if define_intervalo(resultado[IND_DATA], data_inicial, data_final)[0] and filtra_por_questao(lista_questoes, resultado):
					questoes.append('- ' + resultado[IND_DATA] + ' ' + resultado[IND_QUESTAO] + ' ' + resultado[4])			
	for questao in publicadas:
		questao = int(questao)
		if questao not in feitas.keys():
			aresolver.append(questao)
	return [questoes, aresolver, feitas]

def classes_filter(filtro, aulas, dia_da_semana):
	valid = False
	if filtro == 'geral' or aulas == (0,0):
		valid = True
	elif filtro == 'aula' and dia_da_semana in aulas:
		valid = True
	elif filtro == 'naoaula' and dia_da_semana not in aulas:
		valid = True
	return valid
	
def resultados_por_dia(lista_resultados, matricula, data_inicial, data_final, lista_questoes, filtro, t):
	hora_questoes = []
	testes = {}
	ordem = []
	graficos = {}
	
	for resultado in lista_resultados:
		dia = datetime(int(resultado[IND_DATA][6:10]), int(resultado[IND_DATA][3:5]), int(resultado[IND_DATA][0:2])).date()
		if resultado[0] in matricula and define_intervalo(resultado[IND_DATA], data_inicial, data_final)[0] and filtra_por_questao(lista_questoes, resultado) and classes_filter(filtro, dict_classes[t], dia.weekday()):
			hora_questoes.append(resultado[IND_DATA])
			
			if encontra_erro(resultado[4].rstrip('\n')):
				testes[resultado[IND_DATA]] = 0
			else:
				testes[resultado[IND_DATA]] = 1
				
	if len(hora_questoes) == 0:
		return graficos
	
	data_inicial, data_final = define_intervalo(hora_questoes[0][0:10], data_inicial, data_final)[1:3]
	
	while data_inicial <= data_final:
		dia = data_inicial.strftime("%d/%m/%Y")
		ordem.append(dia)
		graficos[dia] = {'e':0,'c':0}
		data_inicial += timedelta(days=1)
	graficos['day'] = ordem
	
	for day in hora_questoes:
		dia = day.split()[0]
							
		if graficos.has_key(dia):
			if testes[day] == 1:
				graficos[dia]['c'] += 1
			elif testes[day] == 0:
				graficos[dia]['e'] += 1	
				
	return graficos

def resultados_por_semana(dicionario):
	graficos = {}
	cont = 0
	ordem = []
	for d in dicionario['day']:
		numero_da_semana = (cont / 7) + 1
		if not graficos.has_key(numero_da_semana):
			graficos[numero_da_semana] = {'c':0, 'e':0}
			ordem.append(numero_da_semana)
		graficos[numero_da_semana]['c'] += dicionario[d]['c']
		graficos[numero_da_semana]['e'] += dicionario[d]['e']
		cont += 1
	graficos['week'] = ordem
				
	return graficos
	
def dic_resultados(dicionario):
	resultados = {'c':0, 'e':0}
	if dicionario.has_key('day'):
		for dia in dicionario['day']:
			resultados['c'] += dicionario[dia]['c']
			resultados['e'] += dicionario[dia]['e']
	
	return resultados
			
def relatorio_sub(lista_resultados, turma, data_inicial, data_final, intervalo_semana):
	"""
	Calcula a media de submissoes de um aluno ou uma turma de alunos
	dado um intervalo de tempo
	"""
	horario = []
	intervalo = []
	media = 0.0

	for resultado in lista_resultados:
		if resultado[0] in turma and define_intervalo(resultado[IND_DATA],data_inicial,data_final)[0]:
			horario.append(resultado[IND_DATA])
			
	if len(horario) > 0:
						
		data_inicial = define_intervalo(horario[0][0:10], data_inicial, data_final)[1]
		data_final = define_intervalo(horario[0][0:10], data_inicial, data_final)[2]
	
		intervalo.append(data_inicial.strftime("%d/%m/%Y"))
		intervalo.append(data_final.strftime("%d/%m/%Y"))					
		
		diferenca = data_final - data_inicial
		dias = diferenca.days + 1
		
		if intervalo_semana:
			semanas = dias/7.0
			if semanas <= 1:
				semanas = 1
			media = float(len(horario))/semanas
			media = "%.1f" % media			
		else:
			media = float(len(horario))/float(dias)
			media = "%.1f" % media
			
	return [media, intervalo]
						
def coordenadas(dic, intervalo, string):
	"""
	Forma a lista com dados para a construcao do grafico
	"""
	completo = []
	if dic.has_key(intervalo):
		for key in dic[intervalo]:
			lista = []
			if intervalo == 'day':
				lista.append(str(key[0:5]))
			else:
				lista.append(string + str(key))
			lista.append(dic[key]['c'])
			lista.append(dic[key]['e'])
			completo.append(lista)

	return completo	
	
def sumarizacao(dicionario):
	""" 
	Sumariza os dados do grupo de matriculas passado como parametro
	"""
	resultado = {}
	""" media """
	soma = 0
	for media in dicionario.values():
		soma += float(media)
	media_geral = soma/len(dicionario)
	resultado['media'] = media_geral
	
	medias_ord = dicionario.values()
	medias_ord.sort()
	
	""" mediana """
	meio = len(dicionario)/2
	mediana = medias_ord[meio]
	resultado['mediana'] = mediana
	
	""" quartis """
	pq = len(dicionario)/4
	tq = 3*(len(dicionario))/4
	
	pri_q = medias_ord[pq]
	resultado['priquar'] = pri_q
	
	ter_q = medias_ord[tq]
	resultado['terquar'] = ter_q
	
	""" maximo e minimo """
	maximo = ''
	minimo = ''
	for aluno in dicionario.keys():
		if dicionario[aluno] == medias_ord[-1]:
			maximo += aluno + ' '
		elif dicionario[aluno] == medias_ord[0]:
			minimo += aluno + ' '
	
	maximo += str(medias_ord[-1])
	resultado['maximo'] = maximo
	
	minimo += str(medias_ord[0])
	resultado['minimo'] = minimo
	
	""" variancia """
	desvios = 0
	for med in dicionario.values():
		desvios += (float(med) - media_geral)**2
	
	variancia = desvios/len(dicionario)
	resultado['variancia'] = variancia
	
	""" desvio padrao """
	dp = math.sqrt(variancia)
	resultado['despad'] = dp
	
	return resultado
	
def filtra_por_questao(questoes, lista):
	questao = False
	if len(questoes) == 0:
		questao = True
	if lista[IND_QUESTAO] in questoes:
		questao = True
	return questao
