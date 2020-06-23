#!/usr/bin/env python

class Reader:
    '''
    Checks disk for soup object and prints out the result.
    '''
    def show_file_content(self, URL) -> bool:
        import os
        file_name = URL.split('/')[-1] + '.soup'
        file_name = file_name

        file_loc = self.DIR_LOC + file_name
        if os.path.exists(self.DIR_LOC):
            if os.path.isfile(file_loc):
                with open(file_loc, 'r') as fin:
                    for line in fin.read().split('\n'):
                        print(line)
                return True
        else:
            return False


class Loader:
    '''
    Downloads pages about parliament of NRW and save as bs_objects.
    '''
    def download_bsObj(self, URL) -> bool:
        import requests
        import random
        from bs4 import BeautifulSoup
        from data.sourceBox import headers

        ix = random.randint(1, 6)

        file_name = URL.split('/')[-1] + '.soup'
        file_loc = './data/soup_objects/' + file_name

        try:
            req = requests.get(URL, headers[ix])
        except requests.exceptions.ConnectionError as e:
            print(e)
            print('ConnectionError, no download')
            return False

        bsObj = BeautifulSoup(req.text, 'lxml')
        with open(file_loc, 'w', encoding='utf-8') as fout:
            fout.write(str(bsObj))

        return True


class Menu(Loader, Reader):
    '''
    Menu options to choose which wikipage to display (or download first).
    '''
    def __init__(self):
        self.choices = {
                "1": self.show_directory,
                "2": self.cabinets_nrw,
                "3": self.specific_cabinet,
                "4": self.mdls_of_term,
                "5": self.quit
                }
        self.DIR_LOC = './data/soup_objects/'

    def display_menu(self) -> None:
        print("""
    Menu to display contents of a specific legislature and its MdLs

    1. Show content of ./data/soup_objects/
    2. Show wikipage of cabinets of NRW (downloads if not on disk)
    3. Show wikipage of a specific cabinet (downloads if not on disk)
    4. Show wikipage of MdLs of chosen legislature (downloads if not on disk)
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

    def show_directory(self) -> None:
        import os
        for directory in sorted(os.listdir(self.DIR_LOC)):
            print(directory)

    def show_file_content(self, URL):
        return Reader.show_file_content(self, URL)

    def download_bsObj(self, URL):
        return Loader.download_bsObj(self, URL)

    def choose_term(self) -> int:
        import sys

        self.choice = input('Which legislature period?')
        while True:
            try:
                if int(self.choice) in range(10, 18):
                    break
                else:
                    self.choice = input('Number between 10 and 17 or q/quit')
                    try:
                        if int(self.choice) in range(10, 18):
                            break
                        elif self.choice == 'q':
                            sys.exit()
                    except ValueError:
                        sys.exit()
            except ValueError:
                sys.exit()
        return self.choice

    def specific_cabinet(self) -> bool:
        CABINETS = ['Amelunxen I', 'Amelunxen II', 'Arnold I', 'Arnold II',
                    'Arnold III', 'Steinhoff', 'Meyers I', 'Meyers II',
                    'Meyers III', 'Kühn I', 'Kühn II', 'Kühn III', 'Rau I',
                    'Rau II', 'Rau III', 'Rau IV', 'Rau V', 'Clement I',
                    'Clement II', 'Steinbrück', 'Rüttgers', 'Kraft I',
                    'Kraft II', 'Laschet']
        print(CABINETS)
        URL = 'https://de.wikipedia.org/wiki/Kabinett_{}'
        choice = input('Which cabinet?')
        while True:
            if choice in CABINETS:
                URL = URL.format(choice)
                break
            elif choice == 'q':
                import sys
                sys.exit()
            else:
                print('No cabinet with that name.')
                choice = input('Which cabinet? (q to quit)')

        if self.show_file_content(URL):
            return True
        else:
            if self.download_bsObj(URL):
                self.show_file_content(URL)
                return True
            else:
                print('Could neither find file on disk nor download.')
                return False

    def cabinets_nrw(self) -> bool:
        URL = 'https://de.wikipedia.org/wiki/Landesregierung_von_Nordrhein-Westfalen'
        if self.wiki_file_size_change(URL):
            print('Wiki entry has changed.')
        else:
            print('Wiki entry is same as on disk.')

        if self.show_file_content(URL):
            return True
        else:
            if self.download_bsObj(URL):
                self.show_file_content(URL)
                return True
            else:
                print('Could neither find file on disk nor download.')
                return False

    def mdls_of_term(self) -> bool:
        term = self.choose_term()
        URL = f'https://de.wikipedia.org/wiki/Liste_der_Mitglieder_des_Landtages_Nordrhein-Westfalen_({term}._Wahlperiode)'
        print(URL)
        if self.show_file_content(URL):
            return True
        else:
            if self.download_bsObj(URL):
                self.show_file_content(URL)
                return True
            else:
                print('Could neither find file on disk nor download.')
                return False

    def wiki_file_size_change(self, URL) -> bool:
        import os
        file_name_disk = URL.split('/')[-1] + '.soup'
        file_loc_disk = self.DIR_LOC + file_name_disk
        if os.path.exists(self.DIR_LOC):
            if os.path.isfile(file_loc_disk):
                size_on_disk = os.path.getsize(file_loc_disk)

        import requests
        import random
        from bs4 import BeautifulSoup
        from data.sourceBox import headers

        ix = random.randint(1, 6)
        file_name_wiki = 'bsObj.tmp'
        file_loc_wiki = './data/soup_objects/' + file_name_wiki

        try:
            req = requests.get(URL, headers[ix])
        except requests.exceptions.ConnectionError as e:
            print(e)
            print('ConnectionError, no download')
            return False

        bsObj = BeautifulSoup(req.text, 'lxml')
        with open(file_loc_wiki, 'w', encoding='utf-8') as fout:
            fout.write(str(bsObj))

        size_wiki_tmp = os.path.getsize(file_loc_wiki)

        if size_wiki_tmp != size_on_disk:
            return True
        else:
            return False


if __name__ == '__main__':
    menu = Menu()
    menu.run()

