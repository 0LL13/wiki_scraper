#!/usr/bin/env python

import sys
from dataclasses import dataclass, field
from inspect import signature
from typing import List


# https://gist.github.com/jhazelwo/86124774833c6ab8f973323cb9c7e251
class QuietError(Exception):
    pass


def quiet_hook(kind, message, traceback):
    if QuietError in kind.__bases__:
        print(f'{kind.__name__} : {message}')
    else:
        sys.__excepthook__(kind, message, traceback)


sys.excepthook = quiet_hook


class NotInRange(QuietError):
    pass


class AttrDisplay:
    '''
    Mark Lutz, Programming Python
    Provides an inheritable display overload method that shows instances
    with their class names and a name=value pair for each attribute stored
    on the instance itself (but not attrs inherited from its classes). Can
    be mixed into any class, and will work on any instance.
    '''
    def gatherAttrs(self) -> list:
        attrs = []
        for key in sorted(self.__dict__):
            if self.__dict__[key] and self.__dict__[key] not in ['unknown',
                                                                 'ew']:
                attrs.append(f'{key}={getattr(self, key)}')
        return attrs

    def __str__(self) -> str:
        comp_repr = (f'{self.__class__.__name__}:\n' +
                     '\n'.join(str(attr) for attr in self.gatherAttrs())+'\n')
        return comp_repr


@dataclass
class _Name_default(AttrDisplay):
    middle_name_1: str = field(default=None)
    middle_name_2: str = field(default=None)
    maiden_name: str = field(default=None)


@dataclass
class _Name_base(AttrDisplay):
    first_name: str
    last_name: str


@dataclass
class Name(_Name_default, _Name_base, AttrDisplay):
    pass


@dataclass
class _Peertitle_default:
    peer_title: str = field(default=None)
    peer_preposition: str = field(default=None)


@dataclass
class Noble(_Peertitle_default, Name, AttrDisplay):
    pass


@dataclass
class _Academic_title_default:
    academic_title: str = field(default=None)

    def title(self, academic_title) -> str:
        if academic_title:
            if '.D' in academic_title:
                academic_title =\
                    '. '.join(c for c in academic_title.split('.'))
            if academic_title.endswith('Dr'):
                academic_title = academic_title[:-2] + 'Dr.'
            while '  ' in academic_title:
                academic_title = academic_title.replace('  ', ' ')
            return academic_title
        return academic_title


@dataclass
class Academic(_Academic_title_default, Name, AttrDisplay):
    def __post_init__(self):
        self.academic_title = self.title(self.academic_title)


@dataclass
class _Person_default:
    gender: str = field(default='unknown')

    def get_gender(self, salutation) -> str:
        if self.gender != 'unknown':
            return self.gender
        elif salutation == 'Herr':
            self.gender = 'male'
            return self.gender
        elif salutation == 'Frau':
            self.gender = 'female'
            return self.gender
        else:
            return self.gender


@dataclass
class Person(_Peertitle_default, _Academic_title_default, _Person_default,
             Name, AttrDisplay):
    def __post_init__(self):
        Academic.__post_init__(self)


@dataclass
class _Politician_default:
    electoral_ward: str = field(default='ew')
    ward_no: int = field(default='None')
    voter_count: int = field(default='None')
    minister: str = field(default=None)
    offices: List[str] = field(default_factory=lambda: [])
    party: str = field(default=None)
    parties: List[str] = field(default_factory=lambda: [])

    def ward_details(self):
        if self.electoral_ward not in ['ew', 'Landesliste']:
            from bs4 import BeautifulSoup
            import requests
            if self.electoral_ward == 'Kreis Aachen I':
                self.electoral_ward = 'Aachen III'
            elif self.electoral_ward == 'Hochsauerlandkreis II – Soest III':
                self.electoral_ward = 'Hochsauerlandkreis II'
            elif self.electoral_ward == 'Kreis Aachen II':
                if self.last_name in ['Wirtz', 'Weidenhaupt']:
                    self.electoral_ward = 'Aachen IV'

            URL_base = 'https://de.wikipedia.org/wiki/Landtagswahlkreis_{}'
            URL = URL_base.format(self.electoral_ward)
            req = requests.get(URL)
            bsObj = BeautifulSoup(req.text, 'lxml')
            table = bsObj.find(class_='infobox float-right toptextcells')
            try:
                for td in table.find_all('td'):
                    if 'Wahlkreisnummer' in td.text:
                        ward_no = td.find_next().text.strip()
                        ward_no = ward_no.split(' ')[0]
                        self.ward_no = int(ward_no)
                    elif 'Wahlberechtigte' in td.text:
                        voter_count = td.find_next().text.strip()
                        if ' ' in voter_count:
                            voter_count = ''.join(voter_count.split(' '))
                        elif '.' in voter_count:
                            voter_count = ''.join(voter_count.split('.'))
                        if voter_count[-1] == ']':
                            voter_count = voter_count[:-3]
                        self.voter_count = int(voter_count)
            except (AttributeError, ValueError) as e:
                print(e)
                print(td)
                print(self.electoral_ward)
                input()
                sys.exit()


