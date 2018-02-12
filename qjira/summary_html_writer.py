
from datetime import datetime

from .encoder import _encode

TABLE_STYLE = 'style="border-width: 1px; width: 100%; border-color: #DADADA; border-style: solid; font-family: "Helvetica Neue",Helvetica,Arial,Lucida Grande,sans-serif;"'

TABLE_HEADER_STYLE = 'color: #FFFFFF; background-color: #909090; text-align: left; vertical-align: baseline; padding: 6px; vertical-align: baseline;'

ROW_HEADER_STYLE = 'color: #505050; background-color: #DADADA; text-align: left; padding: 6px; vertical-align: baseline;'

CAPTION_STYLE = 'caption-side: bottom; text-align: center; font-style: italic;'

def _write_table_start(f):
    f.write('<table class="jiveBorder" border="1px" cellspacing="0" cellpadding="0" {}>\n'.format(TABLE_STYLE))
    f.write('<caption style="{0}">This report was generated by script on {1:%c}. Manual edits will be overwritten.</caption>\n'.format(CAPTION_STYLE, datetime.now()))

def _write_table_end(f):
    f.write('</table>')

def _write_header(f, fieldnames):
    f.write('<thead><tr>\n')
    for fld in fieldnames:
        f.write('<th style="{}">{}</th>'.format(TABLE_HEADER_STYLE, fld))
    f.write('</tr></thead>\n')

def _write_body_start(f):
    f.write('<tbody>\n')

def _write_body_end(f):
    f.write('</tbody>')

def _write_row_header(f, row):
    f.write('<tr style="{}">\n'.format(ROW_HEADER_STYLE))
    f.write('<td colspan="8">{}</td>'.format(row['issue_link']) + '\n')
    f.write('</tr>\n')

def _write_row_content(f, fieldnames, row):
    f.write('<tr>\n')
    # read in-order of fieldnames
    for n in fieldnames:
        f.write('<td>{}</td>'.format(row.get(n, None)))
    f.write('</tr>\n')

    
def write(f, command, encoding, *args, **kwargs):
    '''Write `summary` command output to HTML file.

    Required arguments:
    out - the output file descriptor
    command - the command object
    encoding - the output encoding to use
    '''

    header_done = False
    fieldnames = lambda row: [_encode(encoding, s) for s in command.expand_header(row)]

    _write_table_start(f)
    for row in command.execute():
        if not header_done:
            fieldnames=fieldnames(row)
            _write_header(f, [command.header[fld] for fld in fieldnames])
            header_done = True
            _write_body_start(f)

        # perform unicode conversion 
        unicode_row = {k:_encode(encoding, v) for k, v in row.items()}

        # begin rows, each grouping with table is marked with _row_header: True
        if '_row_header' in row and row['_row_header'] is True:
            _write_row_header(f, unicode_row)
        else:
            _write_row_content(f, fieldnames, unicode_row)

    _write_body_end(f)
    _write_table_end(f)
    
