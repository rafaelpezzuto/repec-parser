import csv
import os


NODE_CODE_COLUMN_HEADER = os.environ.get('NODE_CODE_COLUMN_HEADER', 'Id')
NODE_LABEL_COLUMN_HEADER = os.environ.get('NODE_CODE_COLUMN_HEADER', 'Label')
SOURCE_CODE_COLUMN_HEADER = os.environ.get('SOURCE_CODE_COLUMN_HEADER', 'Source')
TARGET_CODE_COLUMN_HEADER = os.environ.get('TARGET_CODE_COLUMN_HEADER', 'Target')
YEAR_COLUMN_HEADER = os.environ.get('YEAR_COLUMN_HEADER', 'Year')
INSTITUTION_COLUMN_HEADER = os.environ.get('INSTITUTION_COLUMN_HEADER', 'Institution')


def read_nodes(path_file_nodes, delimiter):
    nodes = {}

    with open(path_file_nodes) as f:
        csv_reader = csv.DictReader(f, delimiter=delimiter)
        for i in csv_reader:
            code = i.get(NODE_CODE_COLUMN_HEADER)
            label = i.get(NODE_LABEL_COLUMN_HEADER)

            if code not in nodes:
                nodes[code] = label
            else:
                print('Vértice duplicado %s' % code)

    return nodes


def read_edges(path_file_edges, delimiter):
    edges = []

    with open(path_file_edges) as f:
        csv_reader = csv.DictReader(f, delimiter=delimiter)
        for i in csv_reader:
            source = i.get(SOURCE_CODE_COLUMN_HEADER)
            target = i.get(TARGET_CODE_COLUMN_HEADER)
            year = i.get(YEAR_COLUMN_HEADER)
            institution = i.get(INSTITUTION_COLUMN_HEADER)
            edges.append((source, target, year, institution))

    return edges


def split_edges(edges):
    year_to_edges = {}
    for e in edges:
        s, t, y, i = e
        if y not in year_to_edges:
            year_to_edges[y] = []
        year_to_edges[y].append(e)

    cumulative_year_to_edges = {}
    counter = 0
    for y in sorted(year_to_edges.keys(), key=lambda x: int(x)):
        counter += 1
        cumulative_year_to_edges[counter] = []

        if counter > 1:
            cumulative_year_to_edges[counter].extend(cumulative_year_to_edges[counter - 1])

        cumulative_year_to_edges[counter].extend(year_to_edges[y])

    return cumulative_year_to_edges


def save(data, path):
    with open(path, 'w') as f:
        if 'nodes' in path:
            f.write('Id\tLabel\n')
        elif 'edges' in path:
            f.write('Source\tTarget\tYear\tInstitution\n')

        for d in data:
            f.write(d + '\n')
