"""Check every internal href/src in dist/ resolves to a file; check viewport meta on every page."""
import os, re, sys
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','dist'); bad=[]; pages=0
for root,_,fs in os.walk(D):
    for f in fs:
        if not f.endswith('.html'): continue
        p=os.path.join(root,f); s=open(p,encoding='utf-8').read(); pages+=1
        if 'name="viewport"' not in s: bad.append((p,'no viewport'))
        for u in re.findall(r'(?:href|src)="([^"#]+)',s):
            if re.match(r'^(https?:|mailto:|data:)',u) or '${' in u: continue
            t=os.path.normpath(os.path.join(os.path.dirname(p),u.split('?')[0]))
            if os.path.isdir(t): t=os.path.join(t,'index.html')
            if not os.path.exists(t): bad.append((p,u))
print(f'{pages} pages checked, {len(bad)} problems')
for b in bad[:30]: print(*b)
sys.exit(1 if bad else 0)