@dataclass
class Politician(_Peertitle_default, _Academic_title_default, _Person_default,
                 _Politician_default, Name, AttrDisplay):

    def party_affil(self, party):
        if party not in self.parties:
            self.parties.append(party)

    def __post_init__(self):
        Academic.__post_init__(self)
        if self.party and self.party not in self.parties:
            self.parties.append(self.party)
        if self.minister:
            self.offices.append(self.minister)
        if self.electoral_ward not in ['ew', 'Landesliste']:
            _Politician_default.ward_details(self)


@dataclass
class Contri_single(AttrDisplay):
    # instances of Contri_single should be named after the page_from and
    # page_to numbers combined with the type of contribution, and if there is
    # an instance with that name already an extension like "_2" or "_3" will
    # need to be added; has to start with a letter
    # example: contri_2311_2312_ZwFr

    # >protocol_nr< consists of the legislature and the session's count, so the
    # fifth session of the 15th term would be 15/5
    protocol_nr: str
    # >pages< are the pages that will point to the PDF document, usually the
    # pages cover the whole session or at least more than the part where the
    # contribution can be found
    pages: str
    # >page_from< and >page_to< are the PDF doc's pages where to find the
    # contribution
    page_from: str
    page_to: str
    # >type_of_contri< being the type of contribution like 'ZwFr'(if question)
    # or 'PersErkl' (if a personal statement) or 'speech' etc.
    type_of_contri: str
    # >party< the MdL's party affiliation (or 'fraktionslos' if without party)
    party: str
    # >URL_salt< contains a combination whose meaning I didn't figure out
    # (the rest can be combined with number of term, page numbers etc.
    # example: '%2F'
    URL_salt: str
    # >content< the actual question or speech that contributed to the session
    content: str

# @dataclass
# class Contris_session:
    # instances of Contris_session should be named after the session's number
    # (i.e. the 132 of the protocol_nr 16/132) and the MdL's key
    # example: WÜST_HENDRIK_ew_16_132

    # contris_session is a list of contributions (class Contri_single)
#    contris_session : List = field(default_factory=lambda : [])

# @dataclass
# class Contris_term(AttrDisplay):
    # instances of Contris_term should be named after the MdL's key and sth.
    # like "_all_contributions"
    # example: WÜST_HENDRIK_ew_16_all_contributions

    # contris_term is a list of instances of contris_session


@dataclass
class Speaker_default(_Peertitle_default, _Academic_title_default,
                      AttrDisplay):
    academic_title: str = field(default=None)
    parl_pres: str = field(default=None)
    parl_vicePres: str = field(default=None)
    minister: str = field(default=None)
    type_of_contri: str = field(default=None)

    def __post_init__(self):
        Academic.__post_init__(self)


@dataclass
class Speaker_base(AttrDisplay):
    last_name: str
    party: str


@dataclass
class Speaker(Speaker_default, Speaker_base, AttrDisplay):
    pass


@dataclass
class Session(AttrDisplay):
    # all the details concerning a parliament's sessions
    import datetime
    cal_date: datetime.date
    protocol_nr: str


@dataclass
class Session_sub(Session, AttrDisplay):
    # details of a session's subsession focussing on a specific topic
    url_subsession: str
    topic: str
    # >details< example: "2. Lesung zu GesEntw LRg Drs 17/4668"
    details: str
    page_from: str
    page_to: str
    result: str
    classification: str
    tags: List[str] = field(default_factory=lambda: [])
    lineup: List[Speaker] = field(default_factory=lambda: [])


