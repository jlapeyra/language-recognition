import unicodedataplus as ud
from collections import Counter, defaultdict

def spacing(string:str, chars:int):
    return string[:chars] + ' '*max(0, chars - len(string))


def compute(training_filename:str):
    with open(training_filename, 'r', encoding='utf-8') as file:
        unicode_blocks = defaultdict(lambda: [0, defaultdict(int)])
        num_letters = 0
        for line in file:
            for char in line:
                if char.isalpha():
                    unicode_blocks[ud.block(char)][0] += 1
                    unicode_blocks[ud.block(char)][1][char.lower()[0]] += 1
                    num_letters += 1
        for block, (n_block, letters) in sorted(unicode_blocks.items(), reverse=True, key=lambda item: item[1][0]):
            print('   ', spacing(block, 28), 100*n_block/num_letters, '%', f'({n_block})', file=output)
            for letter, n_letter in sorted(letters.items(), reverse=True, key=lambda item: item[1]):
                if (n_letter/num_letters > 0.0005):
                    print('       ', letter, 100*n_letter/num_letters, '%', f'({n_letter})', file=output)



from language_list import language_list
output = open('blocks.txt', 'w', encoding='utf-8')
for lang in language_list:
    print(lang, file=output)
    lm = compute(f'train/{lang}.txt')
    print(file=output)


    

