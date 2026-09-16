from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')


def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{label}: expected 1 match, got {n}')
    s = s.replace(old, new, 1)


def rep_between(start, end, new, label):
    global s
    i = s.find(start)
    if i < 0:
        raise SystemExit(f'{label}: start marker missing')
    j = s.find(end, i)
    if j < 0:
        raise SystemExit(f'{label}: end marker missing')
    s = s[:i] + new + s[j:]

# ------------------------------------------------------------------
# Version + minimal UI needed for save failure and backup age
# ------------------------------------------------------------------
rep('<!DOCTYPE html>\n<html lang="ja">', '<!DOCTYPE html>\n<!-- ADV STUDIO 2.2 / Data Safety Phase 1 -->\n<html lang="ja">', 'version comment')
rep('<div class="tt" id="hdTitle">暮石村<small>ADV STUDIO</small></div>',
    '<div class="tt" id="hdTitle">暮石村<small>ADV STUDIO 2.2</small></div>', 'header version')
rep('.ref p{margin:5px 0;font-size:12px;line-height:1.75;color:#cfd9e6}\n@media(max-width:700px)',
'''.ref p{margin:5px 0;font-size:12px;line-height:1.75;color:#cfd9e6}
#backupAge{font-size:9px;line-height:1.25;color:#9fb4c9;white-space:nowrap;text-align:center;max-width:64px}
#backupAge.warn{color:#ffc07a}
#saveFailOverlay{position:fixed;inset:0;z-index:140;background:#000c;display:none;align-items:center;justify-content:center;padding:18px}
#saveFailOverlay.on{display:flex}
#saveFailOverlay .sf{width:min(430px,100%);background:#161b22;border:1px solid #ff7a9555;border-radius:14px;padding:14px;box-shadow:0 18px 60px #000b}
#saveFailOverlay h2{font-size:15px;margin:0 0 8px;color:#ffb3c0}
#saveFailOverlay p{font-size:12px;line-height:1.7;color:#dbe6f2;white-space:pre-wrap;word-break:break-word}
@media(max-width:700px)''', 'safety css')

# ------------------------------------------------------------------
# IndexedDB v2: keep existing asset store, add project store.
# Active assets exclude logical trash; raw delete remains for permanent delete/rename internals.
# ------------------------------------------------------------------
assets_block = r'''/* ============ assets (IndexedDB) ============ */
const DBN='kureishi_studio2',DBV=2;
function odb(){return new Promise((s,j)=>{if(!('indexedDB' in window))return j(Error('IndexedDB非対応'));
 const r=indexedDB.open(DBN,DBV);
 r.onupgradeneeded=()=>{const d=r.result;if(!d.objectStoreNames.contains('a'))d.createObjectStore('a',{keyPath:'id'});if(!d.objectStoreNames.contains('project'))d.createObjectStore('project',{keyPath:'key'});};
 r.onsuccess=()=>s(r.result);r.onerror=()=>j(r.error||Error('IndexedDBを開けません'));r.onblocked=()=>j(Error('他のADV STUDIOがデータベースを使用中です'));});}
function dbtx(store,mode,fn){return odb().then(d=>new Promise((s,j)=>{let out;try{const t=d.transaction(store,mode),st=t.objectStore(store);out=fn(st);t.oncomplete=()=>{const v=out&&out.q?out.q.result:out;d.close();s(v);};t.onerror=t.onabort=()=>{const e=t.error||Error(store+' 保存失敗');d.close();j(e);};}catch(e){d.close();j(e);}}));}
function tx(mode,fn){return dbtx('a',mode,fn);}
const aPut=o=>tx('readwrite',st=>({q:st.put(o)})),aDel=i=>tx('readwrite',st=>({q:st.delete(i)})),aAll=()=>tx('readonly',st=>({q:st.getAll()}));
const pGet=()=>dbtx('project','readonly',st=>({q:st.get('current')}));
const pPut=o=>dbtx('project','readwrite',st=>({q:st.put(o)}));
let AS=[];const UC=new Map();
const AX=i=>AS.find(x=>x.id===i);
const A=i=>AS.find(x=>x.id===i&&!x.deleted);
function auid(){return 'a_'+(crypto.randomUUID?crypto.randomUUID():Date.now().toString(36)+Math.random().toString(36).slice(2));}
function url(i){if(!i)return '';const a=A(i);if(!a)return '';if(UC.has(i))return UC.get(i);const u=URL.createObjectURL(a.blob);UC.set(i,u);return u;}
function urlAny(i){if(!i)return '';const a=AX(i);if(!a)return '';if(UC.has(i))return UC.get(i);const u=URL.createObjectURL(a.blob);UC.set(i,u);return u;}
const th=i=>{const a=A(i);return a&&a.thumb?a.thumb:url(i);};
const thAny=i=>{const a=AX(i);return a&&a.thumb?a.thumb:urlAny(i);};
const KIND={bg:'背景/CG',chara:'立ち絵',ui:'UI',bgm:'BGM',se:'SE'};
const PFX={bg:'bg',chara:'fc',ui:'ui',bgm:'bgm',se:'se'};
function nid(kind,base){let n=(base||'').normalize('NFKC').replace(/\.[^.]+$/,'').replace(/[^\w\-]+/g,'_').replace(/^_+|_+$/g,'').toLowerCase();
 if(!n||!/[a-z]/.test(n))n=PFX[kind]+'_'+String(AS.filter(a=>a.kind===kind&&!a.deleted).length+1).padStart(2,'0');
 if(/^\d/.test(n))n=PFX[kind]+'_'+n;let id=n,k=2;while(AX(id))id=n+'_'+(k++);return id;}
function gkind(p){const s=p.toLowerCase(),e=(s.split('.').pop()||'');
 if(['mp3','ogg','wav','m4a','aac','opus','flac'].includes(e))return /se|sfx|効果音/.test(s)?'se':'bgm';
 if(!['png','jpg','jpeg','webp','gif','avif','bmp'].includes(e))return null;
 if(/表情|face|差分|立ち絵|stand|chara/.test(s))return 'chara';
 if(/ui素材|文章ui|ウィンドウ|ウインドウ|名前欄|選択肢|フレーム|枠|window|frame|ログ画面|システムメッセージ|侵食|回想|暗転|古文書|記録用紙|研究ノート|日記|手紙/.test(s))return 'ui';
 return 'bg';}
const MIME=n=>({png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg',webp:'image/webp',gif:'image/gif',mp3:'audio/mpeg',ogg:'audio/ogg',wav:'audio/wav',m4a:'audio/mp4'}[(n.split('.').pop()||'').toLowerCase()]||'application/octet-stream');

async function mkThumb(blob,max){try{const u=URL.createObjectURL(blob),i=await loadImg(u);
 const k=Math.min(1,max/Math.max(i.width,i.height)),c=document.createElement('canvas');
 c.width=Math.max(1,Math.round(i.width*k));c.height=Math.max(1,Math.round(i.height*k));
 c.getContext('2d').drawImage(i,0,0,c.width,c.height);URL.revokeObjectURL(u);
 return {thumb:c.toDataURL('image/jpeg',.72),w:i.width,h:i.height};}catch(e){return {thumb:'',w:0,h:0};}}
async function shrink(blob,max,q){const u=URL.createObjectURL(blob),i=await loadImg(u);
 const k=Math.min(1,max/Math.max(i.width,i.height));if(k>=1){URL.revokeObjectURL(u);return blob;}
 const c=document.createElement('canvas');c.width=Math.round(i.width*k);c.height=Math.round(i.height*k);
 c.getContext('2d').drawImage(i,0,0,c.width,c.height);URL.revokeObjectURL(u);
 const hasA=/png|webp/.test(blob.type);
 return await new Promise(r=>c.toBlob(r,hasA?'image/png':'image/jpeg',q||.86));}

async function addBlob(blob,name,kindForce){
 const kind=kindForce||gkind(name)||'bg';
 let b=blob;
 if(P.settings.autoShrink&&/^image\//.test(blob.type||MIME(name))&&kind!=='ui'){try{b=await shrink(blob,1280,.86);}catch(e){}}
 const rec={uid:auid(),id:nid(kind,name),name,kind,mime:b.type||MIME(name),size:b.size,blob:b,meta:{},deleted:false};
 if(/^image\//.test(rec.mime)){const t=await mkThumb(b,200);rec.thumb=t.thumb;rec.meta.w=t.w;rec.meta.h=t.h;}
 await aPut(rec);AS.push(rec);return rec;}
async function addFiles(fs,kf){let n=0;for(const f of fs){await addBlob(f,f.name,kf);n++;}toast(n+'件追加');rAssets();}

'''
rep_between('/* ============ assets (IndexedDB) ============ */', '/* ---- zip read ---- */', assets_block, 'indexeddb/assets block')

