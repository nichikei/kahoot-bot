import requests, re

r = requests.get('https://kahoot.it/libs/challenge/index.js',
                 headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)

print('Status:', r.status_code)

tokens = re.findall(r'KAHOOT_TOKEN[^\s"\']{0,80}', r.text)
print('Tokens found:', tokens[:5])

version = re.findall(r'"version"\s*:\s*"([^"]+)"', r.text)
print('Versions:', version[:5])

print('\nFirst 1000 chars:')
print(r.text[:1000])

with open('tok.txt', 'w', encoding='utf-8') as f:
    f.write(r.text)
print('\nFull JS saved to tok.txt')
