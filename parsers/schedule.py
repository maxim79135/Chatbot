#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import urllib
from datetime import datetime
from typing import List

import fitz
from bs4 import BeautifulSoup


# TODO: week schedule
class TeacherScheduleParser():
    """Parser teacher schedule for VyatSU (vyatsu.ru)"""

    def __init__(self):
        self.lessons_times = (
            '08:20-09:50',
            '10:00-11:30',
            '11:45-13:15',
            '14:00-15:30',
            '15:45-17:15',
            '17:20-18:50',
            '18:55-20:25'
        )

        self.domain = 'https://www.vyatsu.ru'
        self.sch_url = self.domain + '/studentu-1/spravochnaya-informatsiya/teacher.html'
        self.teacher_url = self.domain + '/php/sotr_teacher_list/ajax_teacher.php'
        self.teacher_list = self._parse_teachers()
        self.available_deps = self._parse_available_deps()
        self.lesson_per_day = len(self.lessons_times)

    def _parse_available_deps(self):
        """Parse available departments(chair) vyatsu.ru"""

        response = urllib.request.urlopen(self.sch_url)
        data = response.read()
        text = data.decode('utf-8')
        soup = BeautifulSoup(text, 'html.parser')
        dep_list = [dep_elem.text.lstrip().replace('\t', '') for dep_elem in soup.find_all('div', {'class': 'kafPeriod'})]

        return list(set(dep_list))

    def update_teacher_list(self):
        """Update teacher list"""
        self.available_deps = self._parse_available_deps()
        self.teacher_list = self._parse_teachers()

    def find_teacher(self, query: str) -> str:
        """Find teacher full name

        Parameters
        ----------
        query : str
            Teacher name (surname, name, patron)
            query_ok = [
                'чистяков',
                'чистяков г а',
                'чистяков г.а.',
                'чистяков г. а.',
                'чистяков геннадий',
                'чистяков ген а',
                'чистяков ген ',
                'чистяков геннадий андреевич'
            ]

        Return
        ------
        List[Dict[str, str]]
            List with all cinceintence names.
            {'dep': 'Кафедра электронных вычислительных машин (ОРУ)', 'name': 'Чистяков Г.А.'}
        """
        query = query.strip().split(' ')[:3]
        familia = query[0]
        name = query[1:]
        if len(name) == 0:
            re_query = familia.capitalize() + ' '
#             re_query = familia.capitalize() # find beg coincentes
        elif len(name) == 1:
            if len(name[0]) < 2:
                re_query = familia.capitalize() + ' ' + name[0][0].capitalize() + '.'
            else:
                names = name[0].split('.')
                if len(names) > 1:
                    re_query = familia.capitalize() + ' ' + names[0][0].capitalize() + '.' \
                        + names[1][0].capitalize() + '.'
                else:
                    re_query = familia.capitalize() + ' ' + names[0][0].capitalize() + '.'
        else:
            re_query = familia.capitalize() + ' ' + name[0][0].capitalize() + '.' + \
                        name[1][0].capitalize() + '.'