# ------------------------------------------------------------------
# Project persistence, migration, failure modal, backup timer, history incl. asset mutations
# ------------------------------------------------------------------
project_block = r'''let P=null,hist=[],hi=-1,cs=0,sel=0,mode='card',errs={};
const STUDIO_VERSION='2.2',LS_PROJECT='kv_proj2',LS_BACKUP_META='kv_backup_meta2',LS_IOS_NOTICE='kv_ios_home_notice2';
let storageMode='idb',projectMigrated=false,emergencyLoaded=false,_sv=null,_savePromise=null,saveFailed=false,savePending=false,saveState='保存済',saveRev=0,savedRev=0,historyBusy=false;
let backupWarned=false;
function normalizeProject(o){
 if(!o||!Array.isArray(o.scenes)||!o.scenes.length)throw Error('シーンがありません');
 const p=JSON.parse(JSON.stringify(o));p.title=String(p.title||'暮石村');
 for(const key of ['scenes','characters','themes']){if(key!=='scenes'&&!Array.isArray(p[key]))p[key]=JSON.parse(JSON.stringify(DEF[key]));if(key==='themes'&&!p[key].length)p[key]=JSON.parse(JSON.stringify(DEF.themes));
 const ids=new Set();p[key].forEach((v,i)=>{if(!v||typeof v!=='object'||Array.isArray(v))throw Error(key+' のデータが不正です');v.id=String(v.id||key+'_'+(i+1));if(!/^[\w-]+$/.test(v.id)||['__proto__','constructor','prototype'].includes(v.id)||ids.has(v.id))throw Error('IDの重複または不正: '+v.id);ids.add(v.id);});}
 p.settings=Object.assign({},DEF.settings,p.settings||{});
 p.scenes.forEach(v=>{v.title=String(v.title||v.id);v.script=String(v.script||'');});
 p.characters.forEach(c=>{c.name=String(c.name||c.id);c.faces=c.faces&&typeof c.faces==='object'?c.faces:{};if(c.faces.happy&&!c.faces.smile)c.faces.smile=c.faces.happy;});
 p.themes.forEach(t=>{t.name=String(t.name||t.id);t.slots=t.slots||{};t.font=Object.assign(DFONT(),t.font||{});t.nameFont=Object.assign({f:'mincho',size:14,color:'#fff'},t.nameFont||{});});return p;
}
function parseLegacyProject(raw){const x=JSON.parse(raw);if(x&&x._emergency===2&&x.project){emergencyLoaded=!!x.truncated;return x.project;}return x;}
function emergencySnapshot(p){const q=JSON.parse(JSON.stringify(p));let remain=420000,truncated=false;
 q.scenes=q.scenes.map((sc,idx)=>{const o={...sc},txt=String(sc.script||''),left=Math.max(1,q.scenes.length-idx),cap=Math.max(1200,Math.min(10000,Math.floor(remain/left)));
  if(txt.length>cap){const h=Math.max(500,Math.floor((cap-80)/2));o.script=txt.slice(0,h)+'\n// [緊急スナップショット: 中間省略]\n'+txt.slice(-h);truncated=true;}else o.script=txt;remain=Math.max(0,remain-o.script.length);return o;});
 return {_emergency:2,savedAt:Date.now(),truncated,project:q};}
function writeEmergencySnapshot(){if(storageMode!=='idb')return;try{localStorage.setItem(LS_PROJECT,JSON.stringify(emergencySnapshot(P)));}catch(e){}}
async function loadP(){let raw=null;try{raw=localStorage.getItem(LS_PROJECT);}catch(e){}
 try{const rec=await pGet();storageMode='idb';
  if(rec&&rec.value){P=normalizeProject(rec.value);return;}
  if(raw){P=normalizeProject(parseLegacyProject(raw));await pPut({key:'current',value:P,savedAt:Date.now(),version:STUDIO_VERSION});projectMigrated=true;writeEmergencySnapshot();return;}
  P=normalizeProject(DEF);await pPut({key:'current',value:P,savedAt:Date.now(),version:STUDIO_VERSION});writeEmergencySnapshot();
 }catch(idbErr){storageMode='local';try{P=normalizeProject(raw?parseLegacyProject(raw):DEF);}catch(e){P=normalizeProject(DEF);toast('保存データを読み込めません。バックアップから復元してください');}
  if(emergencyLoaded)setTimeout(()=>sheet('緊急スナップショットで起動しました','<p class="wn">IndexedDBを利用できないため、軽量スナップショットから起動しました。長いシーン本文は一部省略されている可能性があります。編集前にフルバックアップZIPからの復元を推奨します。</p>'),300);}}
function saveBadge(){let b=$('#saveState');if(!b){b=document.createElement('small');b.id='saveState';b.setAttribute('role','status');$('header').appendChild(b);}b.textContent=saveState;b.style.color=saveFailed?'#ff8585':'#a7ceb8';}
function ensureSaveFailModal(){let m=$('#saveFailOverlay');if(m)return m;m=document.createElement('div');m.id='saveFailOverlay';m.innerHTML='<div class="sf"><h2>保存に失敗しました</h2><p id="sfReason"></p><div class="row"><button class="btn ac" id="sfBackup" style="flex:1">今すぐフルバックアップZIPを保存</button><button class="btn" id="sfRetry">保存を再試行</button></div><button class="btn" id="sfContinue" style="width:100%;margin-top:8px" disabled>バックアップ後に編集へ戻る</button></div>';document.body.appendChild(m);return m;}
function hideSaveFailure(){const m=$('#saveFailOverlay');if(m)m.classList.remove('on');}
function showSaveFailure(e){const m=ensureSaveFailModal(),r=$('#sfReason',m),bk=$('#sfBackup',m),rt=$('#sfRetry',m),ct=$('#sfContinue',m);let backed=false;r.textContent='原因: '+((e&&e.name?e.name+': ':'')+(e&&e.message?e.message:String(e||'不明なエラー')))+'\n編集内容はメモリ上には残っています。まずフルバックアップを保存してください。';ct.disabled=true;m.classList.add('on');
 bk.onclick=async()=>{const ok=await backup();if(ok){backed=true;ct.disabled=false;ct.textContent='バックアップ済み・編集へ戻る';}};
 rt.onclick=async()=>{if(await flushSave(true)){hideSaveFailure();toast('保存できました');}};
 ct.onclick=()=>{if(backed)hideSaveFailure();};}
async function flushSave(force){clearTimeout(_sv);if(_savePromise){const ok=await _savePromise;if(saveRev>savedRev)return flushSave(true);return ok;}const rev=saveRev;savePending=true;saveState='保存中';saveBadge();_savePromise=(async()=>{try{if(storageMode==='idb')await pPut({key:'current',value:JSON.parse(JSON.stringify(P)),savedAt:Date.now(),version:STUDIO_VERSION});else localStorage.setItem(LS_PROJECT,JSON.stringify(P));savedRev=Math.max(savedRev,rev);saveFailed=false;saveState='保存済';if(storageMode==='idb')writeEmergencySnapshot();hideSaveFailure();return true;}catch(e){saveFailed=true;saveState='保存失敗：バックアップしてください';showSaveFailure(e);return false;}finally{savePending=false;saveBadge();}})();const ok=await _savePromise;_savePromise=null;if(ok&&saveRev>savedRev)saveP();return ok;}
function saveP(){saveRev++;saveState='保存中';saveBadge();clearTimeout(_sv);_sv=setTimeout(()=>{void flushSave();},250);}
function readBackupMeta(){try{return Object.assign({at:0,edits:0,firstSeen:Date.now()},JSON.parse(localStorage.getItem(LS_BACKUP_META)||'{}'));}catch(e){return {at:0,edits:0,firstSeen:Date.now()};}}
let backupMeta=readBackupMeta();
function storeBackupMeta(){try{localStorage.setItem(LS_BACKUP_META,JSON.stringify(backupMeta));}catch(e){}}
function backupDue(){const base=backupMeta.at||backupMeta.firstSeen||Date.now();return Date.now()-base>=3600000||backupMeta.edits>=100;}
function updateBackupAge(){let b=$('#backupAge');if(!b){b=document.createElement('small');b.id='backupAge';$('header').appendChild(b);}const base=backupMeta.at||backupMeta.firstSeen||Date.now(),mins=Math.max(0,Math.floor((Date.now()-base)/60000));b.textContent=backupMeta.at?('BK '+(mins<60?mins+'分':Math.floor(mins/60)+'h')):'BK 未作成';b.classList.toggle('warn',backupDue());}
function noteEdit(){backupMeta.edits=(backupMeta.edits||0)+1;storeBackupMeta();updateBackupAge();if(backupDue()&&!backupWarned){backupWarned=true;toast('フルバックアップをおすすめします');}}
function markFullBackup(){backupMeta={at:Date.now(),edits:0,firstSeen:backupMeta.firstSeen||Date.now()};backupWarned=false;storeBackupMeta();updateBackupAge();}
setInterval(updateBackupAge,60000);
function maybeIOSNotice(){try{const ios=/iPad|iPhone|iPod/.test(navigator.userAgent),standalone=navigator.standalone===true||matchMedia('(display-mode: standalone)').matches;if(!ios||standalone||localStorage.getItem(LS_IOS_NOTICE))return false;localStorage.setItem(LS_IOS_NOTICE,'1');sheet('iPhoneでの利用について','<p>データ保全のため、Safariの共有メニューから「ホーム画面に追加」し、以後は追加した <b>my studio</b> のアイコンから開いてください。</p><p class="sb">iOSは状況によりWebサイトの保存領域を整理することがあります。フルバックアップZIPも定期的に保存してください。</p>');return true;}catch(e){return false;}}
function assetHistoryState(){return AS.map(a=>({uid:a.uid||'',id:a.id,name:a.name,kind:a.kind,mime:a.mime,size:a.size||0,meta:JSON.parse(JSON.stringify(a.meta||{})),thumb:a.thumb||'',deleted:!!a.deleted,deletedAt:a.deletedAt||0})).sort((a,b)=>(a.uid||a.id).localeCompare(b.uid||b.id));}
function snapState(){const x={p:JSON.stringify(P),assets:assetHistoryState()};x.sig=x.p+'|'+JSON.stringify(x.assets);return x;}
function initHistory(){const x=snapState();hist=[x];hi=0;hdr();}
function resetHistory(){const x=snapState();hist=[x];hi=0;saveP();hdr();}
async function applyAssetHistory(meta){for(const m of meta||[]){let a=AS.find(x=>(x.uid||x.id)===(m.uid||m.id));if(!a)continue;const oldId=a.id;if(oldId!==m.id){const clash=AX(m.id);if(clash&&clash!==a)throw Error('Undo先の素材IDが使用中です: '+m.id);const next={...a,...m,blob:a.blob};await aPut(next);await aDel(oldId);if(UC.has(oldId)){URL.revokeObjectURL(UC.get(oldId));UC.delete(oldId);}Object.assign(a,next);}else{Object.assign(a,m,{blob:a.blob});await aPut(a);}}}
async function applyHistory(x){await applyAssetHistory(x.assets);P=JSON.parse(x.p);saveP();const t=$('nav button.sel')?.dataset.t||'sc';tab(t);hdr();}
function push(){const x=snapState(),cur=hist[hi];if(cur&&x.sig===cur.sig)return;hist=hist.slice(0,hi+1);hist.push(x);if(hist.length>40)hist.shift();hi=hist.length-1;saveP();noteEdit();hdr();}
async function undo(){if(historyBusy||hi<=0)return;historyBusy=true;try{hi--;await applyHistory(hist[hi]);noteEdit();}catch(e){hi++;toast('Undo失敗: '+e.message);}finally{historyBusy=false;hdr();}}
async function redo(){if(historyBusy||hi>=hist.length-1)return;historyBusy=true;try{hi++;await applyHistory(hist[hi]);noteEdit();}catch(e){hi--;toast('Redo失敗: '+e.message);}finally{historyBusy=false;hdr();}}
function hdr(){saveBadge();updateBackupAge();cs=Math.max(0,Math.min(cs,P.scenes.length-1));$('#hdTitle').innerHTML=esc(P.title||'暮石村')+'<small>ADV STUDIO '+STUDIO_VERSION+'</small>';$('#bUndo').disabled=hi<=0||historyBusy;$('#bRedo').disabled=hi>=hist.length-1||historyBusy;}
const theme=id=>P.themes.find(t=>t.id===id)||P.themes[0];
const chara=id=>P.characters.find(c=>c.id===id);
const nkey=s=>String(s||'').replace(/[\s　]/g,'');

'''
rep_between('let P=null,hist=[],hi=-1,cs=0,sel=0,mode=\'card\',errs={};', '/* ============ script parse / serialize ============ */', project_block, 'project persistence/history block')

