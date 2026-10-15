import csv, json, sys, os
import urllib.request, time
def fetch_all(raw, ids):
    os.makedirs(raw, exist_ok=True)
    for sid in ids:
        for attempt in range(3):
            try:
                with urllib.request.urlopen(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", timeout=30) as r:
                    open(f"{raw}/{sid}.csv","wb").write(r.read()); break
            except Exception as e:
                time.sleep(2); err=e
        else: raise SystemExit(f"fetch failed {sid}: {err}")
raw=sys.argv[1]; out=sys.argv[2]; os.makedirs(out, exist_ok=True)
def load(s):
    d={}
    for r in csv.DictReader(open(f"{raw}/{s}.csv")):
        v=r[s]
        if v not in ("","."): d[r["observation_date"][:7]]=float(v)
    return d
def mshift(m,k):
    y,mo=map(int,m.split("-")); t=y*12+mo-1+k; return f"{t//12}-{t%12+1:02d}"
S={ # key: (fred id, label, group, sticky_class)
 "cpi":("CPIAUCNS","CPI — All items","headline",""),
 "core":("CPILFENS","Core CPI (ex food & energy)","headline",""),
 "energy":("CPIENGNS","Energy","cpi_major","Transitory"),
 "gasoline":("CUUR0000SETB01","Gasoline","cpi_sub","Transitory"),
 "electricity":("CUUR0000SEHF01","Electricity","cpi_sub","Semi-sticky"),
 "natgas":("CUUR0000SEHF02","Utility (piped) gas","cpi_sub","Transitory"),
 "food":("CPIUFDNS","Food","cpi_major","Mixed"),
 "food_home":("CUUR0000SAF11","Food at home","cpi_sub","Transitory"),
 "food_away":("CUUR0000SEFV","Food away from home","cpi_sub","Sticky"),
 "core_goods":("CUUR0000SACL1E","Core goods","cpi_major","Tariff-sensitive"),
 "apparel":("CPIAPPNS","Apparel","cpi_sub","Tariff-sensitive"),
 "furnishings":("CUUR0000SAH3","Household furnishings & operations","cpi_sub","Tariff-sensitive"),
 "new_veh":("CUUR0000SETA01","New vehicles","cpi_sub","Tariff-sensitive"),
 "used_veh":("CUUR0000SETA02","Used cars & trucks","cpi_sub","Transitory"),
 "med_goods":("CUUR0000SAM1","Medical care commodities","cpi_sub","Mixed"),
 "core_svc":("CUUR0000SASLE","Core services","cpi_major","Sticky"),
 "shelter":("CUUR0000SAH1","Shelter","cpi_sub","Sticky"),
 "oer":("CUUR0000SEHC","Owners' equivalent rent","cpi_sub","Sticky"),
 "rent":("CUUR0000SEHA","Rent of primary residence","cpi_sub","Sticky"),
 "transport_svc":("CUUR0000SAS4","Transportation services","cpi_sub","Sticky"),
 "airline":("CUUR0000SETG01","Airline fares","cpi_sub","Transitory"),
 "med_svc":("CUUR0000SAM2","Medical care services","cpi_sub","Sticky"),
 "pce":("PCEPI","PCE price index","pce",""),
 "pce_core":("PCEPILFE","Core PCE","pce",""),
 "pce_goods":("DGDSRG3M086SBEA","PCE goods","pce_sub","Mixed"),
 "pce_durable":("DDURRG3M086SBEA","PCE durable goods","pce_sub","Tariff-sensitive"),
 "pce_nondurable":("DNDGRG3M086SBEA","PCE nondurable goods","pce_sub","Mixed"),
 "pce_services":("DSERRG3M086SBEA","PCE services","pce_sub","Sticky"),
 "pce_energy":("DNRGRG3M086SBEA","PCE energy","pce_sub","Transitory"),
 "pce_food":("DFXARG3M086SBEA","PCE food at home","pce_sub","Mixed"),
 "pce_supercore":("IA001260M","PCE services ex energy & housing","pce_sub","Sticky"),
}
start="2023-01"
if "--fetch" in sys.argv: fetch_all(raw, [v[0] for v in S.values()]+["CPIAUCSL","CPILFESL"])
series=[]; rows=[]
for k,(sid,label,grp,cls) in S.items():
    d=load(sid); months=sorted(m for m in d if m>=start)
    for m in months:
        b=mshift(m,-12); p=mshift(m,-1)
        yoy=round((d[m]/d[b]-1)*100,2) if b in d else None
        mom=round((d[m]/d[p]-1)*100,2) if p in d else None
        rows.append({"series":k,"month":m,"index":d[m],"yoy":yoy,"mom_nsa":mom})
    last=max(d)
    series.append({"key":k,"fred_id":sid,"label":label,"group":grp,"class":cls,"latest_month":last,
      "source": "BLS CPI-U, not seasonally adjusted (via FRED mirror)" if grp.startswith("cpi") or grp=="headline" else "BEA Personal Income & Outlays (via FRED mirror)",
      "url":f"https://fred.stlouisfed.org/series/{sid}"})
# SA series for momentum + projections
SA={"cpi":"CPIAUCSL","core":"CPILFESL","pce":"PCEPI","pce_core":"PCEPILFE"}
mom=[];proj=[]
for k,sid in SA.items():
    d=load(sid); ms=sorted(d)
    def chg(m,n):
        b=mshift(m,-n); return (d[m]/d[b])**(12/n)*100-100 if b in d and m in d else None
    for m in ms:
        if m<start: continue
        p=mshift(m,-1)
        mom.append({"series":k,"month":m,"mom_sa":round((d[m]/d[p]-1)*100,2) if p in d else None,
                    "ann3":round(chg(m,3),2) if chg(m,3) is not None else None,
                    "ann6":round(chg(m,6),2) if chg(m,6) is not None else None})
    last=ms[-1]
    # monthly avg rates (geometric) over windows of available consecutive data
    def avg(a,b):
        if a not in d or b not in d: return None
        n=(int(b[:4])*12+int(b[5:]))-(int(a[:4])*12+int(a[5:]))
        return (d[b]/d[a])**(1/n)-1
    scen={"Recent 3-mo pace":avg(mshift(last,-3),last),
          "12-mo pace":avg(mshift(last,-12),last),
          "Pre-war pace (Feb 2025–Feb 2026)":avg("2025-02","2026-02")}
    for name,r in scen.items():
        if r is None: continue
        lvl=d[last]
        for h in range(1,7):
            m=mshift(last,h); lvl=lvl*(1+r); b=mshift(m,-12)
            yoy=round((lvl/d[b]-1)*100,2) if b in d else None
            proj.append({"series":k,"scenario":name,"month":m,"yoy":yoy,"assumed_mom":round(r*100,3),"note":"" if yoy is not None else "No Oct 2025 base (shutdown) — 12-mo change not computable"})
for name,data in (("series",series),("observations",rows),("momentum",mom),("projections",proj)):
    with open(f"{out}/{name}.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(data[0].keys())); w.writeheader(); w.writerows(data)
print(len(rows),len(mom),len(proj))
