#!/usr/bin/env python
# coding=utf-8

import string
from bs4 import BeautifulSoup
from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode
from scraper_lib._extract_staedte import _make_list_of_cities
from scraper_lib.list_of_peertitles import peertitles
from scraper_lib._extract_vornamen import _get_vornamenListe
from person import MdL


class NoNameException(BaseException):
    pass


class NoPartyException(BaseException):
    pass


class Collector_MdLs:
    def __init__(self, legislature):
        self.legislature = legislature
        self.parties = ['CDU', 'SPD', 'FDP', 'Grüne', 'PIRATEN', 'AfD',
                        'GRÜNE', 'Linke']
        self.CITIES = _make_list_of_cities()

    def collect_tables(self) -> dict:
        '''
        Note: The layout of the wikipedia pages changed inbetween and I tried
        to parse the new content, however I still used the .soup objects I had
        previously downloaded, which obviously led to some confusion.
        Is it a good idea to compare the actual wiki page with the bsObj on my
        disk or is that overkill? Having always the latest wiki page as a
        reference will also make my parsing code obsolete at random times
        without necessarily gaining new information. On the other hand the
        latest change seems to have been motivated by standardizing the topic's
        appearance, so terms 14 - 17 look similar now and a lot of code can be
        spared.
        '''
        bsObj = self._get_bsObj()
        soup = BeautifulSoup(bsObj, 'lxml')
        tables = dict()
        for h2 in soup.find_all('h2'):
            try:
                if 'Ausgeschiedene' in h2.text:
                    table = h2.find_next('table')
                    tables['Ausgeschiedene Abgeordnete'] = table
                elif 'Abgeordnete' in h2.text:
                    table = h2.find_next('table')
                    tables['Abgeordnete'] = table
            except AttributeError:
                pass

        return tables

    def show_mdls(self) -> bool:
        import shelve
        import os

        PATH = './data/shelves/'
        db_name = f'nrw_mdls_term_{self.legislature}'

        if not os.path.isfile(PATH + db_name):
            print(f'No file {PATH + db_name}.')
            return False
        db = shelve.open(PATH + db_name)
        klist = list(db.keys())

        for i, key in enumerate(klist):
            print(str(i).rjust(3, ' '), key)
            print(db[key])
        db.close()

        return True

    def show_specific_MdL(self) -> bool:
        import shelve
        import os

        PATH = './data/shelves/'
        db_name = f'nrw_mdls_term_{self.legislature}'

        if not os.path.isfile(PATH + db_name):
            print(f'No file {PATH + db_name}.')
            return False
        with shelve.open(PATH + db_name) as db:
            klist = list(db.keys())
            while True:
                identifier = input('\nLast or first name, city? => ')
                if not identifier:
                    break
                for key in klist:
                    if identifier in key:
                        print(db[key])

        return True

    def show_MdLs_of_same_party(self) -> bool:
        import shelve
        import os

        PATH = './data/shelves/'
        db_name = f'nrw_mdls_term_{self.legislature}'
        parties = {'14': ['CDU', 'SPD', 'FDP', 'Grüne', 'Fraktionslos'],
                   '15': ['CDU', 'SPD', 'FDP', 'Grüne', 'Linke'],
                   '16': ['CDU', 'SPD', 'FDP', 'GRÜNE', 'PIRATEN'],
                   '17': ['CDU', 'SPD', 'FDP', 'GRÜNE', 'AfD', 'fraktionslos']}

        if not os.path.isfile(PATH + db_name):
            print(f'No file {PATH + db_name}.')
            return False
        with shelve.open(PATH + db_name) as db:
            klist = list(db.keys())
            while True:
                identifier = input('\nWhich party? => ')
                counter = 1
                if identifier not in parties[self.legislature]:
                    print(f'No party {identifier} in term {self.legislature}')
                    break
                for key in klist:
                    if identifier in db[key].parties:
                        print(counter, end=' ')
                        print(db[key])
                        counter += 1

        return True

    def extract_tables_14(self, tables) -> MdL:
        '''

        '''
        table = tables['Abgeordnete']
        for row in table.find_all('tr'):
            index_col = 0
            for col in row.find_all('td'):
                if index_col == 0:
                    col_text = col.text
                    if '!' in col_text:
                        col_text = col.text.split('!')[-1]
                    first_name, middle_name_1, middle_name_2,\
                        last_name, peer_preposition, peer_title =\
                        self._extract_names(col_text)
                elif index_col == 2:
                    party = self._make_party(col.text)
                elif index_col == 4:
                    electoral_ward =\
                        self.mk_electoral_ward(self.CITIES, col.text)
                index_col += 1
            try:
                mdl = MdL(self.legislature, first_name, last_name,
                          middle_name_1, middle_name_2,
                          electoral_ward=electoral_ward,
                          party=party,
                          peer_preposition=peer_preposition,
                          peer_title=peer_title)

                yield mdl
            except UnboundLocalError:
                pass

    def extract_tables_15(self, tables) -> MdL:
        table = tables['Abgeordnete']
        tbody = table.find_next('tbody')
        try:
            index_rows = 0
            for row in tbody.find_all('tr'):
                # print(f'index_rows: {index_rows} **************************')
                index_cols = 0
                for col in row.find_all('td'):
                    # print(f'col.contents {index_cols}: {col.contents}')
                    try:
                        for tag_a in col.find_all('a'):
                            if (self._is_first_name(tag_a.text) and
                                index_cols < 2):
                                first_name, middle_name_1, middle_name_2,\
                                    last_name, peer_preposition,\
                                    peer_title =\
                                    self._extract_names(tag_a.text)
                                continue
                            elif self._is_city(self.CITIES, tag_a.text):
                                electoral_ward = self.mk_electoral_ward(
                                    self.CITIES, tag_a.text)
                                continue
                            elif self._is_kreis(tag_a.text):
                                electoral_ward = tag_a.text
                                continue
                    except TypeError:
                        pass
                    except IndexError:
                        pass
                    try:
                        for tag_span in col.find_all('span'):
                            if self._is_first_name(tag_span.text) and index_cols < 2:
                                first_name, middle_name_1, middle_name_2,\
                                        last_name, peer_preposition,\
                                        peer_title = self._extract_names(
                                            tag_span.text)
                                continue
                            elif self._is_city(self.CITIES, tag_span.text):
                                electoral_ward = self.mk_electoral_ward(
                                    self.CITIES, tag_span.text)
                                continue
                            elif self._is_kreis(tag_span.text):
                                electoral_ward = self.mk_electoral_ward(
                                    self.CITIES, tag_span.text)
                                continue
                    except TypeError:
                        pass
                    except IndexError:
                        pass
                    try:
                        if col.contents[0].strip() in self.parties:
                            party = self._make_party(col.contents[0])
                    except TypeError:
                        pass
                    except IndexError:
                        pass
                    index_cols += 1
                try:
                    mdl = MdL(self.legislature, first_name, last_name,
                              middle_name_1, middle_name_2,
                              electoral_ward=electoral_ward,
                              party=party,
                              peer_preposition=peer_preposition,
                              peer_title=peer_title)
                    yield mdl
                except UnboundLocalError:
                    pass
                index_rows += 1
        except AttributeError:
            pass

    def extract_tables_16(self, tables) -> MdL:
        for key, table in tables.items():
            print(key)
            index_rows = 0
            for row in table.find_all('tr'):
                # print(index_rows)
                index_col = 0
                for col in row.find_all('td'):
                    # print(col)
                    if index_col == 1:
                        col_text = col.text
                        if '!' in col_text:
                            col_text = col.text.split('!')[-1]
                        first_name, middle_name_1, middle_name_2,\
                            last_name, peer_preposition, peer_title =\
                            self._extract_names(col_text)
                    elif index_col == 3:
                        party = self._make_party(col.text)
                    elif index_col == 4:
                        electoral_ward =\
                            self.mk_electoral_ward(self.CITIES, col.text)
                    index_col += 1
                index_rows += 1
                try:
                    mdl = MdL(self.legislature, first_name, last_name,
                              middle_name_1, middle_name_2,
                              electoral_ward=electoral_ward,
                              party=party,
                              peer_preposition=peer_preposition,
                              peer_title=peer_title)
                    print(mdl)
                    print()
                    yield mdl
                except UnboundLocalError:
                    pass
        import sys
        sys.exit()

    def _get_bsObj(self) -> str:
        URL = f'https://de.wikipedia.org/wiki/Liste_der_Mitglieder_des_Landtages_Nordrhein-Westfalen_({self.legislature}._Wahlperiode)'
        file_name = URL.split('/')[-1] + '.soup'
        FILE_LOC = './data/soup_objects/' + file_name

        try:
            with open(FILE_LOC, "r", encoding="utf-8") as fin:
                bsObj = fin.read()
        except FileNotFoundError as e:
            print(e)
            from wiki_scraper import Loader
            loader = Loader()
            if loader.download_bsObj(URL):
                bsObj = self._get_bsObj()
            else:
                print('didnt work')

        return bsObj

    def _standardize_words(self, text) -> list:
        words = text.split(' ')
        words = list(filter(None, words))
        words = [word.strip() for word in words]
        try:
            words = [word[:-1] if word[-1] in string.punctuation else
                     word for word in words]
            words = [word[1:] if word[0] in string.punctuation else
                     word for word in words]
        except IndexError:
            return None

        return words

    def _is_city(self, CITIES, text) -> bool:
        words = self._standardize_words(text)
        word = words[0]
        if word in CITIES:
            return True
        elif '-' in word:
            words = word.split('-')
            word_1 = words[0]
            word_2 = words[1]
            if word_1 in CITIES or word_2 in CITIES:
                return True
            if len(words) == 3:
                word_3 = words[2]
                if word_3 in CITIES:
                    return True
        return False

    def mk_electoral_ward(self, CITIES, text) -> str:
        words = self._standardize_words(text)
        if not words:
            electoral_ward = 'ew'
            return electoral_ward
        if words[0] == 'Landesliste':
            if len(words) == 1:
                electoral_ward = 'ew'
                return electoral_ward
            elif len(words) > 1:
                words = words[1:]
        electoral_ward = ' '.join(words)
        return electoral_ward

    def _make_party(self, text) -> str:
        words = self._standardize_words(text)
        if len(words) > 1:
            raise NoPartyException
        else:
            party = words[0]
        return party

    def _is_kreis(self, word) -> bool:
        if 'Kreis' in word:
            return True
        elif 'kreis' in word:
            return True
        return False

    def _is_first_name(self, text) -> bool:
        '''
        It would be nice if unknown first names could be added to the list of
        first names, but this would blow up this function's purpose.
        '''
        first_names = _get_vornamenListe()

        words = self._standardize_words(text)
        word = words[0]
        if word in first_names:
            return True
        elif '-' in word:
            if word.split('-')[0] in first_names:
                return True
            elif word.split('-')[-1] in first_names:
                return True
        return False

    def _is_middle_name(self, words) -> bool:
        word = words.split(' ')[1].strip()
        if len(words) == 3 and self._is_first_name(word):
            return True
        return False

    def _is_preposition(self, word) -> bool:
        if word in ['von', 'van', 'de', 'auf', 'der', 'und', 'zu', 'den', 'dos']:
            return True
        return False

    def _extract_names(self, text):
        words = self._standardize_words(text)
        # print('words in extract_names:', words)
        middle_name_1 = None
        middle_name_2 = None
        preposition = None
        peer_title = None
        word_1 = words[0]
        word_2 = words[1]

        if len(words) == 2:
            if self._is_first_name(word_1):
                first_name = word_1
                last_name = word_2
            else:
                raise NoNameException
        elif len(words) == 3:
            word_3 = words[-1]
            if self._is_first_name(word_1) and self._is_first_name(word_2):
                first_name = word_1
                middle_name_1 = word_2
                last_name = word_3
            elif self._is_preposition(word_2):
                first_name = word_1
                preposition = word_2
                last_name = word_3
            elif word_1 in peertitles:
                peer_title = word_1
                first_name = word_2
                last_name = word_3
            elif word_2 in peertitles:
                first_name = word_1
                peer_title = word_2
                last_name = word_3
            elif '-' in word_2:
                first_name = word_1
                words_2 = word_2.split('-')
                if words_2[-1] in ['von', 'van', 'de', 'zu']:
                    last_name = ' '.join([word_2, word_3])
            elif word_3 == 'last_word':
                first_name = word_1
                last_name = word_2
            else:
                first_name = word_1
                last_name = ' '.join([word_2, word_3])
        elif len(words) == 4:
            word_3 = words[2]
            if word_3[0] in string.punctuation:
                word_3 = word_3[1:]
            word_4 = words[-1]
            if self._is_first_name(word_1):
                first_name = word_1
            elif word_1 in peertitles:
                peer_title = word_1
                if self._is_first_name(word_2):
                    first_name = word_2
            if word_2 in peertitles:
                peer_title = word_2
                if self._is_preposition(word_3):
                    preposition = word_3
                    last_name = word_4
                else:
                    last_name = ' '.join([word_3, word_4])
            elif self._is_first_name(word_2):
                middle_name_1 = word_2
                if self._is_first_name(word_3):
                    middle_name_2 = word_3
                    last_name = word_4
                elif self._is_preposition(word_3):
                    preposition = word_3
                    last_name = word_4
                else:
                    last_name = ' '.join([word_3, word_4])
            elif self._is_preposition(word_2):
                if self._is_preposition(word_3):
                    preposition = ' '.join([word_2, word_3])
                    last_name = word_4
                elif '-' in word_3:
                    words_3 = word_3.split('-')
                    if words_3[-1] in ['von', 'van', 'de', 'zu']:
                        last_name = ' '.join([word_3, word_4])
                else:
                    preposition = word_2
                    last_name = ' '.join([word_3, word_4])
            elif not self._is_preposition(word_2) and self._is_preposition(word_3):
                preposition = word_3
                last_name = word_4

        return first_name, middle_name_1, middle_name_2, last_name, preposition, peer_title


