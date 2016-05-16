#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
This module extracts content from a corpus. Corpus is interpreted here as
a bunch of text files that may or may not be annotated by a parser.

@author: granada
"""
import sys
sys.path.insert(0, '..') # This line is inserted to find the package utils.arguments
import logging
logger = logging.getLogger('corpus')
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

import os
from os.path import join, splitext
from collections import defaultdict

from structure import dictionaries

class Corpus(object):
    """
    Transforms the content of files in a more computational representation
    (Matrix Market representation).
    """
    def __init__(self, dirin, lang='en', parser='Stanford', filetype='.parsed'):
        """
        Initialize the class to generate a Matrix Market representation 
        of the corpus.

        Parameters:
        -----------
        dirin : string
            The path to the folder containing the input files
       lang : string
            The language of the input files. This is important to parsers that
            can generate files in more than one language. E.g, Treetagger may 
            generate relations for English, French, Portuguese etc.
        parser : string
            The name of the parser used to generate the input files.
        filetype : string
            The extension of the input files. The extension avoids trying to parse non
            parsed files that are in the same folder or backup files (`.parsed~`)

        Notes:
        ------
        self.dwords : DicWords
            Dictionary of words in the form:
                word: (id, freq)
        self.dctxs : DicWords
            Dictionary of the contexts in the form
                context: (id, freq)
        self.drels : DictRels
            Dictionary containing the relations between words 
            and contexts. This dictionary has the form:
                (idw, idc): freq
        """
        self.dirin = dirin
        self.docs = []
        if lang == 'en':
            if parser == 'Stanford':
                from stanford import Stanford
                self.Parser = Stanford
                parsedfiles = os.listdir(self.dirin)
                for filename in sorted(parsedfiles):
                    name, ext = splitext(filename)
                    if ext.endswith(filetype):
                        self.docs.append(filename)

        self.dwords = dictionaries.DictWords()
        self.dctxs = dictionaries.DictWords()
        self.drels = dictionaries.DictRels()


    def _documents(self, lex_mode='word', cwords=True, ctw='njv', normalize=True, lower=False):
        """
        Extract the content from a list of documents yielding each document at time.

        Parameters:
        -----------
        lex_mode : string {'word','lemma'}
            The type of lexical elements that are extracted.
        cwords : boolean {True, False}
            True in case of extracting only content words, False otherwise
        ctw : string {'npjv', 'npj', 'np', 'nj', 'n', ..., 'j'}, optional 
            The content words that should be extracted by `content_words=True`, being:
                n = nouns
                p = pronouns
                j = adjectives
                v = verbs
        normalize : boolean {True|False}, optional
            True in case of apply normalization to the terms, False otherwise
        lower : boolean {True, False}, optional
            Transform word to lowecase

        Yields:
        -------
        doc : array_like
            A list containing all terms of the document
        """
        for filename in self.docs:
            parser = self.Parser(join(self.dirin, filename), extract='WordsAndTags')
            content = parser.document(content_words=cwords, ctw=ctw, normalize=normalize, lower=lower)
            yield content


    def extractWindow(self, size=5, lex_mode='word', cwords=True, ctw='njv', normalize=True, lower=False):
        """
        Extract terms from the corpus using a window size equals to `size`.

        Parameters:
        -----------
        size : integer
            The size of the window that the content is extracted. E.g., ``size=5``
            means a window with two words before and two words after the target word.

        Notes:
        ------
        Contexts are extracted as `word#pos-r` if the context is on the left of the 
        target word and `word#pos-l` is the context is on the right of the target word. 
        Target word is represented as `tword` and context word is represented as  `cword`. 
        """
        d = self._documents(lex_mode, cwords, ctw, normalize, lower)
        doc = []
        for content in d:
            doc.extend(content)

        # create self.dwords, self.dctxs and self.drels
        if isinstance(size, int) or size.isdigit():
            n = (int(size)-1)/2
        else:
            n = len(doc)

        for i in xrange(0, len(doc)):
            for j in xrange(i+1, i+n+1):
                if j <= len(doc)-1:
                    record = False
                    if doc[i].pos == 'n' and doc[j].pos == 'v':
                        tword = doc[i].word
                        cword = doc[j].word+'#'+doc[j].pos+'-r'
                        record = True
                    elif doc[i].pos == 'v' and doc[j].pos == 'n':
                        tword = doc[j].word
                        cword = doc[i].word+'#'+doc[i].pos+'-l'
                        record = True
                    if doc[i].pos == 'n' and doc[j].pos == 'n':
                        tword = doc[j].word
                        cword = doc[i].word+'#'+doc[i].pos+'-l'
                        self.dwords[tword] = 1
                        self.dctxs[cword] = 1
                        idt, _ = self.dwords[tword]
                        idc, _ = self.dctxs[cword]
                        self.drels[(idt, idc)] = 1
                        tword = doc[i].word
                        cword = doc[j].word+'#'+doc[j].pos+'-r'
                        record = True
                    if doc[i].pos == 'n' and doc[j].pos == 'j':
                        tword = doc[i].word
                        cword = doc[j].word+'#'+doc[j].pos+'-r'
                        record = True
                    elif doc[i].pos == 'j' and doc[j].pos == 'n':
                        tword = doc[j].word
                        cword = doc[i].word+'#'+doc[i].pos+'-l'
                        record = True
                    if record:
                        self.dwords[tword] = 1
                        self.dctxs[cword] = 1
                        idt, _ = self.dwords[tword]
                        idc, _ = self.dctxs[cword]
                        self.drels[(idt, idc)] = 1


    def extractDocument(self, lex_mode='word', cwords=True, ctw='n', normalize=True, lower=False):
        """
        Extract terms from the corpus using the whole document as window of cooccurrences.

        """
        d = self._documents(lex_mode, cwords, ctw, normalize, lower)
        doc = []
        for iddoc, content in enumerate(d):
            for term, pos in content:
                self.dwords[term] = 1
                self.dctxs[iddoc] = 1
                idt, _ = self.dwords[term]
                idc, _ = self.dctxs[iddoc]
                self.drels[(idt, idc)] = 1
        print self.drels


    def extractSentences(self, lex_mode='word', cwords=True, ctw='n', normalize=True, lower=False):
        """
        Extract terms from the corpus using the whole document as window of cooccurrences.

        Notes:
        ------
        In this function the `tf` value is changed by the `df` value in self.dwords. Thus, the 
        dictionary of words is composed by the word: (id, df), where `df` means the document 
        frequency.
        """
        idsent = 0
        for filename in self.docs:
            parser = self.Parser(join(self.dirin, filename), extract='WordsAndTags')
            docwords = []
            newwords = []
            for _ in parser:
                content = parser.listOfTerms(content_words=cwords, ctw=ctw, normalize=normalize, lower=lower)
                for term, pos in content:
                    if not self.dwords.has_key(term):
                        self.dwords[term] = 1
                        newwords.append(term)
                    docwords.append(term)
                    self.dctxs[idsent] = 1
                    idt, _ = self.dwords[term]
                    idc, _ = self.dctxs[idsent]
                    self.drels[(idt, idc)] = 1
                idsent += 1
            t_indoc = set(docwords) - set(newwords)
            for word in t_indoc:
                self.dwords[word] = 1
        print self.dwords

    def save(self, fout, mode='db', new=True):
        """
        Save the dictionaries of words, contexts and relations between
        words and contexts. More specifically, save the content of 
        dictionaries self.dwords, self.dctxs and self.rels.

        Parameters:
        -----------
        fout : string
            The path to the file where the content is stored
        mode : string {'db', 'shelve'}
            The mode in which the output is saved
        new : Boolean {True, False}, optional
            Save the dictionary into an empty file
        """
        self.dwords.save(fout, dname='dwords', mode=mode, new=new)
        self.dctxs.save(fout, dname='dctxs', mode=mode)
        self.drels.save(fout, dname='drels', mode=mode)


    def load(self, fin, mode='db'):
        """
        Load the dictionaries of words, contexts and relations between
        words and contexts. More specifically, load the content to the
        dictionaries self.dwords, self.dctxs and self.rels.

        Parameters:
        -----------
        fin : string
            The path to the file where the content is stored
        mode : string {'db', 'shelve'}
            The mode in which the output is loaded
        """
        self.dwords.load(fin, dname='dwords', mode=mode)
        self.dctxs.load(fin, dname='dctxs', mode=mode)
        self.drels.load(fin, dname='drels', mode=mode)
        print self.dwords
#End of class Corpus