arquivo = open("resultados_teste_demo.txt")

arquivo_escrita = open("resultados_teste_demo2.txt", "w+")

lista = ["000000001", "000000002", "000000003", "000000004", "000000005", "000000006", "000000007", "000000008"
         "000000009", "000000010", "000000011", "000000012", "000000013", "000000014", "000000015", "000000016", "000000017", "000000018", "000000019", "000000020"]

for linha in arquivo:
    linha = linha.split(',')
    print linha
    if linha[1] in lista:
        arquivo_escrita.write(",".join(linha))