@dataclass
class _MdL_default:
    parl_pres: bool = field(default=False)
    parl_vicePres: bool = field(default=False)


@dataclass
class _MdL_base:
    legislature: int


@dataclass
class MdL(_MdL_default, Politician, _MdL_base, AttrDisplay):
    def __post_init__(self):
        if int(self.legislature) not in range(10, 21):
            raise NotInRange('Number for legislature not in range')
        Academic.__post_init__(self)
        Politician.__post_init__(self)
        if self.electoral_ward not in ['ew', 'Landesliste']:
            _Politician_default.ward_details(self)


if __name__ == '__main__':

    first_name = 'Olaf'
    last_name = 'Scholz'
    middle_name_1 = 'Johan'
    middle_name_2 = 'Fritz'
    academic_title = 'Prof.Dr.   Dr'
    peer_title = 'Freiherr'
    peer_preposition = 'von'
    electoral_ward = 'Gütersloh III'
    party = 'SPD'
    legislature = 19
    gender = 'male'
    c1 = Contri_single('142', '15014|15023', '15018', '15019', 'speech',
                       'GRÜNE', '%2F', 'Herr ...')
    c2 = Contri_single('141', '14853|14862', '14858', '14858', 'ZwFr', 'GRÜNE',
                       '%2F', 'Vielen ...')

    session_63 = Session('14.08.2020', '63')

    speaker_1 = Speaker(last_name, party, academic_title)
    speaker_2 = Speaker('Eisenbart', 'CDU', 'Dr.', peer_preposition='von')

    print('speaker_1')
    print(speaker_1)
    print('speaker_2')
    print(speaker_2)
    print(signature(Speaker))

    print()
    print('-'*10)

    print(session_63)
    print(session_63.cal_date)
    print(session_63.protocol_nr)

    subsession_63_1 = Session_sub('14.08.2020',
                                  '63',
                                  'https://www.landtag.nrw...',
                                  'Gesetz über ...',
                                  'Beschluss: ...',
                                  '38',
                                  '45',
                                  'bla bla ...',
                                  'Hochschulwesen',
                                  ['Hochschulgesetz', 'Hochschulrecht'],
                                  [speaker_1, speaker_2])
    print(subsession_63_1)
    print(signature(Session_sub))
    print('-'*10)

    print(signature(Contri_single))
    print(c1)
    print(c1.protocol_nr)
    print('-'*10)

    n = Name(first_name, last_name, middle_name_1)
    # print(Name.__mro__)
    print(signature(Name))
    print(n)
    print('-'*10)

    a = Academic(
            first_name,
            last_name,
            academic_title=academic_title)
    # print(Academic.__mro__)
    print(signature(Academic))
    print(a)
    print('-'*10)

    graf = Noble(
            first_name,
            last_name,
            peer_preposition=peer_preposition, peer_title=peer_title)
    # print(Noble.__mro__)
    print(signature(Noble))
    print(graf)
    print('-'*10)

    p = Person(
            first_name,
            last_name,
            gender=gender, middle_name_1=middle_name_1, peer_title=peer_title,
            academic_title=academic_title, peer_preposition=peer_preposition)
    # print(Person.__mro__)
    print(signature(Person))
    print(p)
    print('-'*10)

    pol = Politician(
            first_name,
            last_name,
            middle_name_1=middle_name_1, gender=gender, peer_title=peer_title,
            academic_title=academic_title, party=party, minister='IM',
            electoral_ward=electoral_ward)
    # print(Politician.__mro__)
    print(signature(Politician))
    print(pol)
    print('-'*10)

    print(signature(MdL))
    mdl = MdL(
            legislature,
            first_name,
            last_name,
            middle_name_1=middle_name_1,
            middle_name_2=middle_name_2,
            gender=gender,
            peer_preposition='dos',
            peer_title=peer_title,
            academic_title=academic_title,
            party='fraktionslos',
            electoral_ward=electoral_ward,
            minister='JM')

    print(mdl)
    mdl.party_affil('LINKE')
    print(mdl)

    print(mdl.gender)
    mdl.get_gender('Herr')
    print(mdl.gender)
    mdl.get_gender('Frau')
    print(mdl.gender)
