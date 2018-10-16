from re import findall, match, search  # we will use regexp to parse words out of book fed to us
from collections import Counter  # this class implements what we need - dict with the words & frequencies
from argparse import ArgumentParser


# Thats a global which will contain word / frequency table we gonna use for identifying most probable word
vocabulary = Counter()

def build_vocabulary(file_name):
    """
    Returns Counter of lower case words from the file contents.
    :param file_name: file to be parsed
    :return: Counter with word from file
    """
    try:
        file_content = open(file_name)
        with file_content:
            text = file_content.read()
            normalized_text = text.lower()
            all_words = findall(r'\w+', normalized_text)  # as per https://docs.python.org/3.6/howto/regex.html
            ok_words = []

            for word in all_words:
                word.strip("_")

                if not search('[0-9]', word):
                    ok_words.append(word)

            counter = Counter(ok_words)
            return counter
    except IOError:
        print("[ ERROR ] Cannot read from " + file_name)

# Ok, how do we get correction? We would get correction as most probable candidate from the list
# of all possible word on the edit distance 1, 2, or the same word if nothing else matched...


def propose_correction(for_this_word):
    """
    Most probable spelling for the word
    :param for_this_word: word you are checking
    :return: word (if its right already) or a correction proposition as string
    TODO: Return not first dict match, but max of P for the candidates list
    """
    most_probable_word = max(identify_candidates(for_this_word), P)
    return most_probable_word


def identify_candidates(word):
    """
    We either know this word from file, or its on 1-2 edit distance from known, or we dont know it
    and thus leave as it is
    :param word:
    :return: candidate word(s) as set
    TODO: Rearrange to avoid building all variations upfront - build next section only not found in previous
    """

    # Do we know this word?
    result = known([word])
    if result:
        return result

    # May be its 1-edit from one of the words we know?..
    result = known(edits1(word))
    if result:
        return result

    # May be its 2-edit from one of the words we know?..
    result = known(edits2(word))
    if result:
        return result

    # Ok, we have no idea what to do, ship it back
    return set(word)


def P(of_word):
    """
    Returns probability of the particular word in the text
    :param for_this_word word you are looking for
    :return: probablity as float
    """
    N = sum(vocabulary.values())
    p = vocabulary[of_word] / N
    return p


def known(words):
    """
    Will returns word(s) which are in dictionary.
    :param words: words to check against dictionary
    :return: know word(s) as iterable set
    """

    known_words = set()
    for word in words:
        if word in vocabulary:
            known_words.add(word)

    return known_words
    # return set(w for w in words if w in vocabulary)


"""
Next two functions are courtesy of Datta Sainath Dwarampudi, from:
https://newclasses.nyu.edu/access/content/group/92f54196-4c8e-4057-b493-c1e043cb4334/Labs/Lab%205%20Spell%20Checker.ipynb
"""

alphabet = 'abcdefghijklmnopqrstuvwxyz'


def produce_splits(word):
    return [(word[:i], word[i:])
            for i in range(len(word) + 1)]

def edits1(word):
    pairs = produce_splits(word)
    deletes = [a + b[1:] for (a, b) in pairs if b]
    transposes = [a + b[1] + b[0] + b[2:] for (a, b) in pairs if len(b) > 1]
    replaces = [a + c + b[1:] for (a, b) in pairs for c in alphabet if b]
    inserts = [a + c + b for (a, b) in pairs for c in alphabet]
    return set(deletes + transposes + replaces + inserts)


def edits2(word):
    """
    Recursive call of edits1 to produce edits who are 2 edits away.
    """
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))

if __name__ == '__main__':
    try:
        parser = ArgumentParser()
        parser.add_argument('--v', '--vocabulary', help='File to be used as a vocabulary')
        parser.add_argument('--s', '--source', help='File to use an input for spell check')
        parser.add_argument('--d', '--destination', help='File to store results of the spell check')
        parser.add_argument('--l', '--log', help='Display diagnostic info during spell check')

        args = parser.parse_args()

        source_file = open(args.s, 'r')
        destination_file = open(args.d, 'w')

        # Here we build frequency / probability table we use for spell checking
        vocabulary = build_vocabulary(args.v)
        if args.l:
            print('[ INFO ] Finished parsing ' + args.v +
                  ', extracted ' + str(vocabulary.__len__()) + ' words and their frequencies.\n')

        corrected_words = []
        for line in source_file.readlines():
            clean_line = line.strip("\r\n").lower()
            corrected_word = propose_correction(clean_line).pop() # assuming first one is most probable one
            corrected_words.append(corrected_word + '\n')
            if args.l:
                print('[ INFO ] Word ' + clean_line + ' turns into ' + corrected_word)

        # ok, now lets flush the list we created into the file...
        destination_file.writelines(corrected_words)

    except Exception as e:
        print("[ ERROR ] Cannot spellcheck with parameters you supplied. Exception information as follows:")
        print(str(e.message))

    finally:
        source_file.close()
        destination_file.close()
