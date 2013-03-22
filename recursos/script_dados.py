import urllib2

lista_alunos_unsorted = urllib2.urlopen("https://dl.dropbox.com/u/74287933/2012.2/alunos.csv")

def gera_dados_alunos():
	lista_alunos_sorted = open('dados_alunos.txt', 'w+')

	matriz_dados = []
	for linha in lista_alunos_unsorted:
		linha = linha.split(',')
		
		nome = linha[3].split()
		nome_corrigido = ''
		for caractere in range(len(nome)):
			nome[caractere] = nome[caractere].lower()
			nome[caractere] = nome[caractere].capitalize()
			nome_corrigido += nome[caractere]
			if caractere != len(nome)-1:
				nome_corrigido += ' '
			else:
				nome_corrigido += '\n'
				
		corrigido = [linha[2], linha[0], linha[1], nome_corrigido]
		matriz_dados.append(corrigido)

	matriz_dados = sorted(matriz_dados, key=lambda student: student[3])
	for info_aluno in matriz_dados:
		string_linha = ''
		for elemento in range(len(info_aluno)):
			string_linha += info_aluno[elemento]
			if elemento != len(info_aluno)-1:
				string_linha += ','
		lista_alunos_sorted.write(string_linha)
			
	lista_alunos_sorted.close()

def get_resultados():
	resultados = open('resultados_teste.txt', 'w+')
	arquivo = urllib2.urlopen("https://dl.dropbox.com/u/74287933/2012.2/reports/tst-results.dat")
	for elemento in arquivo:
		resultados.write(elemento)
	
gera_dados_alunos()
get_resultados()
