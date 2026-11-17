"""Ledgerly - payroll manager (single file).
Setup:  pip install fastapi uvicorn sqlalchemy pyjwt
Run:    python ledgerly.py   then open http://127.0.0.1:8000
Logins: admin / viewer; passwords come from LEDGERLY_ADMIN_PW and LEDGERLY_VIEWER_PW
        (local defaults: admin123 / viewer123 - ALWAYS set both in production).
Env:    LEDGERLY_SECRET (JWT key), LEDGERLY_DB (database URL), HOST, PORT
"""
import csv, hashlib, hmac, io, os, secrets, datetime as dt
import jwt
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import JSON, Integer, String, DateTime, create_engine, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

# If no secret is configured, use a random one (logins reset on every restart) instead of a guessable default.
SECRET = os.getenv("LEDGERLY_SECRET") or secrets.token_hex(32)
DB_URL = os.getenv("LEDGERLY_DB", "sqlite:///ledgerly.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})

def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)

# ---- Simplified US-style tax (monthly pay is annualised). Edit to your rules.
BRACKETS = [(11_000_00, .10), (44_725_00, .12), (95_375_00, .22), (None, .24)]  # annual, cents
FICA = .0765

def income_tax_monthly(gross: int) -> int:
    annual, tax, low = gross * 12, 0.0, 0
    for cap, rate in BRACKETS:
        top = annual if cap is None else min(annual, cap)
        if top > low: tax += (top - low) * rate
        low = cap if cap is not None else annual
        if cap is None or annual <= cap: break
    return round(tax / 12)

def payroll(base: int, bonus: int, ded: int) -> dict:
    gross = base + bonus
    tax, fica = income_tax_monthly(gross), round(gross * FICA)
    return dict(gross=gross, tax=tax, fica=fica, deductions=ded, net=gross - tax - fica - ded)

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True)
    pw: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="viewer")  # admin | viewer
class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    dept: Mapped[str] = mapped_column(String, default="")
    base: Mapped[int] = mapped_column(Integer)
    bonus: Mapped[int] = mapped_column(Integer, default=0)
    ded: Mapped[int] = mapped_column(Integer, default=0)
