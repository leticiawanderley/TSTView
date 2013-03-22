function loadXMLDoc()
{
var t = 0;
var xmlhttp;
  xmlhttp = new XMLHttpRequest();
  xmlhttp.onreadystatechange = function()
  {
  if (xmlhttp.readyState == 4 && xmlhttp.status == 200)
    {
    document.getElementById("listasubmissoes").innerHTML=xmlhttp.responseText + "Teste: " + " " + Math.random();
    setTimeout("loadXMLDoc()", 10*1000);
    }
  }
xmlhttp.open("GET","refreshdata?trm={{turma}}&di={{datainicial}}&hi={{horainicial}}&df={{datafinal}}&hf={{horafinal}}",true);
xmlhttp.send();
}