import csv

from .text_utils import _encode


def write(f, command, encoding, delimiter=','):
    '''Write command output to csv file.

    Required arguments:
    out - the output file descriptor
    command - the command object
    encoding - the output encoding to use
    '''
    writer = None

    # TODO retrieve headers & formatting functions
    fieldnames = lambda row: [_encode(encoding, s) for s in command.field_names(row)]

    for row in command.execute():
        if not writer:
            writer = csv.DictWriter(f, fieldnames=fieldnames(row),
                                    dialect='excel',
                                    delimiter=delimiter,
                                    extrasaction='ignore')
            # TODO print the human-readable names
            writer.writerow(command.header)

        # TODO format values if specified
        writer.writerow({k: _encode(encoding, command.field_formatter(k)(v)) for k, v in row.items() })