# ------------------------------------------------------------------
# Asset tab: logical trash + restore + permanent delete + reference confirmation
# ------------------------------------------------------------------
asset_ui = r'''/* ============ assets tab ============ */
function rAssets(){const f=rAssets.f||'all',active=AS.filter(a=>!a.deleted),trash=AS.filter(a=>a.deleted),ls=active.filter(a=>f==='all'||a.kind===f);
 const tot=active.reduce((n,a)=>n+(a.size||0),0),tt=trash.reduce((n,a)=>n+(a.size||0),0);
 $('#t-as').innerHTML='<div class="card"><h3>素材を追加</h3><div class="row">'+
  '<button class="btn ac" id="aA">画像・音声</button><button class="btn" id="aZ">ZIP取り込み</button><button class="btn" id="aTrash">ゴミ箱 '+trash.length+'</button></div>'+
  '<div class="sb" style="margin-top:6px">ファイル名から種類（背景／立ち絵／UI／BGM）を自動判定します。素材シートは登録後に「切り出し」で分割できます。</div></div>'+
  '<div class="chips">'+['all','bg','chara','ui','bgm','se'].map(k=>'<button class="chip'+(f===k?' sel':'')+'" data-f="'+k+'">'+
   (k==='all'?'すべて':KIND[k])+' '+(k==='all'?active.length:active.filter(a=>a.kind===k).length)+'</button>').join('')+'</div>'+
  '<div class="sb" style="padding:2px 2px 7px">使用中 '+fsz(tot)+(trash.length?' / ゴミ箱 '+fsz(tt):'')+'（端末内保存）</div>'+
  '<div class="grid">'+(ls.length?ls.map(a=>'<div class="as" data-i="'+esc(a.id)+'">'+
   (a.kind==='bgm'||a.kind==='se'?'<div class="au">♪</div>':'<img src="'+th(a.id)+'" loading="lazy">')+
   '<div class="bd">'+KIND[a.kind]+(a.meta&&a.meta.safe?' ◱':'')+'</div>'+
   '<div class="id">'+esc(a.id)+'</div><div class="nm">'+esc(a.name)+'</div></div>').join('')
   :'<div class="sb">素材がありません。</div>')+'</div>';
 $('#aA').onclick=()=>$('#fAs').click();$('#aZ').onclick=()=>$('#fZip').click();$('#aTrash').onclick=trashSheet;
 $$('#t-as .chip').forEach(b=>b.onclick=()=>{rAssets.f=b.dataset.f;rAssets();});
 $$('#t-as .as').forEach(c=>c.onclick=()=>asSheet(c.dataset.i));}
function asSheet(id){const a=A(id);if(!a)return;const img=/^image\//.test(a.mime||'');
 sheet('素材：'+a.name,(img?'<img src="'+url(id)+'" style="width:100%;border-radius:9px;background:#000">':
  '<audio controls src="'+url(id)+'" style="width:100%"></audio>')+
  '<label class="f">素材ID</label><input type="text" id="sId" value="'+esc(a.id)+'">'+
  '<label class="f">種類</label><select id="sKd">'+Object.keys(KIND).map(k=>'<option value="'+k+'"'+(k===a.kind?' selected':'')+'>'+KIND[k]+'</option>').join('')+'</select>'+
  '<div class="row" style="margin-top:10px"><button class="btn ac" id="sOK">保存</button>'+
  (img?'<button class="btn" id="sCal">文字位置を調整</button><button class="btn" id="sCrop">切り出し</button><button class="btn" id="sShr">軽量化</button>':'')+
  '<button class="btn dg" id="sDel">ゴミ箱へ</button></div>'+
  '<div class="sb" style="margin-top:6px">'+fsz(a.size||0)+(a.meta&&a.meta.w?' / '+a.meta.w+'×'+a.meta.h+'px':'')+'</div>',()=>{
  $('#sOK').onclick=async()=>{const ni=$('#sId').value.trim().replace(/\s+/g,'_'),nk=$('#sKd').value;
   if(!ni)return toast('IDを入力');if(ni!==a.id&&AX(ni))return toast('同名のIDが存在します（ゴミ箱内を含む）');
   try{await renameAsset(a,ni,nk);shClose();rAssets();rScene();toast('更新しました');}catch(e){toast('保存失敗: '+e.message);}};
  if(img){
   $('#sCal').onclick=()=>{shClose();calib(id);};
   $('#sCrop').onclick=()=>{shClose();crop(id);};
   $('#sShr').onclick=async()=>{const b=await shrink(a.blob,1280,.86);if(b.size>=a.size)return toast('これ以上小さくなりません');
    a.blob=b;a.size=b.size;const t=await mkThumb(b,200);a.thumb=t.thumb;a.meta.w=t.w;a.meta.h=t.h;
    await aPut(a);UC.delete(id);shClose();rAssets();toast('軽量化しました（'+fsz(b.size)+'）');};}
  $('#sDel').onclick=()=>requestTrashAsset(id);});}
function usageHTML(refs){return refs.length?'<div class="lst2">'+refs.map(x=>'<div class="it"><div class="g"><b>'+esc(x.label)+'</b></div></div>').join('')+'</div>':'<p class="sb">使用箇所はありません。</p>';}
function requestTrashAsset(id){const a=A(id);if(!a)return;const refs=assetUsage(id);if(!refs.length){if(!confirm('この素材をゴミ箱へ移動しますか？（Undo・復元できます）'))return;void softDeleteAsset(id);return;}
 sheet('使用中の素材をゴミ箱へ','<p class="wn">この素材は現在使用されています。ゴミ箱へ移動すると、その箇所は素材不足になります。</p>'+usageHTML(refs)+'<button class="btn dg" id="trashGo" style="width:100%;margin-top:9px">確認してゴミ箱へ移動</button>',()=>{$('#trashGo').onclick=async()=>{await softDeleteAsset(id);shClose();};});}
async function softDeleteAsset(id){const a=A(id);if(!a)return;a.deleted=true;a.deletedAt=Date.now();await aPut(a);if(UC.has(id)){URL.revokeObjectURL(UC.get(id));UC.delete(id);}push();rAssets();rebuildPreview();toast('ゴミ箱へ移動しました');}
async function restoreAsset(id){const a=AX(id);if(!a||!a.deleted)return;a.deleted=false;a.deletedAt=0;await aPut(a);push();rAssets();rebuildPreview();toast('素材を復元しました');}
async function permanentDeleteAsset(id){const a=AX(id);if(!a||!a.deleted)return;const refs=assetUsage(id),msg=(refs.length?'まだ '+refs.length+' 箇所から参照されています。\n':'')+'完全削除すると元に戻せません。実行しますか？';if(!confirm(msg))return;await aDel(id);AS=AS.filter(x=>x!==a);if(UC.has(id)){URL.revokeObjectURL(UC.get(id));UC.delete(id);}resetHistory();trashSheet();toast('完全削除しました');}
function trashSheet(){const ls=AS.filter(a=>a.deleted);sheet('素材ゴミ箱',ls.length?'<div class="lst2">'+ls.map(a=>'<div class="it" data-trash="'+esc(a.id)+'">'+(a.kind==='bgm'||a.kind==='se'?'<div style="width:36px;text-align:center">♪</div>':'<img src="'+thAny(a.id)+'">')+'<div class="g"><b>'+esc(a.id)+'</b><div class="s">'+esc(a.name)+' / '+KIND[a.kind]+'</div></div><button class="btn sm" data-restore="'+esc(a.id)+'">復元</button><button class="btn sm dg" data-purge="'+esc(a.id)+'">完全削除</button></div>').join('')+'</div>':'<p class="sb">ゴミ箱は空です。</p>',()=>{$$('#sh [data-restore]').forEach(b=>b.onclick=()=>restoreAsset(b.dataset.restore));$$('#sh [data-purge]').forEach(b=>b.onclick=()=>permanentDeleteAsset(b.dataset.purge));});}

'''
rep_between('/* ============ assets tab ============ */', '/* ---- safe area calibrate ---- */', asset_ui, 'asset trash UI')

