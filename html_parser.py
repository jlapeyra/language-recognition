from html.parser import HTMLParser
import requests
from time import time

time_request = 0
time_parse = 0

class RequesterParser(HTMLParser):
    def __init__(self, url: str, keep_content: bool = False) -> None:
        global time_request
        global time_parse
        super().__init__()
        self.url = url

        start = time()
        response = requests.get(url)
        content = response.content.decode(response.encoding)
        time_request += time() - start

        start = time()
        self.feed(content)
        if (keep_content): self.content = content
        time_parse += time() - start
        

class Text(RequesterParser):

    stack : list = []
    #stack_tags = []
    text : str = ''

    count_keys = {
        'include 1' : 0,
        'include 2' : 0,
        'exclude' : 0
    }

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get('class', '').split()
        keys = []
        if 'mw-parser-output' in classes: 
            keys.append('include 1')
        if tag == 'p':
            keys.append('include 2')
        elif (tag in ('script', 'style', 'table', 'math') or
            not {'mw-editsection', 'reflist', 'citation', 'interProject'}.isdisjoint(classes)
        ):
            keys.append('exclude')
        for key in keys:
            self.count_keys[key] += 1
            #print(self.count_keys, key, tag)
        self.stack.append((tag, keys))
        #self.stack_tags.append('.'.join([tag]+classes))
        

    def handle_endtag(self, tag):
        #self.stack_tags.pop()
        stack_tag, keys = None, None
        while tag != stack_tag:
            stack_tag, keys = self.stack.pop()
            for key in keys:
                self.count_keys[key] -= 1
                #print(self.count_keys, '/', key, stack_tag)
    
    def handle_data(self, data):
        if (self.count_keys['include 1'] and
            self.count_keys['include 2'] and 
            not self.count_keys['exclude']
        ):
            self.text += data
            #print(self.count_keys)



class LanguageLinks(RequesterParser):

    language_links = {}

    def url2lang(url:str):
        return url.split('/')[2].split('.')[0]

    def __init__(self, url: str, keep_content: bool = False) -> None:
        lang = LanguageLinks.url2lang(url)
        self.language_links[lang] = url
        super().__init__(url, keep_content)
    
    def handle_starttag(self, tag, attrs):
        if (tag == 'a'):
            attrs = dict(attrs)
            if (attrs.get('class') == 'interlanguage-link-target'):
                href = attrs['href']
                lang = LanguageLinks.url2lang(href)
                self.language_links[lang] = href


class Top1000Links(RequesterParser):

    stack = []
    links = []
    preffix = ''

    def __init__(self, url: str, keep_content: bool = False):
        self.preffix = '/'.join(url.split('/')[:3])
        super().__init__(url=url, keep_content=keep_content)
    
    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)
        if ('a' == tag and 'li' in self.stack and 'ol' in self.stack):
            href = dict(attrs)['href']
            if (href.startswith('/wiki/') and not ':' in href):
                self.links.append(self.preffix + href)
            

    def handle_endtag(self, tag):
        stack_tag = None
        while tag != stack_tag:
            stack_tag = self.stack.pop()

if __name__ == '__main__':
    Text('https://ca.wikipedia.org/wiki/COVID-19')
    
