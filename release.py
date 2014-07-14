#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Script to make a CXTM test suite release.
#
# It creates a tar.gz distribution and updates the HTML page
#
import re
import glob
import os
from datetime import date
from string import Template
import tarfile

RELEASE_VERSION = 0.5

# Name of the directory for the generated index.html and the dist file
# The directory will be created if it does not exist
_DIST_DIRNAME = 'release' 

def get_directory_names():
    """\
    Returns the subdirectory names, '.svn' and 'web' excluded
    """
    return [n for n in os.listdir('.') if n not in ('.svn', 'web', _DIST_DIRNAME) and os.path.isdir(os.path.join('.', n))]

_LAST_CHANGES_PATTERN = re.compile(r'(\*.+?)(?:\n\n)', re.DOTALL|re.MULTILINE)

def generate_index_and_mail():
    """\
    Creates the index.html.
    """
    def update_test_count(dct, key, path):
        if key != 'tmcl':
            dct[key+'_valid'] = test_case_count(os.path.join(path, 'baseline'))
            dct[key+'_invalid'] = test_case_count(os.path.join(path, 'invalid'))
        else:
            dct[key+'_valid'] = test_case_count(os.path.join(path, 'valid'))
            dct[key+'_invalid'] = test_case_count(os.path.join(path, 'invalid')) + test_case_count(os.path.join(path, 'bad-schema'))
    def test_case_count(path):
        return len([n for n in glob.glob(path + '/*.*') if not n.endswith('.sub')])
    dct = {'release_version': RELEASE_VERSION,
           'release_date': date.today().isoformat()}
    for dirname in get_directory_names():
        update_test_count(dct, dirname, os.path.join('.', dirname))
        # Special cases
        if dirname == 'rdf':
            # CRTM tests are in a subdir of the RDF tests
            update_test_count(dct, 'crtm', os.path.join('.', dirname, 'crtm'))
            # The external mapping tests are in a subdir of the RDF tests
            # Count them to the RDF tests
            update_test_count(dct, '__rdf', os.path.join('.', dirname, 'externalmapping'))
            dct['rdf_valid'] += dct.pop('__rdf_valid')
            dct['rdf_invalid'] += dct.pop('__rdf_invalid')
        elif dirname == 'tmcl':
            update_test_count(dct, dirname, os.path.join('.', dirname, 'level-1'))
    # Update the test count for XTM 2.1 and JTM 1.1 since XTM 2.1 requires XTM 2.0 and JTM 1.1 requires JTM 1.0
    dct['xtm21_valid'] += dct['xtm2_valid']
    dct['xtm21_invalid'] += dct['xtm2_invalid']
    dct['jtm11_valid'] += dct['jtm_valid']
    dct['jtm11_invalid'] += dct['jtm_invalid']
    total_valid = 0
    total_invalid = 0
    for k,v in dct.iteritems():
        if '_invalid' in k:
            total_invalid+=v
        elif '_valid' in k:
            total_valid+=v
    dct['total_valid'] = total_valid
    dct['total_invalid'] = total_invalid
    # Template
    tpl = Template(open('./web/index.html').read())
    # Generated page
    index_page = open('./%s/index.html' % _DIST_DIRNAME, 'wb')
    index_page.write(tpl.substitute(dct))
    index_page.close()
    # Generate e-mail
    mail_tpl = Template(open('./web/mail.txt').read())
    changes = open('./CHANGES.txt').read()
    dct['changes'] = _LAST_CHANGES_PATTERN.search(changes).group(1)
    mail = open('./%s/mail.txt' % _DIST_DIRNAME, 'wb')
    mail.write(mail_tpl.substitute(dct))
    mail.close()

def generate_dist():
    """\
    Generates the distribution file.
    """
    def exclude_file(fn):
        return '.svn' in fn or fn.endswith('.bak')
    name = 'cxtm-tests-' + str(RELEASE_VERSION)
    base_dir = name+'/'
    archive_name = name + '.tar.gz'
    tar = tarfile.open(archive_name, fileobj=open(_DIST_DIRNAME + '/' + archive_name, 'wb'), mode='w:gz')
    for f in 'README', 'CHANGES.txt', 'LICENSE.txt':
        tar.add(f, arcname=base_dir+f)
    for d in get_directory_names():
        tar.add(d + '/', arcname=base_dir+d, exclude=exclude_file)
    tar.close()


if __name__ == '__main__':
    import sys
    if sys.hexversion < 0x020600F0:
        raise Exception('Requires Python >= 2.6')
    if not os.path.isdir('./' + _DIST_DIRNAME):
        os.mkdir('./' + _DIST_DIRNAME)
    generate_dist()
    generate_index_and_mail()