# ------------------------------------------------------------------
# Backup: include trash metadata, and record successful full backup time
# ------------------------------------------------------------------
old_backup = "async function backup(){if(AS.reduce((n,a)=>n+a.size,0)>150*1048576&&!confirm('素材が150MBを超えます。バックアップを作成しますか？'))return;toast('バックアップ作成中…');const files=[],enc=new TextEncoder(),idx=[];\n for(const a of AS){const fn='assets/'+a.id+'.'+EXT(a);idx.push({id:a.id,name:a.name,kind:a.kind,file:fn,meta:a.meta||{}});\n  files.push({name:fn,data:new Uint8Array(await a.blob.arrayBuffer())});}\n files.push({name:'project.json',data:enc.encode(JSON.stringify(P,null,1))});\n files.push({name:'assets.json',data:enc.encode(JSON.stringify(idx,null,1))});\n dl(zipWrite(files),(P.title||'kureishi')+'_backup_'+new Date().toISOString().slice(0,10)+'.zip');toast('完了');}"
new_backup = "async function backup(){try{if(AS.reduce((n,a)=>n+a.size,0)>150*1048576&&!confirm('素材が150MBを超えます。バックアップを作成しますか？'))return false;toast('バックアップ作成中…');const files=[],enc=new TextEncoder(),idx=[];\n for(const a of AS){const fn='assets/'+a.id+'.'+EXT(a);idx.push({uid:a.uid||auid(),id:a.id,name:a.name,kind:a.kind,mime:a.mime,file:fn,meta:a.meta||{},deleted:!!a.deleted,deletedAt:a.deletedAt||0});\n  files.push({name:fn,data:new Uint8Array(await a.blob.arrayBuffer())});}\n files.push({name:'project.json',data:enc.encode(JSON.stringify(P,null,1))});\n files.push({name:'assets.json',data:enc.encode(JSON.stringify(idx,null,1))});\n dl(zipWrite(files),(P.title||'kureishi')+'_backup_'+new Date().toISOString().slice(0,10)+'.zip');markFullBackup();toast('フルバックアップ完了');return true;}catch(e){toast('バックアップ失敗: '+e.message);return false;}}"
rep(old_backup, new_backup, 'backup function')

