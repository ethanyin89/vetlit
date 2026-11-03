import os,sys; os.environ.setdefault('VETLIT_LIVE','1')
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
import build_preview as B
t=B.TBY['fip']; ps=B.tpapers(t); base=B.newest3(ps); top=B.tops('fip')
x=dict(base[0]); x['reporting_inconsistency']={'severity':'affects_conclusion','note_zh':'原文结论与数据不一致'}
assert B.affects_conclusion(x) and '原文结论与数据不一致' in B.ri_notice(x)
assert x['sid'] not in [p['sid'] for p in B._fill([x]+base[1:])]
for sev in ('minor',None):
    y=dict(base[0]); y['reporting_inconsistency']={'severity':sev} if sev else {}
    assert not B.affects_conclusion(y) and B._fill([y])[0]['sid']==y['sid']
# extras path
pm=str(top[0]['pmid']); B._RI_FILE[pm]={'severity':'affects_conclusion'}
assert B.affects_conclusion(B.get(pm)) and top[0]['sid'] not in [p['sid'] for p in B.tops('fip')]
B._RI_FILE.clear()
# no paper has the field yet -> nothing excluded by it
assert not any(B.affects_conclusion(p) for p in B.PAPERS) if hasattr(B,'PAPERS') else True
print('reporting_inconsistency tests OK')