#         print(re_query)
        coincidence = list(filter(lambda prep: re.search(re.escape(re_query), prep['name']), self.teacher_list))
        return coincidence

    def get_link(self, dep_name: str, target_date: datetime = datetime.now()) -> str:
        """Get link to department schedule.

        Parameters
        ----------
        dep_name : str
            Full department name
        target_date : datetime
            Schedule date

        Return
        ------
        str
            Link to schedule
        None
            If no schedule for this target date

        Raise
        -----
        ValueError
            Invalid department name

        """

        if dep_name not in self.available_deps:
            raise ValueError("Invalid department name")

        response = urllib.request.urlopen(self.sch_url)
        html_page = response.read().decode('utf-8')

        soup = BeautifulSoup(html_page, 'html.parser')
        kafPeriod_list = soup.find_all('div', text=re.compile(re.escape(dep_name)))  # pylint: disable=[invalid-name]

        for kafPeriod in kafPeriod_list:  # pylint: disable=[invalid-name]
            dates_list = (kafPeriod.parent.find('div', {'class': 'listPeriod'}).find_all('a'))
            for date in dates_list:
                elem_dates = re.findall(r'\d{2} \d{2} \d{4}', date.text.replace('\n', ''))
                if len(elem_dates) != 2:
                    continue
                period_begin = datetime.strptime(elem_dates[0], '%d %m %Y')
                period_end = datetime.strptime(elem_dates[1], '%d %m %Y')
                if period_begin.date() <= target_date.date() <= period_end.date():
                    return self.domain + date['href']

        return None

    def get_schedule_simple(self, teacher_name: str, target_date: datetime = datetime.now()):
        """Get schedule by teacher name and date.

        Parameters
        ----------
        teacher_name : str
            Teacher name if free format (surname, name, patron). See self.find_teacher.
        target_date : datetime
            Schedule date

        Return
        ------
        List[str]
            Schedule for target date
        None
            No schedule for target date

        Raise
        -----
        ValueError
            No coincentence
            More then 1 coincentence

        """

        teacher = self.find_teacher(teacher_name)
        if len(teacher) < 1:
            raise ValueError('No coincentence')
        if len(teacher) > 1:
            raise ValueError('Too many coincentences.')

        return self.get_schedule(teacher[0], target_date)

    def get_schedule(self, teacher, target_date: datetime = datetime.now()):
        """Get schedule by teacher data and date.

        Parameters
        ----------
        teacher : str
            Teacher dict format
        target_date : datetime
            Schedule date

        Return
        ------
        List[str]
            Schedule for target date
        None
            No schedule for target date

        Raise
        -----
        ValueError
            Invalid teacher data

        """

        if teacher not in self.teacher_list:
            print(teacher)
            raise ValueError('Invalid teacher data')
        sch_url = self.get_link(teacher['dep'], target_date)
        if sch_url is None:
            return None

        response = urllib.request.urlopen(sch_url)
        html_page = response.read().decode('utf-8')

        soup = BeautifulSoup(html_page, 'html.parser')
        table = soup.table
        rows = table.find_all('tr')
        cols = rows[1].find_all('td')

        # find teacher table index
        teacher_exist = False
        target_col_index = 0
        for col in cols:
            try:
                item_text = col.span.text
            except AttributeError as e:
                target_col_index += 1
                continue
            if item_text.replace(u'\xa0', u' ') == teacher['name']:
                teacher_exist = True
                break
            target_col_index += 1

        if not teacher_exist:
            return None

        # find target date
        start_td = None
        page_dates = table.find_all('td', text=re.compile(r'\d{2}\.\d{2}\.\d{2}'))
        for p in page_dates[1:]:  # exclude 'Обновление'
            cur_date = p.text.strip().replace(u'\xa0', u' ').split(' ')[1]
            if datetime.strptime(cur_date, '%d.%m.%y').date() == target_date.date():
                start_td = p
                break
        if start_td is None:
            return None  # empty schedule

        # get day sch for target teacher
        lessons = [''] * self.lesson_per_day
        rl = start_td.parent
        lessons[0] = list(rl.find_all('td'))[target_col_index].text
        for i, row in enumerate(rl.find_next_siblings()[:self.lesson_per_day-1]):
            lessons[i+1] = list(row.find_all('td'))[target_col_index-1].text

        return [self.lessons_times[i] + ' \n ' + les for i, les in enumerate(lessons) if les != '']

    def _parse_teachers(self) -> List[str]:
        """Parse teachers with departments(chair) vyatsu.ru"""

        teacher_list = []

        for dep_dict in self._get_links():

            response = urllib.request.urlopen(dep_dict['link'])
            data = response.read()
            text = data.decode('utf-8')
            soup = BeautifulSoup(text, 'html.parser')
            table = soup.table
            rows = table.find_all('tr', limit=2)  # get only 2 first row
            cols = rows[1].find_all('td')
            exclude_cols = ['', 'День', 'Интервал']
            for col in cols:
                try:
                    teacher_name = col.span.text
                except AttributeError as e:
                    continue
                teacher_name = teacher_name.replace(u'\xa0', u' ')
                if teacher_name not in exclude_cols:
                    teacher_list.append({'dep': dep_dict['dep'], 'name': teacher_name})
        return teacher_list

    def _get_links(self, target_date: datetime = datetime.now()) -> str:
        """Get links to deps schedule.

        Parameters
        ----------
        target_date : datetime
            Schedule date

        Return
        ------
        List[Dict[str(dep),str(link)]]
            Links list to deps schedule
        """

        links = []

        response = urllib.request.urlopen(self.sch_url)
        html_page = response.read().decode('utf-8')

        soup = BeautifulSoup(html_page, 'html.parser')
        kafPeriod_list = soup.find_all('div', {'class': 'kafPeriod'})

        for kafPeriod in kafPeriod_list:
            dates_list = (kafPeriod.parent.find('div', {'class': 'listPeriod'}).find_all('a'))
            for date in dates_list:
                elem_dates = re.findall(r'\d{2} \d{2} \d{4}', date.text.replace('\n', ''))
                if len(elem_dates) != 2:
                    continue
                period_begin = datetime.strptime(elem_dates[0], '%d %m %Y')
                period_end = datetime.strptime(elem_dates[1], '%d %m %Y')
                if period_begin.date() <= target_date.date() <= period_end.date():
                    links.append({'dep': kafPeriod.text.replace('\n', '').strip(),
                                 'link': self.domain + date['href']})
                    break

        return links


