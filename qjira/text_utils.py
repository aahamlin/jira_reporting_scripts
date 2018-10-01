
import six

def _encode(encoding, s):
    return six.text_type(s).encode(encoding, errors='ignore').decode(encoding)

def _generate_name(*args):
    return '_'.join([six.text_type(a) for a in args])

