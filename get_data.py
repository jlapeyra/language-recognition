from collections import defaultdict
import html_parser
import math


def getLinks(languages:list[str] = None, size : int = None, offset: int = 0, limit: int = None) -> dict[str,list[str]]:

    parser = html_parser.Top1000Links('https://ca.wikipedia.org/wiki/Viquip%C3%A8dia:Llista_d%27articles_que_totes_les_lleng%C3%BCes_haurien_de_tenir')
    
    links_by_language = defaultdict(list) #{lang:[] for lang in langs}
    
    step = math.ceil(len(parser.links)/size) if size else 1
    start = offset
    end = start + step*limit if limit else None

    for link in parser.links[start:end:step]:
        lang_parser = html_parser.LanguageLinks(link)
        for lang in lang_parser.language_links:
            if not languages or lang in languages:
                links_by_language[lang].append(lang_parser.language_links[lang])
    '''with open('languages.py', 'w') as f:
        print('languages =', list(links_by_language), file=f)'''
    return links_by_language





def saveText(lang_links: dict[str,list[str]], dir: str):
    for lang, links in lang_links.items():
        with open(f'{dir}/{lang}.txt', 'w', encoding='utf-8') as file:
            for link in links:
                try:
                    parser = html_parser.Text(link)
                    print(parser.text, file=file)
                    print(link)
                except Exception as e:
                    print(f'Error in {link}: {e}')



def getText(lang_links:list[str]):
    for links in lang_links:
        for link in links:
            print(link)
            try:
                yield html_parser.Text(link).text
            except Exception as e:
                print(f'{link}: {e}')




def pruneData(min_size):
    import os
    dir = 'training_many/'
    sizes = []

    for filename in os.listdir(dir):
        path = dir+filename
        lines = set()
        size = 0
        with open(path, 'r', encoding='utf-8') as input:
            with open('out.aux.txt', 'w', encoding='utf-8') as output:
                for line in input:
                    if line!='\n' and line not in lines:
                        lines.add(line)
                        size += len(line)
                        output.write(line)
        sizes.append((filename, size))
        if size >= min_size:
            os.remove(path)
            os.rename('out.aux.txt', path)
        else:
            os.remove('out.aux.txt')
            os.remove(path)
    print('ok')

#saveText(getLinks(languages, size=80), 'training_many')

#print('Request time:', html_parser.time_request, 'sec')
#print('Parse time:  ', html_parser.time_parse, 'sec')

#pruneData(3000)