# ------------------------------------------------------------------
# Existing Studio safety helpers: detailed asset refs and undoable rename
# ------------------------------------------------------------------
rep("/* Studio 2.1: safe operations and guided editing */", "/* Studio 2.2: data safety and guided editing */", 'studio version comment')
old_refs = "function assetRefs(id){const refs=[];P.scenes.forEach(s=>{if(parseScript(s.script,P.characters).ops.some(o=>assetFields(o).some(k=>o.args?.[k]===id)))refs.push('シーン：'+s.title);});P.characters.forEach(c=>Object.entries(c.faces||{}).forEach(([k,v])=>{if(v===id)refs.push(c.name+' / '+k);}));P.themes.forEach(t=>Object.entries(t.slots||{}).forEach(([k,v])=>{if(v===id)refs.push(t.name+' / '+k);}));return refs;}"
new_refs = "function assetUsage(id){const refs=[];P.scenes.forEach((sc,si)=>parseScript(sc.script,P.characters).ops.forEach(o=>{if(assetFields(o).some(k=>o.args?.[k]===id)){const nm=(CMD[o.cmd]&&CMD[o.cmd].l)||o.cmd;refs.push({type:'scene',scene:si,line:o.ln0+1,cmd:o.cmd,label:'シーン「'+sc.title+'」 / '+(o.ln0+1)+'行 / '+nm+' (@'+o.cmd+')'});}}));P.characters.forEach(c=>Object.entries(c.faces||{}).forEach(([k,v])=>{if(v===id)refs.push({type:'character',label:'キャラ「'+c.name+'」 / 表情 '+k});}));P.themes.forEach(t=>Object.entries(t.slots||{}).forEach(([k,v])=>{if(v===id)refs.push({type:'theme',label:'UIテーマ「'+t.name+'」 / '+k});}));return refs;}\nfunction assetRefs(id){return assetUsage(id).map(x=>x.label);}"
rep(old_refs, new_refs, 'asset usage')
old_rename = "async function renameAsset(a,id,kind){if(!/^[\\w-]+$/.test(id)||['__proto__','constructor','prototype'].includes(id))throw Error('IDは半角英数字・_・-で指定してください');const old=a.id,previous=JSON.stringify(P),next={...a,id,kind};await aPut(next);try{if(old!==id)replaceAssetRefs(old,id);if(!flushSave())throw Error('シナリオを保存できません');}catch(e){P=JSON.parse(previous);if(old!==id)await aDel(id);throw e;}Object.assign(a,next);if(old!==id){await aDel(old);if(UC.has(old))URL.revokeObjectURL(UC.get(old));UC.delete(old);}resetHistory();}"
new_rename = "async function renameAsset(a,id,kind){if(!/^[\\w-]+$/.test(id)||['__proto__','constructor','prototype'].includes(id))throw Error('IDは半角英数字・_・-で指定してください');if(id!==a.id&&AX(id))throw Error('同じIDがゴミ箱内を含めて存在します');const old=a.id,previousP=JSON.stringify(P),previous={...a,meta:JSON.parse(JSON.stringify(a.meta||{}))},next={...a,id,kind};try{if(old!==id){await aPut(next);replaceAssetRefs(old,id);Object.assign(a,next);await aDel(old);if(UC.has(old)){URL.revokeObjectURL(UC.get(old));UC.delete(old);}}else{Object.assign(a,next);await aPut(a);}if(!await flushSave(true))throw Error('シナリオを保存できません');push();}catch(e){P=JSON.parse(previousP);if(old!==id){try{await aPut(previous);await aDel(id);}catch(_){}Object.assign(a,previous);}else Object.assign(a,previous);throw e;}}"
rep(old_rename, new_rename, 'undoable asset rename')

