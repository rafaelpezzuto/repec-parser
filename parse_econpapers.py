import argparse
import bs4
import os
import re


REGEX_TOTAL_CITATIONS = r'.*View citations \((.*)\)'
REGEX_CITING_DOCS_URL = r'.*scripts/showcites.pf\?h=(.*)'
REGEX_CITING_DOC_YEAR = r'(\d{4})|$'
CITING_DOCS = {}


def _extract_author_code(path_file):
    head, tail = os.path.split(path_file)
    return tail.split('.')[0]


def _extract_author_name(soup):
    h1_details_about = soup.find('h1')
    if h1_details_about:
        return h1_details_about.text.replace('Details about ', '')
    return ''


def _extract_journal_articles(soup):
    articles = {}

    h2_journal_articles = _find_journal_article_header(soup)

    if h2_journal_articles:
        h3_year = h2_journal_articles.find_next('h3')

        while True:
            if h3_year:
                if h3_year.text not in articles:
                    articles[h3_year.text] = []
                articles[h3_year.text].extend(_extract_articles_for_year(h3_year))

            if _is_h2_section_end(h3_year):
                break
            else:
                h3_year = h3_year.find_next('h3')

    return articles


def _find_journal_article_header(soup):
    for i in soup.find_all('h2'):
        if 'Journal Articles' in i.text:
            return i


def _is_h2_section_end(h3_year):
    sib = h3_year

    for i in range(4):
        try:
            sib = sib.next_sibling
            if sib and sib.name == 'h2':
                return True
        except AttributeError:
            return True

    return False


def _extract_articles_for_year(h3_year):
    year_articles = []

    ol_articles = h3_year.find_next('ol')
    for li in ol_articles.find_all('li'):
        art = _extract_article_data(li)
        if art:
            year_articles.append(art)

    return year_articles


def _extract_article_data(li):
    code = _extract_article_code(li)
    title = _extract_article_title(li)
    journal = _extract_article_journal(li)
    citations = _extract_article_citations_info(li)

    return (code, title, journal) + citations


def _extract_article_code(li):
    li_a = li.find('a')
    if li_a:
        return li_a.get('name')
    return ''


def _extract_article_title(li):
    li_a = li.find('a')
    if li_a:
        return li_a.text
    return ''


def _extract_article_journal(li):
    li_i = li.find('i')
    if li_i:
        return li_i.text
    return ''


def _extract_article_citations_info(li):
    total_citations = _extract_total_citations(li)
    citing_documents_info = _extract_citing_documents_info(li)
    return (total_citations, '#'.join(citing_documents_info))


def _extract_total_citations(li):
    total_citations = 0

    cit_match = re.search(REGEX_TOTAL_CITATIONS, li.text)
    if cit_match and cit_match.group(1).isdigit():
        total_citations = int(cit_match.group(1))

    return total_citations


def _extract_citing_documents_info(li):
    citing_documents_data = []

    a = li.find('a')
    if a:
        cd_code = a.get('name')

        if cd_code:
            cd_path = CITING_DOCS.get(cd_code, '')

            if cd_path:
                citing_documents_data.extend(_parse_citing_doc(cd_path))

    return citing_documents_data


def _parse_citing_doc(path_file):
    cd_years = []

    with open(path_file) as f:
        soup = bs4.BeautifulSoup(f, 'html.parser')

        for cd in soup.find_all('li'):
            cdy = _find_citing_document_year(cd)
            cd_years.append(cdy)

    return cd_years


def _find_citing_document_year(citing_document_li):
    cdli_fixed = citing_document_li.text.replace('\n', '').strip()
    while '  ' in cdli_fixed:
        cdli_fixed = cdli_fixed.replace('  ', ' ')

    match_year = re.search(REGEX_CITING_DOC_YEAR, cdli_fixed)
    if match_year:
        if match_year.group(1):
            if match_year.group(1).isdigit():
                return match_year.group(1)

    return ''


def parse_file(path_file):
    parsed_data = []

    with open(os.path.join(path_file)) as f:
        soup = bs4.BeautifulSoup(f, 'html.parser')

        author_code = _extract_author_code(path_file)
        author_name = _extract_author_name(soup)
        author_journal_papers = _extract_journal_articles(soup)

        parsed_data.append((author_code, author_name, author_journal_papers))

    return parsed_data


def save(data):
    with open('biblio_econpapers.csv', 'w') as f:
        for d in data:
            a_code, a_name, ajps = d
            for year, arts in ajps.items():
                for art in arts:
                    code, title, journal, citations_total, citations_years = art
                    line = '|'.join(str(x).strip() for x in [a_code, a_name, year, code, title, journal, citations_total, citations_years])
                    f.write(line + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d',
        required=True,
        dest='dir_raw'
    )

    params = parser.parse_args()

    dir_econpapers = os.path.join(params.dir_raw, 'econpapers')
    dir_citing_docs = os.path.join(params.dir_raw, 'citing_docs')

    if not os.path.exists(dir_econpapers):
        print('Caminho %s não existe' % dir_econpapers)
        exit(1)

    files_econpapers = [os.path.join(dir_econpapers, f) for f in os.listdir(dir_econpapers)]

    global CITING_DOCS
    for f in os.listdir(dir_citing_docs):
        CITING_DOCS[f.replace('_', '/').replace('.html', '')] = os.path.join(dir_citing_docs, f)

    econpapers = []
    total_files = len(files_econpapers)
    for index, f in enumerate(files_econpapers):
        print('Status: %d of %d\tParsing: %s' % (index + 1, total_files, f))

        pf = parse_file(f)
        if pf:
            econpapers.extend(pf)

    save(econpapers)


if __name__ == '__main__':
    main()
