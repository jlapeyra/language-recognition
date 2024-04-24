from io import TextIOWrapper
from distribution import *
import unicodedataplus as unicode
import langcodes
import os



NUM_ALPHABET_CHARS = 38
NUM_ALPHABET_BLOCKS = 2
NUM_UNICODE_LETTERS = 2155 + 127004 # source: https://www.compart.com/en/unicode/category
NUM_UNICODE_BLOCKS = 327 # (including all) source: https://en.wikipedia.org/wiki/Unicode_block 
N_NGRAM = 3
WORD_MARKER = ' '

class Alphabet:
    __alphabet:set
    __block_encoding:dict

    def train(self, chars:Distribution, blocks:Distribution,
              num_chars:int=NUM_ALPHABET_CHARS, num_blocks:int=NUM_ALPHABET_BLOCKS
            ):
        self.__alphabet = {char 
                           for char, _ in chars.most_common(num_chars)}
        self.__block_encoding = {block:str(index) 
                                 for index, (block, _) in enumerate(blocks.most_common(num_blocks))}
        return self

    def save(self, file:TextIOWrapper):
        print('/'.join(self.__block_encoding.keys()), file=file)
        print(''.join(sorted(self.__alphabet)), file=file)

    def load(self, file:TextIOWrapper):
        self.__block_encoding = {block:str(index) 
                                 for index, block in enumerate(file.readline().strip().split('/'))}
        self.__alphabet = set(file.readline().strip())
        return self

    def getChar(self, char:str):
        char_low = char.lower()[0]
        if char_low in self.__alphabet:
            return char_low
        else:
            return self.__block_encoding.get(unicode.block(char_low)) or '?'
        
    def getString(self, string:str):
        return ''.join(self.getChar(c) for c in string if c.isalpha())

    def getAlphabet(self):
        return sorted(list(self.__alphabet)) + list(self.__block_encoding.values()) + ['?']
    
    def getTotalSize(self):
        return len(self.__alphabet) + len(self.__block_encoding) + 1

    def __eq__(self, other: object) -> bool:
        assert isinstance(other, self.__class__), f'No == defined for {type(self)} and {type(other)}'
        return self.__alphabet == other.__alphabet and self.__block_encoding == other.__block_encoding

class LanguageModel:
    def __init__(self, lang:str) -> None:
        self.lang = lang

    def compute_alphabet_distribution(self, train_iterator:list[str]):
        chars = Distribution()
        blocks = Distribution()
        for line in train_iterator:
            chars.update(char.lower()[0] for char in line if char.isalpha())
            blocks.update(unicode.block(char) for char in line if char.isalpha())
        self.block = blocks.most_common(1)[0][0]
        return chars, blocks

    def train(self, train_iterator:str, alphabet:Alphabet):
        self.trigram = NGram(3, ' ')
        self.alphabet = alphabet
        for line in train_iterator:
            for word in line.split():
                self.trigram.feed(alphabet.getString(word))
        return self

    def save(self, file):
        print(self.block, file=file)
        self.alphabet.save(file)
        self.trigram.save(file)

    def load(self, file:TextIOWrapper):
        self.block = file.readline().strip()
        self.alphabet = Alphabet().load(file)
        self.trigram = NGram(3, ' ').load(file)
        return self
 
    def getCrossEntropy(self, string:str):
        cross_entropy = CrossEntropy()
        for word in string.split():
            word = self.alphabet.getString(word)
            cross_entropy.feed(
                self.trigram.logProbabity(word, num_keys=self.alphabet.getTotalSize()), 
                len(word)+1
            )
        return cross_entropy.get()
    
        
class MetaLanguageModel:
    models : list[LanguageModel]

    def __init_models(self, folder, extension, given_langs):
        folder_langs = [filename.split('.')[0] for filename in os.listdir(folder) if filename.split('.')[-1] == extension]
        if given_langs:
            self.models = [LanguageModel(lang) for lang in given_langs if lang in folder_langs]
        else:
            self.models = [LanguageModel(lang) for lang in folder_langs]

    def train(self, folder_train:str, languages:list = None, folder_save:str=None):
        self.__init_models(folder_train, 'txt', languages)
        
        block_distributions = defaultdict(lambda: [Distribution(), Distribution()])
        for model in self.models:
            print(f"Training {model.lang}'s alphabet...")
            try:
                with open(f'{folder_train}/{model.lang}.txt', encoding='utf-8') as file:
                    chars, blocks = model.compute_alphabet_distribution((line for i,line in enumerate(file) if i%10 == 0))
                block_distributions[model.block][0] += chars.probabilityDistribution(num_keys=NUM_UNICODE_LETTERS)
                block_distributions[model.block][1] += blocks.probabilityDistribution(num_keys=NUM_UNICODE_BLOCKS)
            except Exception as e:
                print(e)
       
        alphabets = {}
        for block, (chars, blocks) in block_distributions.items():
            alphabets[block] = Alphabet().train(chars, blocks)
        
        for model in self.models:
            print(f'Training {model.lang}...')
            try: 
                with open(f'{folder_train}/{model.lang}.txt', encoding='utf-8') as file:
                    model.compute_trigram(file, alphabets[model.block])
                #print(f'Saving {model.lang}')
                if folder_save:
                    with open(f'{folder_save}/{model.lang}.model', 'w', encoding='utf-8') as file:
                        model.save(file)
            except Exception as e:
                print(e)
        return self

    def save(self, folder):
        for model in self.models:
            print(f'Saving {model.lang}')
            with open(f'{folder}/{model.lang}.model', 'w', encoding='utf-8') as file:
                model.save(file)
    
    def load(self, folder:str, languages:list = None):
        self.__init_models(folder, 'model', languages)
        alphabets_per_block = {}
        for model in self.models:
            print(f"Loading {model.lang}'s alphabet...")
            try:
                with open(f'{folder}/{model.lang}.model', encoding='utf-8') as file:
                    model.load(file)
                    __class__.__check_consistent_alphabets(alphabets_per_block, model.alphabet, model.block)
            except Exception as e:
                print(e)
        return self
  
    def __check_consistent_alphabets(alphabets_per_block, alphabet:Alphabet, block):
        if block in alphabets_per_block:
            assert alphabet == alphabets_per_block[block], 'Languages with the same block must have the same alphabet'
        else:
            alphabets_per_block[block] = alphabet

    def get_language(self, string:str):
        block = Distribution(unicode.block(char) for char in string if char.isalpha()).most_common(1)[0][0]
        entropy = []
        for model in self.models:
            if block == model.block:
                entropy.append((model.getCrossEntropy(string), model.lang))
        sorted_entropy = sorted(entropy)
        print(sorted_entropy)
        if sorted_entropy:
            print(langcodes.Language(sorted_entropy[0][1]).display_name('ca'))
        #langcodes.Language
        #print langcodes. sorted(entropy)[0][1]



if __name__ == '__main__':
    from time import time
    start = time()
    metamodel = MetaLanguageModel()
    metamodel.load('model_272L', ['ca', 'es', 'fr', 'it', 'nl', 'de', 'cz', 'pt', 'sr'])
    end = time()
    print(f'time = {end-start}')
    print(f'time/lang = {(end-start)/len(metamodel.models)}')


print('ok')