# preflight must await the asynchronous durable save
rep("async function preflight(){flushSave();const warnings=validate(true)", "async function preflight(){await flushSave(true);const warnings=validate(true)", 'preflight save')

# ------------------------------------------------------------------
# Restore old/new backups, async save semantics, boot migration and iOS notice
# ------------------------------------------------------------------
old_restore = "async function writeAssetSet(records){await tx('readwrite',s=>{s.clear();records.forEach(a=>s.put(a));});}\nasync function restoreBackup(file,ask=true){const en=await unzip(file),get=n=>en.find(e=>e.name===n||e.name.endsWith('/'+n));const dec=e=>JSON.parse(new TextDecoder().decode(e.data));if(!get('project.json')||!get('assets.json'))throw Error('フルバックアップZIPを選んでください');const p=normalizeProject(dec(get('project.json'))),idx=dec(get('assets.json'));if(!Array.isArray(idx))throw Error('素材一覧が不正です');const seen=new Set(),records=[];for(const a of idx){if(!/^[\\w-]+$/.test(a.id)||['__proto__','constructor','prototype'].includes(a.id)||seen.has(a.id)||!KIND[a.kind])throw Error('素材IDまたは種類が不正です');seen.add(a.id);const data=get(a.file);if(!data)throw Error('素材が不足: '+a.file);const blob=new Blob([data.data],{type:a.mime||MIME(a.file)}),r={...a,blob,mime:blob.type,size:blob.size,meta:a.meta||{}};if(/^image\\//.test(r.mime)){const t=await mkThumb(blob,200);r.thumb=t.thumb;r.meta={...r.meta,w:t.w,h:t.h};if(!t.w)throw Error('画像を読めません: '+a.name);}records.push(r);}\n if(ask&&!confirm('現在のシナリオと素材をバックアップの内容で置き換えます。必要な作業は先にバックアップしてください。続けますか？'))return false;\n const previousP=P,previousAS=AS;await writeAssetSet(records);P=p;if(!flushSave()){P=previousP;await writeAssetSet(previousAS);throw Error('保存容量が不足しています。元のデータを維持しました');}UC.forEach(u=>URL.revokeObjectURL(u));UC.clear();AS=records;cs=0;sel=Math.max(0,parseScript(P.scenes[0].script,P.characters).ops.findIndex(o=>o.cmd==='msg'));resetHistory();tab('sc');toast(records.length+'素材とシナリオを復元しました');return true;}"
new_restore = "async function writeAssetSet(records){await tx('readwrite',s=>{s.clear();records.forEach(a=>s.put(a));});}\nasync function restoreBackup(file,ask=true){const en=await unzip(file),get=n=>en.find(e=>e.name===n||e.name.endsWith('/'+n));const dec=e=>JSON.parse(new TextDecoder().decode(e.data));if(!get('project.json')||!get('assets.json'))throw Error('フルバックアップZIPを選んでください');const p=normalizeProject(dec(get('project.json'))),idx=dec(get('assets.json'));if(!Array.isArray(idx))throw Error('素材一覧が不正です');const seen=new Set(),records=[];for(const a of idx){if(!/^[\\w-]+$/.test(a.id)||['__proto__','constructor','prototype'].includes(a.id)||seen.has(a.id)||!KIND[a.kind])throw Error('素材IDまたは種類が不正です');seen.add(a.id);const data=get(a.file);if(!data)throw Error('素材が不足: '+a.file);const blob=new Blob([data.data],{type:a.mime||MIME(a.file)}),r={...a,uid:a.uid||auid(),blob,mime:a.mime||blob.type,size:blob.size,meta:a.meta||{},deleted:!!a.deleted,deletedAt:a.deletedAt||0};if(/^image\\//.test(r.mime)){const t=await mkThumb(blob,200);r.thumb=t.thumb;r.meta={...r.meta,w:t.w,h:t.h};if(!t.w)throw Error('画像を読めません: '+a.name);}records.push(r);}\n if(ask&&!confirm('現在のシナリオと素材をバックアップの内容で置き換えます。必要な作業は先にバックアップしてください。続けますか？'))return false;\n const previousP=P,previousAS=AS;await writeAssetSet(records);P=p;AS=records;if(!await flushSave(true)){P=previousP;AS=previousAS;await writeAssetSet(previousAS);throw Error('プロジェクトを保存できません。元のデータを維持しました');}UC.forEach(u=>URL.revokeObjectURL(u));UC.clear();cs=0;sel=Math.max(0,parseScript(P.scenes[0].script,P.characters).ops.findIndex(o=>o.cmd==='msg'));resetHistory();tab('sc');toast(records.length+'素材とシナリオを復元しました');return true;}"
rep(old_restore, new_restore, 'backup restore')

