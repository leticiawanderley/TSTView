from datetime import datetime

import data_source


class Student(object):

    # Input:
    # recursos/demo/dados_alunos_demo.txt
    # 000000001,1,1,Ada Lovelace,ada.lovelace

    # new format:
    # 2,2,113210097,FABRICIO DE LIMA SILVA,fabricio.silva,fabricio.silva@ccc.ufcg.edu.br,
    def __init__(self, line):
        #self.matricula, self.tt, self.tp, self.name, self.email = line.split(',')
        self.tp, self.tt, self.matricula, _, self.name, self.email, _ = line.split(',')
        self.submissions = []
        self.questions = {}  # {id: Question}

    def _add_submission(self, questions, submission):
        self.submissions.append(submission)
        question = self.questions.get(submission.question, Question(submission.question))
        question.submissions += 1
        self.questions[submission.question] = question
        questions.add(submission.question)

    def __eq__(self, other):
        return self.matricula == other.matricula

    def __hash__(self):
        return hash(self.matricula)


class Turma():  # FIXME -- translate

    def __init__(self, name, alunos):
        self.alunos = list(alunos)
        self.nome = name


class Question(object):

    def __init__(self, name):
        self.name = name
        self.submissions = 0

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)


class _TestResult(object):

    def __init__(self, result):
        self.result = result.strip()
        self.success = len(self.result.replace('.', '')) == 0


class Submission(object):

    # FIXME max submission was removed... use it again?
    # Input:
    # recursos/resultados_teste.txt
    # 16,112210650,1,2,29/11/2012 09:07:31,FFFF

    # new format:
    # 2013,12,12,12,09,00,314720|joao.alcimar.junior@ccc.ufcg.edu.br|media_aluno|1|.....
    def __init__(self, line):
        #_, self.matricula, self.question, self.submission, date, tests = line.split(',')
        #self.date = datetime(int(date[6:10]), int(date[3:5]), int(date[0:2]), int(date[11:13]), int(date[14:16]), int(date[17:19]))
        date, self.email, self.question, self.submission, tests = line.split('|')
        self.date = datetime(*map(int, date.split(',')))
        self._test = _TestResult(tests)
        self.success = self._test.success
        self.result = self._test.result


def create_students_questions_and_classes(start_date=None, end_date=None):
    # TODO Cache this return -- specially submissions
    # FIXME Translate
    alunos = {}
    email_alunos = {}
    dicionario_turmas_p = {}
    dicionario_turmas_t = {}
    questions = set()

    for linha_info in data_source.get_students_data():
        aluno = Student(linha_info.strip())
        email_alunos[aluno.email] = aluno
        pratica = dicionario_turmas_p.get(aluno.tp, set())
        pratica.add(aluno)
        dicionario_turmas_p[aluno.tp] = pratica

        teorica = dicionario_turmas_t.get(aluno.tt, set())
        teorica.add(aluno)
        dicionario_turmas_t[aluno.tt] = teorica

        alunos[aluno.matricula] = aluno

    # Reading submissions...
    for linha_dados in reversed(data_source.get_test_data()):
        submissao = Submission(linha_dados)
        if submissao.email not in email_alunos:
            continue
        submissao.matricula = email_alunos[submissao.email].matricula
        # FIXME leave this to controller..
        if submissao.matricula in alunos and ((start_date is None and end_date is None) or (start_date <= submissao.date <= end_date)):
            alunos.get(submissao.matricula)._add_submission(questions, submissao)

    # creating classes...
    turmas = {}
    for turma in dicionario_turmas_p:
        nome = "TP" + turma
        turmas[nome] = Turma("TP" + turma, dicionario_turmas_p[turma])

    for turma in dicionario_turmas_t:
        nome = "TT" + turma
        turmas[nome] = Turma("TT" + turma, dicionario_turmas_t[turma])

    return alunos, questions, turmas


def search_name(students, classes, parameters):

    result = []

    if parameters.strip() == '':
        return students

    match = False
    for parameter in map(unicode.strip, parameters.split(',')):
        if parameter in classes:
            result.extend(classes[parameter].alunos)
            match = True

    if match:
        return result

    for parameter in map(unicode.strip, parameters.split(',')):
        for matricula, student in students.items():
            if parameter.lower() in student.name.lower() or parameter.lower() in matricula:
                result.append(student)
    return result


def _is_admin(user):
    adms = open("recursos/admins.txt").readlines()
    admins = []
    for adm in adms:
        adm = adm.strip()
        admins.append(adm)
    if user.email() in admins:
        return True
    return False


def info(user):
    if user:
        is_adm = _is_admin(user)
        email = user.email()
    else:
        is_adm = False
        email = ''
    return user, is_adm, email