class StudentScheduleParser:
    """Parser for full-time students schedule for VyatSU (www.vyatsu.ru)"""

    def __init__(self):
        self.lessons_times = (
            '08:20-09:50',
            '10:00-11:30',
            '11:45-13:15',
            '14:00-15:30',
            '15:45-17:15',
            '17:20-18:50',
            '18:55-20:25'
        )

        self.domain = 'https://www.vyatsu.ru'
        self.main_url = self.domain + '/studentu-1/spravochnaya-informatsiya/raspisanie-zanyatiy-dlya-studentov.html'
        self.group_list = self._parse_available_groups()

    def update_groups_list(self):
        """Update group list from vyatsu.ru"""
        self.group_list = self._parse_available_groups()

    def _parse_available_groups(self) -> List[str]:
        """Parse available groups for full-time students from vyatsu.ru"""

        response = urllib.request.urlopen(self.main_url)
        data = response.read()
        text = data.decode('utf-8')
        group_regex = r'[а-яА-Я]{1,3}[бсма]-\d{4}-\d{2}-\d{2}'
        group_list = re.findall(group_regex, text)
        group_list = list(set(group_list))  # save only unique values

        return group_list

    def proceed_group_name(self, group_name: str, default_ed_level: str = 'б') -> str:
        """Canonization group name

        Parameters
        ----------
        group_name : str
            Group name in free format
        default_ed_level : str[1]
            Default education level. Example: 'б' 'с' 'м'

        Return
        -----
        str
            cononical group name like 'ИВТб-4301-03-00' or empty string

        """

        group_name = group_name.replace(' ', '-').replace('_', '-').lower()
        if group_name.find('-') < 0:
            return ''

        group_abb = re.search(r'[а-я]{1,3}(?:б-|с-|м-|а-|\d|-)', group_name)
        if group_abb is None:
            return ''

        group_abb = group_abb.group()[:-1]

        ed_level = bool(re.search(r'[а-я]{1}[бсма][-\d]', group_name))
        if not ed_level:
            group_abb = group_abb + default_ed_level

        group_num_long = re.findall(r'\d{4}', group_name)
        if len(group_num_long) > 1:
            return ''
        elif len(group_num_long) == 1:
            group_num_str = group_num_long[0]
        else:
            group_num = re.findall(r'\d{2}', group_name)
            if len(group_num) > 0:
                group_num_str = group_num[0][0] + r'\d{2}' + group_num[0][1]
            else:
                return ''

        assert len(group_num_str) in [4, 7]
        assert len(group_abb) > 1

        group_list_low = [group_name.lower() for group_name in self.group_list]
        for group_name_low, group_name in zip(group_list_low, self.group_list):
            if group_abb == group_name_low.split('-')[0]:
                rigth_group_num = re.search(group_num_str, group_name_low.split('-')[1])
                if rigth_group_num:
                    return group_name

        return ''

    def get_link(self, group_name: str, target_date: datetime = datetime.now()) -> str:
        """Get link to schedule in *.pdf by group name.

        Parameters
        ----------
        group_name : str
            Group name in free format
        target_date : datetime
            Schedule date

        Return
        ------
        str
            Link to schedule or empty stirng if no schedule for this target date

        Raise
        -----
        ValueError
            Invalid group name

        """
        cgroup_name = self.proceed_group_name(group_name)
        if cgroup_name == '':
            raise ValueError('Invalid group_name')

        request = urllib.request.urlopen(self.main_url)
        html_page = request.read().decode('utf8')

        soup = BeautifulSoup(html_page, 'html.parser')
        grpPeriod_list = soup.find_all('div', text=re.compile(cgroup_name))

        for grpPeriod in grpPeriod_list:
            dates_list = (grpPeriod.parent.find('div', {'class': 'listPeriod'}).find_all('a'))
            for date in dates_list:
                elem_dates = re.findall(r'\d{2} \d{2} \d{4}', date.text.replace('\n', ''))
                assert len(elem_dates) == 2
                period_begin = datetime.strptime(elem_dates[0], '%d %m %Y')
                period_end = datetime.strptime(elem_dates[1], '%d %m %Y')
                if period_begin <= target_date <= period_end:
                    return self.domain + date['href']

        return ''

    def get_schedule(self, group_name: str, target_date: datetime = datetime.now(), week: bool = False):
        """Get schedule dict by group name.

        Parameters
        ----------
        group_name : str
            Group name in free format
        target_date : datetime
            Schedule date
        week : bool = False
            If True return schedule for target day. Else return schedule for couple weeks.

        Return
        ------
        dict
            Group schedule in dict (week = True)
        List[str]
            Paths to schedule in images (week = True)
        List[str]
            Schedule for target date. (week = False)
        str
            Path to schedule in image for target date. (week = False)
        None
            No schedule for target date

        Raise
        -----
        ValueError
            Invalid group name

        """
        pdf_url = self.get_link(group_name, target_date)
        if pdf_url == '':
            return None

        try:
            schedule = self._parse_pdf(pdf_url)
            if week:
                return schedule
            return schedule[target_date.strftime('%d.%m.%y')]
        except Warning as e:
            print('can`t parse pdf file')   # TODO: add logger or remove messages
            #  print(e)
            schedule_images = self._pdf_to_image(pdf_url)
            if week:
                return schedule_images
            return schedule_images[target_date.strftime('%d.%m.%y')]

    def _pdf_to_image(self, pdf_url: str):
        """Convert pdf document to images

        Parameters
        ----------
        pdf_url : str
            Link to pdf document

        Return
        ------
        dict
            Schedule dict {str(date) : str(path to image)}
        """

        response = urllib.request.urlopen(pdf_url)
        data = response.read()
        doc = fitz.open(stream=data, filetype='pdf')

        zoom_x = 2.0
        zomm_y = 2.0
        mat = fitz.Matrix(zoom_x, zomm_y)

        images_path_dict = {}

        for i in range(doc.pageCount):
            page = doc.loadPage(i)
            str_list = page.getText("text").split('\n')
            dates = self._pdf_find_dates(str_list)

            pix = page.get_pixmap(matrix=mat, alpha=False)
            image_file_name = f"outfile{i}.png"

            pix.writePNG(image_file_name)
            images_path_dict.update([date_file for date_file in zip(dates, [image_file_name]*len(dates))])

        return images_path_dict

    def _parse_pdf(self, pdf_url: str):
        """Parse schedule pdf document

        Parameters
        ----------
        pdf_url : str
            Link to pdf document

        Return
        ------
        dict
            Schedule dict {str(date) : str(description)}

        Raise
        -----
        Warning
            Parse error
        """
        response = urllib.request.urlopen(pdf_url)
        data = response.read()
        doc = fitz.open(stream=data, filetype='pdf')

        sch_dict = {}

        for i in range(doc.pageCount):
            page = doc.loadPage(i)
            str_list = page.getText("text").split('\n')
            dates = self._pdf_find_dates(str_list)
            schedule = self._pdf_find_lessons(str_list)
            if len(dates) != len(schedule):
                raise Warning('Different len of dates and schedule')

            for day_index in range(len(schedule)):
                day_schedule = []
                for lesson_index in range(len(self.lessons_times)):
                    if schedule[day_index][lesson_index] != '':
                        lesson_description = self.lessons_times[lesson_index] + ' \n ' + schedule[day_index][lesson_index]
                        day_schedule.append(lesson_description)

                sch_dict.update([(dates[day_index], day_schedule)])

        return sch_dict

    def _pdf_find_dates(self, str_list: List[str]) -> List[str]:
        """Find dates in list of strings

        Parameters
        ----------
        str_list : List[str]
            List of parsed document strings

        Return
        ------
        List[str]
            List of sorted finded dates

        Raise
        -----
        Warning
            Can`t find date for week day
        """

        dates = []
        week_day_regex = 'понедельник|вторник|среда|четверг|пятница|суббота|воскресенье'
        for i, string in enumerate(str_list):
            # несколько дней недели в одной строке быть не могут
            res = re.match(week_day_regex, string)
            if res:
                date_regex = r'[0-3][0-9]\.[0-1][0-9]\.[0-9][0-9]'
                date = re.search(date_regex, string)
                if not date:
                    # find in next string
                    date = re.search(date_regex, str_list[i+1])
                if date:
                    dates.append(date.group())
                else:
                    raise Warning('Can`t find date for week day')

        dates.sort(key=lambda date: datetime.strptime(date, '%d.%m.%y'))
        return dates

    def _pdf_find_lessons(self, str_list):
        """Find lessons in list of strings

        Parameters
        ----------
        str_list : List[str]
            List of parsed document strings

        Return
        ------
        List[List[str]]
            List of List of finded lessons. str position index equal lesson num

        Raise
        -----
        Warning
            Invalid lessons order
        """

        week_day_regex = 'понедельник|вторник|среда|четверг|пятница|суббота|воскресенье'

        time_index_matrix = []
        for lesson_index in range(len(self.lessons_times)):
            cur_lesson_indexes = [i for i, string in enumerate(str_list) if string == self.lessons_times[lesson_index]]
            time_index_matrix.append(cur_lesson_indexes)

        for i in range(len(time_index_matrix[0])):
            for j in range(len(self.lessons_times) - 1):
                if time_index_matrix[j][i] > time_index_matrix[j+1][i]:
                    raise Warning('Invalid lesson order')

        beg_indexes = [i for i, string in enumerate(str_list) if string == self.lessons_times[0]]

        days = []

        for beg, end in list(zip(beg_indexes, beg_indexes[1:] + [len(str_list)])):
            les = [''] * len(self.lessons_times)
            cur_les = -1
            for i in range(beg, end):
                if str_list[i] == self.lessons_times[(cur_les+1) % len(self.lessons_times)]:
                    cur_les += 1
                elif str_list[i] == 'УТВЕРЖДАЮ' or re.match(week_day_regex, str_list[i]):
                    break
                else:
                    les[cur_les] = les[cur_les] + ' ' + str_list[i]
            days.append(les)

        return days
