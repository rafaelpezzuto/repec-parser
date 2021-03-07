import argparse

import bs4
import os
import re
import sys


REGEX_YEAR = r'\d{4}'
REGEX_STUDENT_NAME = r'\d{4}(.*)\('
REGEX_CODE = r'\/(\w*)\.html'

ARTIFICIAL_NODES_COUNTER = 1


def save(data, path):
    with open(path, 'w') as f:
        if 'nodes' in path:
            f.write('Id\tLabel\n')
        elif 'edges' in path:
            f.write('Source\tTarget\tYear\tInstitution\n')

        for d in data:
            f.write(d + '\n')


def get_cleaned_nodes_edges(raw):
    nodes = []
    edges = []

    for k, v in raw.items():
        profile_researcher_code = k
        profile_researcher_name = v.get('name', '')

        nodes.append('\t'.join([profile_researcher_code, profile_researcher_name]))

        for vi in v.get('advisors', []):
            advisor_code = vi
            if len(v.get('graduate_info', [])) > 0:
                formation_institution = v.get('graduate_info')[0][0]
                formation_year = v.get('graduate_info')[0][-1]

                edges.append('\t'.join([advisor_code, profile_researcher_code, formation_year, formation_institution, 'padv']))

        for vi in v.get('students', []):
            stu_code, stu_name, stu_year, stu_institution = vi
            edges.append('\t'.join([profile_researcher_code, stu_code, stu_year, stu_institution, 'pstu']))

    print('cleaning and deduplicating edges...')
    edges = deduplicate_edges(edges)

    return nodes, edges


def generate_artificial_code(mode: str):
    global ARTIFICIAL_NODES_COUNTER

    if mode == 'advisor':
        artcode = 'adv' + str(ARTIFICIAL_NODES_COUNTER)
    elif mode == 'student':
        artcode = 'stu' + str(ARTIFICIAL_NODES_COUNTER)

    ARTIFICIAL_NODES_COUNTER += 1

    return artcode


def _extract_graduate_info(raw):
    gras = []

    institution_name = ''
    year = ''

    if raw.name == 'a':
        institution_name = raw.text

    possible_year = raw.next_sibling
    if isinstance(possible_year, str):
        matched_year = re.search(REGEX_YEAR, possible_year)
        if matched_year:
            year = matched_year.group()

    if institution_name or year:
        gras.append((institution_name, year))

    return gras


def _extract_students(raw):
    stus = []

    for c in raw.children:
        stu_institution = _find_institution(c.next)
        for li in c.find_all('li'):
            stu_year, stu_name, stu_code = _find_student_data(li)

            if stu_code == '-1':
                stu_code = generate_artificial_code('student')

            stus.append((stu_code, stu_name, stu_year, stu_institution))

        return stus


def _find_author_code(li):
    code = '-1'

    li_a = li.find('a')
    if li_a:
        li_a_href = li_a.get('href')
        if li_a_href:
            code = _extract_author_code(li_a_href, 'url')

    return code


def _find_student_data(li):
    year = ''
    name = ''
    code = ''

    if isinstance(li.next, str):
        matched_year = re.search(REGEX_YEAR, li.next)
        if matched_year:
            year = matched_year.group()

        matched_name = re.search(REGEX_STUDENT_NAME, li.next)
        if matched_name:
            name = matched_name.groups()[0].replace('  ', ' ').strip()

        li_a = li.find('a')
        if li_a:
            li_a_href = li_a.get('href')
            if li_a_href:
                matched_code = re.search(REGEX_CODE, li.find('a').get('href'))
                if matched_code:
                    code = matched_code.groups()[0].strip()

    return year, name, code


def _find_institution(tag):
    inst = ''

    if isinstance(tag, bs4.element.Tag):
        if tag.name == 'a':
            if 'data' in tag.get('href', ''):
                inst = tag.text
    return inst


def _extract_advisors(raw):
    advs = []

    for li in raw.find_all('li'):
        adv_code = _find_author_code(li)
        if adv_code == '-1':
            adv_code = generate_artificial_code('advisor')
        advs.append(adv_code)

    return advs


def _extract_author_name(raw):
    return raw.replace('RePEc Genealogy page for ', '').replace('  ', ' ').strip()


def _extract_author_code(raw, mode='default'):
    if mode == 'default':
        return raw.split('.')[0].strip()
    elif mode == 'url':
        return _extract_author_code(raw.split('/')[-1])


def deduplicate_edges(edges: list):
    edges_keys = {}

    for e in edges:
        els = e.split('\t')
        source = els[0]
        target = els[1]
        year = els[2]
        institution = els[3]

        if source and target and year:
            edge_key = '-'.join(sorted([source, target]))

            if edge_key not in edges_keys:
                edges_keys[edge_key] = set()

            edges_keys[edge_key].add('\t'.join([source, target, year, institution]))

    ddp_edges = []
    for k, v in edges_keys.items():
        if len(v) > 2:
            print('\n'.join(v))

        for vi in v:
            ddp_edges.append(vi)

    return sorted(ddp_edges)


def parse_file(path_file):
    parsed_data = []

    with open(os.path.join(path_file)) as f:
        soup = bs4.BeautifulSoup(f, 'html.parser')



    return parsed_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d',
        required=True,
        dest='dir_ideas'
    )
    params = parser.parse_args()

    if not os.path.exists(params.dir_ideas):
        print('Caminho %s não existe' % params.dir_ideas)
        exit(1)

    files = [os.path.join(params.dir_ideas, f) for f in os.listdir(params.dir_ideas)]

    ideas = []
    for f in files:
        if 'pzy8' in f:
            pf = parse_file(f)
            if pf:
                ideas.append(pf)

    save(ideas, 'biblio_ideas.tsv')


if __name__ == '__main__':
    main()
