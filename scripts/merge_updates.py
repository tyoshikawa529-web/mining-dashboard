#!/usr/bin/env python3
import json, pathlib, sys, datetime, re
root=pathlib.Path(__file__).resolve().parents[1]
base=root/"mining_data_latest.json"
inbox=root/"updates/inbox"
archive=root/"updates/processed"
countries={"Canada","Mongolia","Finland","Alaska"}
def read(p): return json.loads(p.read_text(encoding="utf-8"))
def valid(d):
 if not isinstance(d,dict): raise ValueError("JSON object required")
 if d.get("as_of"): datetime.date.fromisoformat(d["as_of"][:10])
 for x in d.get("map_updates",{}).get("mines",[]):
  if x.get("country") not in countries or not x.get("name") or not str(x.get("source","")).startswith("https://"): raise ValueError("Mine requires country/name/HTTPS source")
 for x in d.get("map_updates",{}).get("coordinates",[]):
  if x.get("country") not in countries or not x.get("name"): raise ValueError("Unknown coordinate mine")
  if not isinstance(x.get("lat"),(int,float)) or not isinstance(x.get("lng"),(int,float)) or not -90<=x["lat"]<=90 or not -180<=x["lng"]<=180: raise ValueError("Invalid lat/lng")
  if not x.get("precision") or "https://" not in str(x.get("location_note","")): raise ValueError("Missing coordinate precision or source")
 for x in d.get("market_changes",[]):
  if not x.get("commodity"): raise ValueError("Missing commodity")
  sources=[x.get("source")]+x.get("sources",[])+x.get("source_urls",[])
  if not any(str(s).startswith("https://") for s in sources if s): raise ValueError("Market source HTTPS required")
 for x in d.get("changes",[]):
  if not (x.get("name") or x.get("project")): raise ValueError("Missing mine name or project")
def unique(a,b,key):
 out={str(key(x)):x for x in a}
 for x in b:out[str(key(x))]=x
 return list(out.values())
def minekey(x):return (x.get("country","").lower(),x.get("name","").lower())
def changekey(x):return x.get("id") or (x.get("event_date") or x.get("published") or x.get("_source_date"),x.get("country"),x.get("name"),x.get("change_type") or x.get("current"))
def marketkey(x):return x.get("id") or (x.get("date") or x.get("published") or x.get("_source_date"),x.get("commodity"),x.get("indicator") or x.get("metric"),str(x.get("value") or x.get("current")))
def main():
 data=read(base);valid(data)
 pending=sorted(inbox.glob("*.json"))
 if not pending:print("No reviewed updates; retaining published data.");return
 for p in pending:
  delta=read(p);valid(delta)
  for field,key in (("changes",changekey),("market_changes",marketkey)):
   data[field]=unique(data.get(field,[]),delta.get(field,[]),key)
  for field in ("mines","coordinates"):
   data.setdefault("map_updates",{})[field]=unique(data["map_updates"].get(field,[]),delta.get("map_updates",{}).get(field,[]),minekey)
  if delta.get("as_of","")>data.get("as_of",""):data["as_of"]=delta["as_of"]
 valid(data)
 base.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 archive.mkdir(parents=True,exist_ok=True)
 for p in pending:p.rename(archive/p.name)
 print("Merged",len(pending),"reviewed files")
if __name__=="__main__":
 try:main()
 except Exception as e:print("VALIDATION ERROR:",e,file=sys.stderr);sys.exit(1)