old_before = "window.addEventListener('beforeunload',e=>{if(!flushSave()){e.preventDefault();e.returnValue='';}});window.addEventListener('unhandledrejection',e=>toast('操作に失敗しました: '+(e.reason?.message||e.reason)));"
new_before = "window.addEventListener('beforeunload',e=>{void flushSave(true);if(saveFailed||savePending){e.preventDefault();e.returnValue='';}});window.addEventListener('unhandledrejection',e=>toast('操作に失敗しました: '+(e.reason?.message||e.reason)));"
rep(old_before, new_before, 'beforeunload')

# Old sync pagehide handlers were part of the replaced project block; add durable async triggers after saveP definition area.
needle = "function saveP(){saveRev++;saveState='保存中';saveBadge();clearTimeout(_sv);_sv=setTimeout(()=>{void flushSave();},250);}\n"
rep(needle, needle+"window.addEventListener('pagehide',()=>{void flushSave(true);});document.addEventListener('visibilitychange',()=>{if(document.hidden)void flushSave(true);});\n", 'pagehide visibility')

old_boot = "(async function boot(){loadP();hdr();\n try{AS=(await aAll())||[];}catch(e){AS=[];}\n AS.sort((a,b)=>a.kind.localeCompare(b.kind)||a.id.localeCompare(b.id));\n sel=Math.max(0,parseScript(P.scenes[0].script,P.characters).ops.findIndex(o=>o.cmd==='msg'));tab('sc');\n if(!AS.length){if(location.protocol.startsWith('http')){try{const response=await fetch('starter_backup.zip');if(response.ok){await restoreBackup(await response.blob(),false);return;}}catch(e){}}helpStudio();}})();"
new_boot = "(async function boot(){await loadP();hdr();\n try{AS=(await aAll())||[];let dirty=false;for(const a of AS){if(!a.uid){a.uid=auid();dirty=true;}if(a.deleted===undefined)a.deleted=false;}if(dirty)for(const a of AS)await aPut(a);}catch(e){AS=[];}\n AS.sort((a,b)=>a.kind.localeCompare(b.kind)||a.id.localeCompare(b.id));initHistory();\n sel=Math.max(0,parseScript(P.scenes[0].script,P.characters).ops.findIndex(o=>o.cmd==='msg'));tab('sc');\n if(projectMigrated)toast('既存プロジェクトをIndexedDBへ移行しました');\n if(!AS.filter(a=>!a.deleted).length){if(location.protocol.startsWith('http')){try{const response=await fetch('starter_backup.zip');if(response.ok){await restoreBackup(await response.blob(),false);maybeIOSNotice();return;}}catch(e){}}if(!maybeIOSNotice())helpStudio();}else maybeIOSNotice();})();"
rep(old_boot, new_boot, 'boot')

# ------------------------------------------------------------------
# Config backup wording: project is now also in IndexedDB.
# ------------------------------------------------------------------
rep("<div class=\"card\"><h3>バックアップ</h3><div class=\"sb\">素材は端末内（IndexedDB）にあります。ブラウザのデータを消すと失われるので、定期的にフルバックアップZIPを保存してください。</div>",
    "<div class=\"card\"><h3>バックアップ</h3><div class=\"sb\">プロジェクトと素材は端末内（IndexedDB）に保存します。iOSのストレージ整理やブラウザデータ削除に備え、定期的にフルバックアップZIPを保存してください。</div>", 'backup wording')

# ------------------------------------------------------------------
# Static safeguards for the requested compatibility contract.
# ------------------------------------------------------------------
assert "function createPlayer(root,pj,resolve,opts)" in s
assert "new CustomEvent('adv:flags'" in s
assert "new CustomEvent('adv:end'" in s
assert "getState(){return" in s
assert "indexedDB.open(DBN,DBV)" in s and "createObjectStore('project'" in s
assert "function softDeleteAsset" in s and "function trashSheet" in s
assert "Studio 2.2" in s

p.write_text(s, encoding='utf-8')
print('phase 1 patch applied')