class Run(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    month: Mapped[str] = mapped_column(String, unique=True)
    created: Mapped[dt.datetime] = mapped_column(DateTime, default=now)
    rows: Mapped[list] = mapped_column(JSON)  # frozen snapshot of that month

def hash_pw(p: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    return salt + "$" + hashlib.pbkdf2_hmac("sha256", p.encode(), salt.encode(), 200_000).hex()
def check_pw(p: str, stored: str) -> bool:
    return hmac.compare_digest(hash_pw(p, stored.split("$")[0]), stored)

def init_db():
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        if not s.scalar(select(func.count(User.id))):
            admin_pw = os.getenv("LEDGERLY_ADMIN_PW", "admin123")
            viewer_pw = os.getenv("LEDGERLY_VIEWER_PW", "viewer123")
            s.add_all([User(username="admin", pw=hash_pw(admin_pw), role="admin"),
                       User(username="viewer", pw=hash_pw(viewer_pw), role="viewer")])
            for c, n, d, b, bo, de in [("E101","Aarav Mehta","Engineering",9500000,800000,150000),
                ("E102","Priya Nair","Engineering",10200000,1200000,200000),
                ("E201","Daniel Cho","Sales",7200000,2100000,100000),
                ("E301","Lena Fischer","Finance",8100000,400000,120000)]:
                s.add(Employee(code=c, name=n, dept=d, base=b, bonus=bo, ded=de))
            s.commit()

app = FastAPI(title="Ledgerly")
init_db()
bearer = HTTPBearer(auto_error=False)

def db():
    with Session(engine) as s: yield s
def user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if cred is None: raise HTTPException(401, "Please sign in again.")
    try: return jwt.decode(cred.credentials, SECRET, algorithms=["HS256"])
    except Exception: raise HTTPException(401, "Please sign in again.")
def admin(u: dict = Depends(user)) -> dict:
    if u["role"] != "admin": raise HTTPException(403, "Only admins can change payroll data.")
    return u

class Login(BaseModel): username: str; password: str
class EmpIn(BaseModel):
    code: str = Field(min_length=1, max_length=20); name: str = Field(min_length=1, max_length=80)
    dept: str = Field("", max_length=40)
    base: int = Field(ge=0, le=10**10); bonus: int = Field(0, ge=0, le=10**10); ded: int = Field(0, ge=0, le=10**10)

def emp_out(e: Employee) -> dict:
    return dict(id=e.id, code=e.code, name=e.name, dept=e.dept, base=e.base, bonus=e.bonus, ded=e.ded,
                **payroll(e.base, e.bonus, e.ded))

@app.post("/api/login")
def login(b: Login, s: Session = Depends(db)):
    u = s.scalar(select(User).where(User.username == b.username))
    if not u or not check_pw(b.password, u.pw): raise HTTPException(401, "Wrong username or password.")
    exp = now() + dt.timedelta(hours=8)
    return dict(token=jwt.encode(dict(sub=u.username, role=u.role, exp=exp), SECRET, "HS256"), role=u.role, username=u.username)

@app.get("/api/employees")
def list_emps(_: dict = Depends(user), s: Session = Depends(db)):
    return [emp_out(e) for e in s.scalars(select(Employee).order_by(Employee.name))]

@app.post("/api/employees", status_code=201)
def add_emp(b: EmpIn, _: dict = Depends(admin), s: Session = Depends(db)):
    if s.scalar(select(Employee).where(Employee.code == b.code)):
        raise HTTPException(409, "That employee ID already exists.")
    if b.ded > b.base + b.bonus: raise HTTPException(422, "Deductions can't exceed gross pay.")
    e = Employee(**b.model_dump()); s.add(e); s.commit(); return emp_out(e)

@app.put("/api/employees/{eid}")
def edit_emp(eid: int, b: EmpIn, _: dict = Depends(admin), s: Session = Depends(db)):
    e = s.get(Employee, eid)
    if not e: raise HTTPException(404, "Employee not found.")
    clash = s.scalar(select(Employee).where(Employee.code == b.code, Employee.id != eid))
    if clash: raise HTTPException(409, "That employee ID already exists.")
    if b.ded > b.base + b.bonus: raise HTTPException(422, "Deductions can't exceed gross pay.")
    for k, v in b.model_dump().items(): setattr(e, k, v)
    s.commit(); return emp_out(e)

@app.delete("/api/employees/{eid}", status_code=204)
def del_emp(eid: int, _: dict = Depends(admin), s: Session = Depends(db)):
    e = s.get(Employee, eid)
    if not e: raise HTTPException(404, "Employee not found.")
    s.delete(e); s.commit()

@app.post("/api/runs/{month}", status_code=201)
def run_payroll(month: str, _: dict = Depends(admin), s: Session = Depends(db)):
    try: dt.datetime.strptime(month, "%Y-%m")
    except ValueError: raise HTTPException(422, "Month must look like 2026-11.")
    if s.scalar(select(Run).where(Run.month == month)): raise HTTPException(409, f"Payroll for {month} is already finalised.")
    rows = [emp_out(e) for e in s.scalars(select(Employee))]
    if not rows: raise HTTPException(422, "Add employees before running payroll.")
    r = Run(month=month, rows=rows); s.add(r); s.commit()
    return dict(id=r.id, month=month, net=sum(x["net"] for x in rows))

@app.get("/api/runs")
def runs(_: dict = Depends(user), s: Session = Depends(db)):
    return [dict(id=r.id, month=r.month, created=r.created.isoformat(), count=len(r.rows),
                 gross=sum(x["gross"] for x in r.rows), net=sum(x["net"] for x in r.rows))
            for r in s.scalars(select(Run).order_by(Run.month.desc()))]

def safe_cell(v: str) -> str:
    # Stop spreadsheet apps from treating text like "=SUM(...)" as a formula.
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v

@app.get("/api/runs/{rid}/csv")
def run_csv(rid: int, _: dict = Depends(user), s: Session = Depends(db)):
    r = s.get(Run, rid)
    if not r: raise HTTPException(404, "Run not found.")
    out = io.StringIO(); w = csv.writer(out)
    w.writerow(["ID","Name","Department","Gross","Income tax","FICA","Deductions","Net"])
    for x in r.rows:
        w.writerow([safe_cell(x["code"]), safe_cell(x["name"]), safe_cell(x["dept"])]
                   + [f"{x[k]/100:.2f}" for k in ("gross","tax","fica","deductions","net")])
    return Response(out.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="payroll-{r.month}.csv"'})

@app.get("/")
def home(): return HTMLResponse(PAGE)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))


# ---------------- Front-end page (served at /) ----------------
PAGE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ledgerly – Payroll Manager</title>
<style>
:root{--bg:#eef2f4;--s:#fff;--ink:#102a37;--mu:#5d7380;--ln:#d6dfe4;--ac:#1f5fbf;--good:#12805c;--bad:#c23b3b}
@media(prefers-color-scheme:dark){:root{--bg:#0d1a22;--s:#142632;--ink:#e6eef2;--mu:#8fa5b2;--ln:#25404f;--ac:#6aa3ff;--good:#4ccf9f;--bad:#ff7a7a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px 48px}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between}
button,input,select{font:inherit;color:var(--ink)}
button{border:1px solid var(--ln);background:var(--s);padding:8px 14px;border-radius:8px;cursor:pointer}
button.p{background:var(--ac);border-color:var(--ac);color:var(--bg);font-weight:600}
button.l{border:0;background:none;color:var(--ac);padding:4px 6px}button.d{color:var(--bad)}
input,select{width:100%;background:var(--s);border:1px solid var(--ln);border-radius:8px;padding:8px 10px}
.hero{background:var(--ink);color:var(--bg);border-radius:14px;padding:22px;margin:16px 0;display:flex;flex-wrap:wrap;gap:24px;justify-content:space-between}
.big{font-size:40px;font-weight:700;letter-spacing:-.03em}.hero small{opacity:.7;display:block}
.hero b{font-size:20px;display:block}
.panel{background:var(--s);border:1px solid var(--ln);border-radius:12px;padding:16px;margin-top:16px}
.tabs{display:flex;gap:4px;border-bottom:1px solid var(--ln)}
.tabs button{border:0;border-radius:8px 8px 0 0;background:none;color:var(--mu)}.tabs .on{color:var(--ink);font-weight:600;box-shadow:inset 0 -2px var(--ac)}
.sc{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:760px}
th,td{padding:10px 8px;text-align:right;border-bottom:1px solid var(--ln);white-space:nowrap}
th:nth-child(-n+3),td:nth-child(-n+3){text-align:left}th{color:var(--mu);font-weight:500}
.net{color:var(--good);font-weight:600}
.bar{display:grid;grid-template-columns:110px 1fr 90px;gap:10px;align-items:center;margin:6px 0}
.bar i{height:14px;border-radius:7px;background:var(--ac);display:block}
dialog{border:1px solid var(--ln);border-radius:14px;background:var(--s);color:var(--ink);width:min(440px,94vw);padding:20px}
label{display:block;font-size:13px;color:var(--mu);margin:10px 0 4px}.two{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.err{color:var(--bad);min-height:1.4em}.act{display:flex;justify-content:flex-end;gap:8px;margin-top:14px}
#login{max-width:340px;margin:12vh auto}
dl{display:grid;grid-template-columns:1fr auto;gap:6px 12px}dd{margin:0;text-align:right}
@media print{body *{visibility:hidden}#slip,#slip *{visibility:visible}#slip{position:absolute;left:0;top:0}}
</style></head><body><main>
<section id="login" class="panel"><h1 style="margin-top:0">Ledgerly</h1>
<label for="u">Username</label><input id="u" value="admin" autocomplete="username">
<label for="pw">Password</label><input id="pw" type="password" autocomplete="current-password">
<div class="err" id="lerr"></div><button class="p" id="go" style="width:100%">Sign in</button></section>

<section id="app" hidden>
<div class="row"><h1 style="margin:0">Ledgerly</h1><div class="row">
<span id="who" style="color:var(--mu)"></span><button id="add" class="p">Add employee</button><button id="out">Sign out</button></div></div>
<div class="hero"><div><small>Net payroll (current employees)</small><div class="big" id="kNet"></div></div>
<div><small>Employees</small><b id="kN"></b></div><div><small>Income tax + FICA</small><b id="kT"></b></div><div><small>Average net</small><b id="kA"></b></div></div>
<div class="panel"><b>Net pay by department</b><div id="bars"></div></div>
<div class="panel"><div class="tabs"><button class="on" data-t="e">Employees</button><button data-t="r">Payroll history</button></div>
<div id="tE"><div class="row" style="margin:12px 0"><input id="q" placeholder="Search name or ID" style="max-width:300px"></div>
<div class="sc"><table><thead><tr><th>ID</th><th>Name</th><th>Department</th><th>Gross</th><th>Income tax</th><th>FICA</th><th>Deductions</th><th>Net</th><th></th></tr></thead><tbody id="tb"></tbody></table></div></div>
<div id="tR" hidden><div class="row" style="margin:12px 0"><span style="color:var(--mu)">Finalising saves a frozen copy of this month's pay.</span>
<span class="row"><input id="mo" type="month" style="width:auto"><button id="run" class="p">Run payroll</button></span></div>
<div class="sc"><table style="min-width:520px"><thead><tr><th>Month</th><th>Employees</th><th>Gross</th><th>Net</th><th></th></tr></thead><tbody id="rb"></tbody></table></div></div></div>
</section>

<dialog id="fd"><form id="f"><h2 id="ft" style="margin-top:0"></h2>
<label for="c">Employee ID</label><input id="c" required><label for="n">Full name</label><input id="n" required>
<label for="dp">Department</label><input id="dp"><div class="two"><div><label for="b">Monthly base ($)</label><input id="b" required inputmode="decimal"></div>
<div><label for="bo">Bonus ($)</label><input id="bo" inputmode="decimal"></div></div>
<label for="de">Other deductions ($)</label><input id="de" inputmode="decimal"><div class="err" id="ferr"></div>
<div class="act"><button type="button" id="fx">Cancel</button><button class="p">Save employee</button></div></form></dialog>
<dialog id="sd"><div id="slip"></div><div class="act"><button id="sx">Close</button><button class="p" id="sp">Print</button></div></dialog>
</main>
<script>
const $=i=>document.getElementById(i);let T=sessionStorage.getItem("t"),ROLE=sessionStorage.getItem("r"),USER=sessionStorage.getItem("n"),E=[],editing=null;
const usd=c=>"$"+(c/100).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
const esc=s=>String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const cents=s=>{s=(s||"").trim();if(!s)return 0;if(!/^\d+(\.\d{1,2})?$/.test(s))return NaN;return Math.round(parseFloat(s)*100)};
async function req(path,method="GET",body){
 const r=await fetch("/api"+path,{method,headers:{"Content-Type":"application/json",...(T?{Authorization:"Bearer "+T}:{})},body:body?JSON.stringify(body):undefined});
 if(r.status===401&&T){out();throw new Error("Session expired. Sign in again.")}
 if(!r.ok){let m="Something went wrong.";try{const j=await r.json();m=typeof j.detail==="string"?j.detail:"Check the highlighted values and try again."}catch(e){}throw new Error(m)}
 return r}
async function api(path,method="GET",body){const r=await req(path,method,body);return r.status===204?null:r.json()}
function out(){sessionStorage.clear();T=null;$("app").hidden=true;$("login").hidden=false;$("pw").value=""}
async function login(){try{const j=await api("/login","POST",{username:$("u").value,password:$("pw").value});
 T=j.token;ROLE=j.role;USER=j.username;sessionStorage.setItem("t",T);sessionStorage.setItem("r",ROLE);sessionStorage.setItem("n",USER);$("lerr").textContent="";start()}catch(e){$("lerr").textContent=e.message}}
async function start(){$("login").hidden=true;$("app").hidden=false;$("who").textContent=USER?USER+" ("+ROLE+")":"";$("add").hidden=ROLE!=="admin";$("run").hidden=ROLE!=="admin";
 $("mo").value=new Date().toISOString().slice(0,7);await load()}
async function load(){try{E=await api("/employees");draw();const R=await api("/runs");
 $("rb").innerHTML=R.map(r=>`<tr><td>${esc(r.month)}</td><td>${r.count}</td><td>${usd(r.gross)}</td><td class="net">${usd(r.net)}</td><td><button class="l" data-csv="${r.id}" data-m="${esc(r.month)}">Download CSV</button></td></tr>`).join("")||'<tr><td colspan="5" style="text-align:center;color:var(--mu)">No payroll runs yet.</td></tr>'}catch(e){alert(e.message)}}
$("rb").onclick=async ev=>{const b=ev.target.closest("button[data-csv]");if(!b)return;
 try{const r=await req("/runs/"+b.dataset.csv+"/csv"),u=URL.createObjectURL(await r.blob()),a=document.createElement("a");
  a.href=u;a.download="payroll-"+b.dataset.m+".csv";a.click();URL.revokeObjectURL(u)}catch(e){alert(e.message)}};
function draw(){const q=$("q").value.toLowerCase(),A=ROLE==="admin";
 $("tb").innerHTML=E.filter(e=>!q||e.name.toLowerCase().includes(q)||e.code.toLowerCase().includes(q)).map(e=>`<tr><td>${esc(e.code)}</td><td>${esc(e.name)}</td><td>${esc(e.dept||"–")}</td><td>${usd(e.gross)}</td><td>${usd(e.tax)}</td><td>${usd(e.fica)}</td><td>${usd(e.deductions)}</td><td class="net">${usd(e.net)}</td>
 <td><button class="l" data-a="s" data-i="${e.id}">Payslip</button>${A?`<button class="l" data-a="e" data-i="${e.id}">Edit</button><button class="l d" data-a="d" data-i="${e.id}">Delete</button>`:""}</td></tr>`).join("");
 const n=E.reduce((a,e)=>a+e.net,0),t=E.reduce((a,e)=>a+e.tax+e.fica,0),by={};E.forEach(e=>by[e.dept||"Unassigned"]=(by[e.dept||"Unassigned"]||0)+e.net);
 $("kNet").textContent=usd(n);$("kN").textContent=E.length;$("kT").textContent=usd(t);$("kA").textContent=usd(E.length?Math.round(n/E.length):0);
 const mx=Math.max(1,...Object.values(by));$("bars").innerHTML=Object.entries(by).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`<div class="bar"><span>${esc(k)}</span><span><i style="width:${Math.max(0,v)/mx*100}%"></i></span><b>${usd(v)}</b></div>`).join("")}
function form(e){editing=e?e.id:null;$("ft").textContent=e?"Edit employee":"Add employee";$("ferr").textContent="";
 $("c").value=e?e.code:"";$("n").value=e?e.name:"";$("dp").value=e?e.dept:"";$("b").value=e?e.base/100:"";$("bo").value=e&&e.bonus?e.bonus/100:"";$("de").value=e&&e.ded?e.ded/100:"";$("fd").showModal()}
$("f").onsubmit=async ev=>{ev.preventDefault();const b=cents($("b").value),bo=cents($("bo").value),de=cents($("de").value);
 if([b,bo,de].some(isNaN)){$("ferr").textContent="Amounts must be numbers like 5000 or 5000.50.";return}
 try{const body={code:$("c").value.trim(),name:$("n").value.trim(),dept:$("dp").value.trim(),base:b,bonus:bo,ded:de};
  await api(editing?"/employees/"+editing:"/employees",editing?"PUT":"POST",body);$("fd").close();load()}catch(e){$("ferr").textContent=e.message}};
$("tb").onclick=async ev=>{const b=ev.target.closest("button");if(!b)return;const e=E.find(x=>x.id==b.dataset.i),a=b.dataset.a;
 if(a==="e")form(e);
 if(a==="d"&&confirm("Delete "+e.name+"? This can't be undone.")){try{await api("/employees/"+e.id,"DELETE");load()}catch(x){alert(x.message)}}
 if(a==="s"){$("slip").innerHTML=`<h2 style="margin-top:0">Payslip</h2>${esc(e.name)} · ${esc(e.code)}<br><span style="color:var(--mu)">${esc(e.dept||"No department")}</span><dl style="margin:12px 0"><dt>Base</dt><dd>${usd(e.base)}</dd><dt>Bonus</dt><dd>${usd(e.bonus)}</dd><dt>Gross</dt><dd>${usd(e.gross)}</dd><dt>Income tax</dt><dd>-${usd(e.tax)}</dd><dt>FICA</dt><dd>-${usd(e.fica)}</dd><dt>Other deductions</dt><dd>-${usd(e.deductions)}</dd></dl><b style="font-size:18px">Net pay ${usd(e.net)}</b>`;$("sd").showModal()}};
$("run").onclick=async()=>{if(!$("mo").value){alert("Pick a month first.");return}
 if(!confirm("Finalise payroll for "+$("mo").value+"? It can't be changed afterwards."))return;
 try{await api("/runs/"+$("mo").value,"POST");load()}catch(e){alert(e.message)}};
document.querySelectorAll(".tabs button").forEach(b=>b.onclick=()=>{document.querySelectorAll(".tabs button").forEach(x=>x.classList.toggle("on",x===b));$("tE").hidden=b.dataset.t!=="e";$("tR").hidden=b.dataset.t!=="r"});
$("go").onclick=login;$("pw").onkeydown=e=>{if(e.key==="Enter")login()};$("add").onclick=()=>form(null);$("out").onclick=out;
$("fx").onclick=()=>$("fd").close();$("sx").onclick=()=>$("sd").close();$("sp").onclick=()=>print();$("q").oninput=draw;
if(T)start();
</script></body></html>
"""
