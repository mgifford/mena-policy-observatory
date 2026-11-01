#!/usr/bin/env python3
"""Generate portable static HTML per region and locale (no runtime JS)."""
from pathlib import Path
import argparse,html,json
ROOT=Path(__file__).resolve().parents[1]
def esc(s):return html.escape(str(s),quote=True)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def page(lang,title,body,depth=0):
 direction='rtl' if lang=='ar' else 'ltr'
 return f"""<!doctype html><html lang="{lang}" dir="{direction}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><link rel="stylesheet" href="{'../'*depth}assets/site.css"></head><body><a class="skip" href="#main">{'تجاوز إلى المحتوى الرئيسي' if lang=='ar' else 'Skip to main content'}</a><header><p class="brand">{esc(title)}</p><nav aria-label="{'اللغة' if lang=='ar' else 'Language'}"><a href="{'../'*depth + ('en/' if lang=='ar' else 'ar/')}" hreflang="{'en' if lang=='ar' else 'ar'}" lang="{'en' if lang=='ar' else 'ar'}">{'English' if lang=='ar' else 'العربية'}</a></nav></header><main id="main" tabindex="-1">{body}</main><footer><p>{'بحث مستقل، وليس نصيحة قانونية أو تفسيرًا رسميًا' if lang=='ar' else 'Independent research, not legal advice or an official interpretation.'}</p></footer></body></html>"""
