#!/usr/bin/env python3
"""Static accessibility lint; does not assert WCAG conformance."""
from html.parser import HTMLParser
from pathlib import Path
import sys
class Check(HTMLParser):
 def __init__(self):super().__init__();self.lang=False;self.main=0;self.skip=False;self.h1=0;self.table=0;self.headings=[]
 def handle_starttag(self,t,a):
  x=dict(a)
  if t=='html':self.lang=bool(x.get('lang')) and x.get('dir') in ('rtl','ltr')
  if t=='main':self.main+=1
  if t=='h1':self.h1+=1
  if t=='a' and x.get('href')=='#main':self.skip=True
  if t=='table':self.table+=1
  if t=='th' and x.get('scope') not in ('row','col'):self.headings.append('th without scope')
errors=[]
for f in Path('dist').rglob('*.html'):
 p=Check();p.feed(f.read_text())
 if not(p.lang and p.main==1 and p.h1==1 and p.skip and not p.headings):errors.append(str(f))
print('HTML accessibility structure checks:', 'passed' if not errors else errors)
sys.exit(bool(errors))
