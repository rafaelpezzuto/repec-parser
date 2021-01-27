import bs4
import os
import re
import sys


REGEX_YEAR = r'\d{4}'
ARTIFICIAL_NODES_COUNTER = 1


def save(data, path):
    with open(path, 'w') as f:
        if 'nodes' in path:
            f.write('Id\tName\n')
        elif 'edges' in path:
            f.write('Source\tTarget\tYear\tInstitution\n')

        for d in data:
            f.write(d + '\n')


def get_cleaned_nodes_edges(raw):
    nodes = []
    edges = []

    for k, v in raw.items():
        source_code = k
        source_name = v.get('name', '')

        nodes.append('\t'.join([source_code, source_name]))

        for vi in v.get('advisors', []):
            target_code = vi
            if len(v.get('graduate_info', [])) > 0:
                target_institution = v.get('graduate_info')[0][0]
                target_year = v.get('graduate_info')[0][-1]

                edges.append('\t'.join([source_code, target_code, target_year, target_institution]))

    return nodes, edges


def generate_artificial_code():
    global ARTIFICIAL_NODES_COUNTER

    artcode = 'art' + str(ARTIFICIAL_NODES_COUNTER)
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
    return stus


def _extract_advisors(raw):
    advs = []

    for li in raw.find_all('li'):
        adv_code = '-1'

        li_a = li.find('a')
        if li_a:
            li_a_href = li_a.get('href')
            if li_a_href:
                adv_code = _extract_author_code(li_a_href, 'url')

        if adv_code == '-1':
            adv_code = generate_artificial_code()

        advs.append(adv_code)

    return advs


def _extract_author_name(raw):
    return raw.replace('RePEc Genealogy page for ', '').replace('  ', ' ').strip()


def _extract_author_code(raw, mode='default'):
    if mode == 'default':
        return raw.split('.')[0].strip()
    elif mode == 'url':
        return _extract_author_code(raw.split('/')[-1])


def parse(path):
    raw_graph = {}

    files = sorted(os.listdir(path))
    total = len(files)
    for ind, fi in enumerate(files):
        print('\rParsing %d of %d... ' % (ind, total), end='')
        with open(os.path.join(path, fi)) as fr:
            fr_soup = bs4.BeautifulSoup(fr, 'html.parser')

            author_name = _extract_author_name(fr_soup.find('h1').text)
            author_code = _extract_author_code(fi)

            related = fr_soup.find_all('h2')

            for rel in related:
                if rel.text == 'Graduate studies':
                    graduate_graduate_info = _extract_graduate_info(rel.find_next())
                elif rel.text == 'Advisor':
                    advisors = _extract_advisors(rel.find_next())
                elif rel.text == 'Students':
                    students = _extract_students(rel.find_next())

            raw_graph[author_code] = {'name': author_name,
                                      'advisors': advisors,
                                      'graduate_info': graduate_graduate_info,
                                      'students': students}
    print('Done')
    return raw_graph


if __name__ == '__main__':
    raw_graph = parse(sys.argv[1])
    nodes, edges = get_cleaned_nodes_edges(raw_graph)
    save(nodes, 'nodes.tsv')
    save(edges, 'edges.tsv')