def build(region):
 base=ROOT/'regions'/region; out=ROOT/'dist'/region
 if out.exists(): import shutil;shutil.rmtree(out)
 (out/'assets').mkdir(parents=True)
 (out/'assets/site.css').write_text((ROOT/'framework/site.css').read_text())
 cfg=load(base/'region.json'); policies=load(base/'data/policies.json'); countries=load(base/'data/countries.json')
 for lang in cfg['languages']:
  pdir=out/lang;pdir.mkdir()
  title=cfg['title'][lang]; ar=lang=='ar'
  intro='<h1>'+esc(title)+'</h1><p>'+('البحث غير مكتمل. لا تعني المعلومات المفقودة عدم وجود قانون.' if ar else 'Research is incomplete. Missing evidence does not establish that legislation is absent.')+'</p>'
  intro+='<h2>'+('مقارنة السياسات' if ar else 'Policy comparison')+'</h2>'
  intro+='<div class="table-scroll" role="region" aria-label="'+('جدول السياسات' if ar else 'Policy comparison table')+'" tabindex="0"><table><caption>'+('السجلات البحثية، وليست أحكام امتثال' if ar else 'Research records, not compliance verdicts')+'</caption><thead><tr><th scope="col">'+('الدولة' if ar else 'Jurisdiction')+'</th><th scope="col">'+('الوثيقة' if ar else 'Document')+'</th><th scope="col">'+('المعيار المشار إليه' if ar else 'Reported standard')+'</th><th scope="col">'+('المراجعة القانونية' if ar else 'Legal assessment')+'</th><th scope="col">'+('الأدلة' if ar else 'Evidence')+'</th></tr></thead><tbody>'
  for rec in policies:
   id=rec['id']; country=rec.get('country',''); name=rec.get('title','Untitled');std=rec.get('standard') or '—'
   row=f'<tr><th scope="row">{esc(country)}</th><td>{esc(name)}</td><td>{esc(std)}</td><td>{esc(rec.get("legal_effect","not assessed"))}</td><td><a href="records/{esc(id)}.html">'+('التفاصيل والمصادر' if ar else 'View sources and notes')+'</a></td></tr>'
   intro+=row
  intro+='</tbody></table></div>'
  intro+='<h2>'+('تغطية البلدان' if ar else 'Country research coverage')+'</h2><div class="table-scroll" role="region" tabindex="0" aria-label="'+('تغطية البلدان' if ar else 'Country coverage')+'"><table><caption>'+('عدم وجود سجلات لا يعني عدم وجود تشريعات' if ar else 'No record does not mean no legislation')+'</caption><thead><tr><th scope="col">'+('البلد' if ar else 'Jurisdiction')+'</th><th scope="col">'+('سجلات المصادر' if ar else 'Source records')+'</th><th scope="col">'+('حالة البحث' if ar else 'Research status')+'</th></tr></thead><tbody>'
  for country in countries:
   ct=sum(1 for record in policies if record.get('country')==country['code'])
   intro+='<tr><th scope="row">'+esc(country['name'])+'</th><td>'+str(ct)+'</td><td>'+ (('مصادر أولية، مراجعة قانونية معلقة' if ar else 'Source leads; legal review pending') if ct else ('لم يبدأ البحث' if ar else 'Not yet researched')) +'</td></tr>'
  intro+='</tbody></table></div>'
  intro+='<h2>'+('مصادر مقارنة إضافية' if ar else 'Additional comparative resources')+'</h2><p><a href="https://www.unescwa.org/sites/default/files/pubs/pdf/technical-guidelines-digital-accessibility-empower-older-persons-english.pdf">UN ESCWA digital accessibility guidance and regional comparison (2025)</a>. '+('هذه دراسة ثانوية وليست تشريعاً ملزماً.' if ar else 'This is a secondary research source, not binding legislation.')+'</p>'
  intro+='<h2>'+('مجالات السياسة' if ar else 'Policy domains')+'</h2><ul>' 
  for v in cfg['domain_labels'].values():intro+='<li>'+esc(v[lang])+'</li>'
  intro+='</ul>'
  (pdir/'index.html').write_text(page(lang,title,intro,1),encoding='utf-8')
  (pdir/'records').mkdir()
  for rec in policies:
   id=rec['id']; ref=base/'policies'/id
   body='<p><a href="../index.html">'+('العودة إلى المقارنة' if ar else 'Back to comparison')+'</a></p><h1>'+esc(rec.get('title',id))+'</h1>'
   body+='<dl><dt>'+('الجهة' if ar else 'Authority')+'</dt><dd>'+esc(rec.get('authority','Not verified'))+'</dd><dt>'+('حالة المراجعة' if ar else 'Legal review')+'</dt><dd>'+esc(rec.get('legal_effect','Not assessed'))+'</dd><dt>'+('المصدر الرسمي المبلغ عنه' if ar else 'Reported official source')+'</dt><dd><a href="'+esc(rec.get('source_url','#'))+'">'+esc(rec.get('source_title','Source'))+'</a></dd></dl>'
   body+='<p>'+('الملفات أدناه مواد بحثية وغير معتمدة قانونيًا.' if ar else 'The files below are research artifacts, not legally approved executable requirements.')+'</p>'
   body+='<h2>'+('نطاق الوثيقة' if ar else 'Instrument scope')+'</h2><p>'+esc(rec.get('scope','Not verified'))+'</p><h2>'+('نوع الوثيقة' if ar else 'Instrument type')+'</h2><p>'+esc(rec.get('instrument_type','Not classified'))+'</p><h2>'+('الأسئلة المفتوحة' if ar else 'Open interpretation issues')+'</h2><p>'+str(rec.get('unresolved_interpretations',0))+' '+('مسائل تتطلب مراجعة' if ar else 'issues require review')+'</p>'
   body+='<h2>'+('الملخص وحدود الأدلة' if ar else 'Research summary and limits')+'</h2><p>'+esc(rec.get('notes','No source analysis completed.'))+'</p><p><strong>'+('حالة القواعد' if ar else 'Rule status')+':</strong> '+esc(rec.get('execution_status','not encoded'))+'</p>'
   for file,label in [('PROVISIONS.md','Provision-by-provision research'),('SOURCE.md','Source Markdown'),('INTERPRETATION.md','Interpretation and ambiguity'),('RELATED.md','Related documents'),('rule.rulespec.yaml','Axiom RuleSpec scaffold'),('manifest.json','Manifest')]:
    if (ref/file).exists():
     body+='<section><h2>'+esc(label)+'</h2><p><a href="artifacts/'+esc(id)+'/'+esc(file)+'">'+('عرض الملف الأصلي' if ar else 'Open source file')+'</a></p></section>'
   (pdir/'records'/f'{id}.html').write_text(page(lang,title,body,2),encoding='utf-8')
  # Publish raw artifacts under language-scoped paths, preserving URLs and provenance.
  art=pdir/'records'/'artifacts'
  art.mkdir()
  for rec in policies:
   src=base/'policies'/rec['id']
   if src.exists():import shutil;shutil.copytree(src,art/rec['id'])
 print(f'Built {region}: {len(policies)} research records')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--region',choices=['mena','europe','all'],default='all');a=parser.parse_args()
 for r in (['mena'] if a.region=='all' else [a.region]):build(r)

# Standalone regional landing page
(ROOT/'dist'/'index.html').write_text('<!doctype html><html lang="en" dir="ltr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MENA Policy Observatory</title><link rel="stylesheet" href="mena/assets/site.css"></head><body><a class="skip" href="#main">Skip to main content</a><main id="main"><h1>MENA Policy Observatory</h1><p>Research and comparison, not binding legal advice.</p><ul><li><a href="mena/en/">English</a></li><li><a href="mena/ar/" lang="ar">العربية</a></li></ul></main></body></html>',encoding='utf-8')
