import os
from string import punctuation
import argparse

from pymorphy2 import MorphAnalyzer
from tqdm import tqdm


def uniq(list_):

    already = set()
    result = []

    for it in list_:
        if it not in already:
            result.append(it)
            already.add(it)
    return result


def inflect_word(word, morph=None):

    CASES = ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']

    if morph is None:
        morph = MorphAnalyzer()

    parsed = morph.parse(word)[0]

    results = [word]

    for case in CASES:
        inflected = parsed.inflect({case})
        if inflected is not None:
            results.append(inflected.word)

    if not results:
        results.append(word)

    return sorted(uniq(results), key=lambda _: len(_))


def get_common(list_of_words):

    common = os.path.commonprefix(list_of_words)
    n_common = len(common)

    suffixes = []

    for word in list_of_words:
        suffixes.append(word[n_common:])

    return common, suffixes


def is_word(word):

    return any(char.isalpha() for char in word)


def fix_ocr_errors(word_regexp):

    new_regexp = word_regexp.replace('о', '(о|0)')
    new_regexp = new_regexp.replace('ё', '(е|ё)')

    return new_regexp


def inflected_word_regexp(word, ocr=True):

    if len(word) < 3:
        return word

    if word == '...':
        return '.*'

    if not is_word(word):
        return word

    last = ''

    if word[-1] in punctuation:
        last = word[-1]
        word = word[:-1]

    forms = inflect_word(word)
    common, suffixes = get_common(forms)

    suffixes_regexp = ''

    if len(suffixes) == 1 and suffixes[0] == '':
        suffixes = []
    else:
        suffixes_regexp = '({0})'.format('|'.join(_ for _ in suffixes if _))

    required = '' not in suffixes

    regexp = '{0}{1}{2}{3}'.format(common, suffixes_regexp, '' if required else '?', last)

    return fix_ocr_errors(regexp) if ocr else regexp


def inflected_regexp(sent, ocr=True):

    return [inflected_word_regexp(w, ocr) for w in sent.split(' ') if w]


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--directory', help='Directory with files')
    parser.add_argument('--debug', action='store_true')

    args = parser.parse_args()

    directory = args.directory
    debug = args.debug

    for filename in tqdm(os.listdir(directory)):
        if filename.endswith('.txt'):
            if debug:
                print('Reading file: ', filename)
            full_filename = os.path.join(directory, filename)
            with open(full_filename) as fid:
                lines = fid.read().split('\n')

            infl_lines = []

            for line in lines:
                if debug:
                    print('Source line: ', line)
                inflected_words = inflected_regexp(line)
                inflected_line = ' '.join(inflected_words)
                infl_lines.append(inflected_line)
                if debug:
                    print('Inflected line: ', inflected_line, '\n')

            new_full_filename = os.path.splitext(full_filename)[0] + '.rules'
            with open(new_full_filename, 'w') as fid:
                fid.write('\n'.join(infl_lines))


if __name__ == '__main__':

    main()
