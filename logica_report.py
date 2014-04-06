#  -*- coding: utf-8 -*-
import math
from datetime import datetime, timedelta
import model

dict_classes = {
    "TP1": (0, 3), "TP2": (0, 3), "TP3": (1, 4), "TP4": (1, 4), "TP5": (2, 4)}

# FIXME fix SS and other metrics...


class Report_Logic():

    def __init__(self):
        # self.students: { matricula: Student }
        # self.questions: set(ids)
        # self.classes: { id: Turma
        self.students, self.questions, self.classes = model.create_students_questions_and_classes()

    def _define_interval(self, question_date, inicial_date, final_date):
        # Return a list with a test, and sets start and final date.
        inicial_date = inicial_date or question_date.date()
        final_date = final_date or (datetime.now() + timedelta(0, 24 * 3600 + 1)).date()  # final_date or 1 day in the future
        return [inicial_date <= question_date.date() <= final_date, inicial_date,  final_date]

    def _question_filter(self, questions, q):
        question = False
        if len(questions) == 0:
            question = True
        if q in questions:
            question = True
        return question

    def search_name(self, name):
        return model.search_name(self.students, self.classes, name)

    def submissions_results(self, matriculas, inicial_date, final_date, question_list):
        questions = []  # questions with student submissions -- TODO review format
        done = {}  # questions already done
        to_be_done = []  # questions to be done (not successfuly done or not tried)

        for student in matriculas:
            for submission in student.submissions:
                if self._define_interval(submission.date, inicial_date, final_date)[0] and self._question_filter(question_list, submission.question):
                    done[submission.question] = submission.success
                    questions.append('- ' + submission.date.strftime("%H:%M %d/%m/%Y") + ' ' + submission.question + ' ' + submission.result)

        for q in self.questions:
            if q not in done:
                to_be_done.append(q)

        return [questions, to_be_done, done]

    def classes_filter(self, classes, week_day):
        # FIXME load classesfrom a file -- FIXME when t (class) is 0.
        return week_day in classes

    def results_day(self, list_matricula, inicial_date, final_date, question_list, tp):
        # Returns [graphics, on_class, out_of_class] where:
        # - graphics -> general data
        # - on_class -> questions on class
        # - out_of_class -> questions done out of class
        #
        # graphics[date] = {'e': 0, 'c'} where e = errors, c = successful
        # and...
        # graphics['day'] = [date1, date2, date3, ...] where date1 = is a date
        #                   (same as order)
        # in '%d/%m/%Y'.
        #
        # list_matricula is a list of matriculas
        questions_time = []
        tests = {}
        order = []
        grafics = {}
        on_class = {}
        out_of_class = {}

        # -> tests is a dict mapping dates with submissions and their test
        # results
        for student in list_matricula:
            for submission in student.submissions:
                if self._define_interval(submission.date, inicial_date, final_date)[0] and self._question_filter(question_list, submission.question):
                    questions_time.append(submission.date)
                    tests[submission.date] = submission.success

        questions_time.sort()

        if len(questions_time) == 0:  # nothing to do here... get out!
            return [grafics, on_class, out_of_class]

        inicial_date, final_date = self._define_interval(questions_time[0], inicial_date, final_date)[1:3]

        # Initializing output dicts.
        while inicial_date <= final_date:
            d = inicial_date.strftime("%d/%m/%Y")
            order.append(d)
            grafics[d] = {'e': 0, 'c': 0}
            on_class[d] = {'e': 0, 'c': 0}
            out_of_class[d] = {'e': 0, 'c': 0}
            inicial_date += timedelta(days=1)
        grafics['day'] = order
        on_class['day'] = order
        out_of_class['day'] = order

        # Setting dict values
        for day in questions_time:
            dia = day.strftime("%d/%m/%Y")
            if dia in grafics:
                if tests[day]:
                    grafics[dia]['c'] += 1
                else:
                    grafics[dia]['e'] += 1
            if dia in on_class and self.classes_filter(dict_classes.get(tp, (0, 0)), day.weekday()):
                if tests[day]:
                    on_class[dia]['c'] += 1
                else:
                    on_class[dia]['e'] += 1
            else:
                if tests[day]:
                    out_of_class[dia]['c'] += 1
                else:
                    out_of_class[dia]['e'] += 1
        return [grafics, on_class, out_of_class]

    # Convert each dict from Report_Logic.results_day(..) to week.
    # Same format as results_day, but each key being a week number.
    def results_week(self, dict_results):
        grafics = {}
        cont = 0
        order = []
        for d in dict_results['day']:
            week_number = (cont / 7) + 1
            if week_number not in grafics:
                grafics[week_number] = {'c': 0, 'e': 0}
                order.append(week_number)
            grafics[week_number]['c'] += dict_results[d]['c']
            grafics[week_number]['e'] += dict_results[d]['e']
            cont += 1
        grafics['week'] = order

        return grafics

    # Process submissions to get an average submission rate and interval:
    # with [initial date, final date] (in %d/%m/%Y formats)
    def submission_report(self, class_students, inicial_date, final_date, is_week):
        timetable = []
        interval = []
        media = 0.0

        for student in class_students:
            for submission in student.submissions:
                if self._define_interval(submission.date, inicial_date, final_date)[0]:
                    timetable.append(submission.date)

        timetable.sort()

        if len(timetable) > 0:

            inicial_date, final_date = self._define_interval(
                timetable[0], inicial_date, final_date)[1:3]

            interval.append(inicial_date.strftime("%d/%m/%Y"))
            interval.append(final_date.strftime("%d/%m/%Y"))

            days = (final_date - inicial_date).days + 1

            if is_week:
                weeks = days / 7.0
                if weeks <= 1:
                    weeks = 1
                media = float(len(timetable)) / weeks
                media = "%.1f" % media
            else:
                media = float(len(timetable)) / float(days)
                media = "%.1f" % media

        return [media, interval]

    # dict_results that are from Report_Logic.results_day(..)
    # separete correct and wrong results from results_day
    def right_wrong_results(self, dict_results):
        results = {'c': 0, 'e': 0}
        if 'day' in dict_results:
            for d in dict_results['day']:
                results['c'] += dict_results[d]['c']
                results['e'] += dict_results[d]['e']

        return results

    # - dict_results are from results_day and results_week.
    # - interval is 'day' or 'week'
    # - string is label
    #
    # Returns:
    # [["01/02", "10", "4"], ["02/04", "11", "5"], ...] where 10, 11 are
    # number of correct questions and 4, 5 are incorrect questions
    # or..... [["Semana1"... ] where 'semana' is the string value (ex.)
    def coordinates(self, dict_results, interval, string):
        complete = []
        if interval in dict_results:
            for key in dict_results[interval]:
                line = []
                if interval == 'day':
                    line.append(str(key[0:5]))
                else:
                    line.append(string + str(key))
                line.append(dict_results[key]['c'])
                line.append(dict_results[key]['e'])
                complete.append(line)
        return complete

    def summarization(self, dict_results):
        # dict_results is a dictionary of students and their submission rate average
        results = {}

        cur_maximo = ('', -10.0)
        cur_minimo = ('', 10000000.0)
        maximo = ''
        minimo = ''

        """ media, max, min """
        soma = 0
        for aluno, media in dict_results.items():
            if cur_maximo[1] < media:
                cur_maximo = ([aluno], media)
            elif cur_maximo[1] == media:  # it can be a draw
                cur_maximo[0].append(aluno)
            if cur_minimo[1] > media:
                cur_minimo = ([aluno], media)
            elif cur_minimo[1] == media:  # it can be a draw
                cur_minimo[0].append(aluno)
            soma += float(media)
        media_geral = soma / len(dict_results)
        results['media'] = media_geral

        for aluno in cur_maximo[0]:
            maximo += aluno.name + ' '
        results['maximo'] = maximo + str(cur_maximo[1])

        for aluno in cur_minimo[0]:
            minimo += aluno.name + ' '
        results['minimo'] = minimo + str(cur_minimo[1])

        medias_ord = dict_results.values()
        medias_ord.sort()

        """ mediana """
        meio = len(dict_results) / 2
        mediana = medias_ord[meio]
        results['mediana'] = mediana

        """ quartis """
        pq = len(dict_results) / 4
        tq = 3 * (len(dict_results)) / 4

        pri_q = medias_ord[pq]
        results['priquar'] = pri_q

        ter_q = medias_ord[tq]
        results['terquar'] = ter_q

        """ variancia """
        desvios = 0
        for med in dict_results.values():
            desvios += (float(med) - media_geral) ** 2

        variancia = desvios / len(dict_results)
        results['variancia'] = variancia

        """ desvio padrao """
        dp = math.sqrt(variancia)
        results['despad'] = dp

        return results

    # Flats Report_Logic.coordinates() results.
    def _opens_cordinates(self, list_given):
        final = []
        for elem in list_given:
            final.append(elem[0])
            final.append(elem[1])
            final.append(elem[2])
        return final

    # Recieves: [.coordinates(student) results, .coordinate(p) results, len(tp)]
    # Output: [matricula, correct, wrongs, correct (tp), wrong (tp)]
    def merge_coordinates(self, list_student, list_class, number_of_students):
        merged_list = []
        list_student = self._opens_cordinates(list_student)

        for elem in list_class:
            merged_line = []
            merged_line.append(elem[0])

            try:
                i = list_student.index(elem[0])
                merged_line.append(list_student[i + 1])
                merged_line.append(list_student[i + 2])

            except ValueError:
                merged_line.append(0)
                merged_line.append(0)

            merged_line.append(int(elem[1]) / number_of_students)
            merged_line.append(int(elem[2]) / number_of_students)
            merged_list.append(merged_line)

        return merged_list

    def top_submited(self, current_student):
        questions = {}  # questions that this student have done
        class_questions = {}  # questions that all students have done

        for question in self.questions:
            questions[question] = [0, question, False]
            class_questions[question] = [0, question, False]

            for matricula, student in self.students.items():
                class_questions[question][0] += 1

        for question_name, question in current_student.questions.items():
            if not question.success:
                questions[question_name][0] += 1
            else:
                questions[question_name][2] = True

        top_student, not_sub = self._rank_submissions(questions)
        class_order = self._rank_submissions(class_questions)[0]
        top_class = {"done": [], "not_done": [], "merge": []}
        for q in class_order:
            if q in not_sub and q not in top_class["not_done"]:
                top_class["not_done"].append(q)
            elif q in top_student and q not in top_class["done"]:
                top_class["done"].append(q)
            if (q in top_student or q in not_sub) and q not in top_class["merge"]:
                top_class["merge"].append(q)
        if len(top_student) > 5:
            top_student = top_student[0:5]
        return [top_student, top_class]

    def _rank_submissions(self, dict_sub):
        aux_list = []
        aux_list2 = []
        not_sub = []

        for q in dict_sub.keys():
            if not dict_sub[q][2] and dict_sub[q][0] != 0:
                aux_list.append(dict_sub[q][0])
                aux_list.append(dict_sub[q][1])
                aux_list2.append(dict_sub[q][0])
            if not dict_sub[q][2] and dict_sub[q][0] == 0:
                not_sub.append(dict_sub[q][1])
        sub = []
        order = sorted(aux_list2)
        for s in reversed(order):
            for ind in range(0, len(aux_list), 2):
                if s == aux_list[ind]:
                    sub.append(aux_list[ind + 1])
        return [sub, not_sub]
