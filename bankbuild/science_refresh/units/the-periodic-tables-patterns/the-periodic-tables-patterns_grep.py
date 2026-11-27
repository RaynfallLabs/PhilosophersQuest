import json,glob,re,os,sys
pat=re.compile(sys.argv[1],re.I)
for f in sorted(glob.glob('bankbuild/science_refresh/units/*/final.json')):
    unit=os.path.basename(os.path.dirname(f))
    d=json.load(open(f,encoding='utf-8'))
    for q in d['questions']:
        txt=q['question']+' || '+' | '.join(q['choices'])+' || '+q.get('context','')
        if pat.search(txt):
            print('##',unit,'T'+str(q['tier']))
            print('  Q:',q['question'])
            print('  A:',q['answer'])
            print('  C:',q['choices'])
            if len(sys.argv)>2: print('  X:',q.get('context'))