class Menu(Collector_MdLs):
    '''
    Menu options to choose which wikipage to display (or download first).
    '''
    def __init__(self):
        self.choices = {
                "0": self.chose_term,
                "1": self.show_mdls,
                "2": self.show_specific_MdL,
                "3": self.show_MdLs_of_same_party,
                "4": self.shelve_mdls,
                "5": self.quit
                }
        self.DIR_LOC = './data/soup_objects/'
        self.parties = ['CDU', 'SPD', 'FDP', 'Grüne', 'PIRATEN', 'AfD',
                        'GRÜNE', 'Linke']
        self.CITIES = _make_list_of_cities()

    def display_menu(self) -> None:
        print("""
    Menu to display contents of a specific legislature and its MdLs

    0. Which legislature?
    1. Show all MdLs of chosen term
    2. Show MdLs of chosen term with common city or name
    3. Show MdLs of chosen term with common party
    4. Shelve MdLs of chosen term
    5. Quit
    """)

    def run(self) -> None:
        '''Display menu and respond to choices'''
        while True:
            self.display_menu()
            choice = input('Enter an option: ')
            action = self.choices.get(choice)
            if action:
                action()
            else:
                print('{} is not a valid choice'.format(choice))

    def quit(self) -> None:
        import sys
        sys.exit()

    def chose_term(self):
        self.legislature = ask_for_wahlperiode()

    def show_mdls(self) -> bool:
        Collector_MdLs.show_mdls(self)

    def show_specific_MdL(self) -> bool:
        Collector_MdLs.show_specific_MdL(self)

    def show_MdLs_of_common_party(self):
        Collector_MdLs.show_MdLs_of_same_party(self)

    def collect_tables(self) -> dict:
        tables = Collector_MdLs.collect_tables(self)
        return tables

    def _create_dict(self):
        func_dict = {'14': Collector_MdLs.extract_tables_14,
                     '15': Collector_MdLs.extract_tables_15,
                     '16': Collector_MdLs.extract_tables_16,
                     '17': Collector_MdLs.extract_tables_16}
        return func_dict

    def extract_tables_14(self, tables) -> MdL:
        for mdl in Collector_MdLs.extract_tables_14(self, tables):
            yield mdl

    def extract_tables_15(self, tables) -> MdL:
        for mdl in Collector_MdLs.extract_tables_15(self, tables):
            yield mdl

    def extract_tables_16(self, tables) -> MdL:
        for mdl in Collector_MdLs.extract_tables_16(self, tables):
            yield mdl

    def shelve_mdls(self) -> None:
        import shelve
        import os

        tables = self.collect_tables()
        PATH = './data/shelves/'
        if not os.path.exists(PATH):
            os.mkdir(PATH)
        filename = f'nrw_mdls_term_{self.legislature}'
        print(filename)
        db = shelve.open(PATH + filename)
        func_dict = self._create_dict()
        extract_tables = func_dict[self.legislature]

        for mdl in extract_tables(self, tables):
            key = f'{mdl.last_name}_{mdl.first_name}_{mdl.electoral_ward}_{mdl.legislature}'
            print(key)
            print(mdl)
            db[key] = mdl
        db.close()
        print(f'Shelved MdLs for term {self.legislature}')


if __name__ == "__main__":
    menu = Menu()
    menu.run()
