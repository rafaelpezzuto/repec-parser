import argparse

from utils import read_nodes, read_edges, split_edges, save


DELIMITER = '\t'


def decide_edge_merge(key, old_inst, new_inst):
    if old_inst == '' and new_inst != '':
        return new_inst

    if new_inst == '':
        return old_inst

    choice = input('[%s] 1 or 2?\n1: %s\n2: %s\n' % (key.replace('\t', '|'),
                                                     old_inst.replace('\t', '|'),
                                                     new_inst.replace('\t', '|')))

    if choice == '1':
        return old_inst
    elif choice == '2':
        return new_inst


def read_data():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-n',
        dest='file_nodes',
        help='Arquivo em que cada linha deve conter o código do vértice e seu '
             'respectivo nome.'
    )
    parser.add_argument(
        '-e',
        dest='file_edges',
        required=True,
        help='Arquivo em que cada linha deve conter o código do vértice origem e o código '
             'do vértice de destino.'
    )
    params = parser.parse_args()

    if params.file_nodes:
        nodes = read_nodes(params.file_nodes, delimiter=DELIMITER)
    else:
        nodes = {}

    edges = read_edges(params.file_edges, delimiter=DELIMITER)

    return nodes, edges


if __name__ == '__main__':
    print('Reading nodes and edges')
    nodes, edges = read_data()

    print('Spliting edges according to its years')
    cumedges = split_edges(edges)

    edge_to_inst = {}

    print('Saving subgraphs')
    for c in cumedges:
        c_edges = []
        c_nodes = []

        c_year = -1

        for i in cumedges[c]:
            s_code, t_code, year, institution = i
            s_name = nodes.get(s_code, '')
            t_name = nodes.get(t_code, '')

            sn_str = '\t'.join([s_code, s_name])
            tn_str = '\t'.join([t_code, t_name])

            if sn_str not in c_nodes:
                c_nodes.append(sn_str)
            if tn_str not in c_nodes:
                c_nodes.append(tn_str)

            c_edge = '\t'.join([s_code, t_code, year])

            if c_edge not in c_edges:
                c_edges.append(c_edge)

                if c_edge not in edge_to_inst:
                    edge_to_inst[c_edge] = institution
                else:
                    if edge_to_inst[c_edge] != institution:
                        institution = decide_edge_merge(c_edge, edge_to_inst[c_edge], institution)
                        edge_to_inst[c_edge] = institution

            if int(year) > c_year:
                c_year = int(year)

        save(c_nodes, 'nodes_' + str(c_year) + '.csv')

        for ind, c in enumerate(c_edges):
            c_edges[ind] = c + '\t' + edge_to_inst[c]
        save(c_edges, 'edges_' + str(c_year) + '.csv')
