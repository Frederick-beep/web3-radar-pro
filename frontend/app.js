const state={page:'dashboard',apiKey:localStorage.getItem('wr_api_key')||'demo-key',base:'',data:{}};
const nav=[
  ['dashboard','▦','控制台'],
  ['bsc','🔥','BSC 新币雷达'],
  ['airdrops','🎁','空投雷达'],
  ['smart','🧠','聪明钱'],
  ['whale','🐋','鲸鱼雷达'],
  ['tokens','🪙','代币情报'],
  ['dex','💧','DEX 雷达'],
  ['alerts','🚨','Alpha 警报']
];
const app=document.getElementById('app');
function esc(x){return String(x??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function short(x){return x?String(x).slice(0,6)+'…'+String(x).slice(-4):'—'}
function money(x){x=Number(x||0);return x>=1e9?'$'+(x/1e9).toFixed(2)+'B':x>=1e6?'$'+(x/1e6).toFixed(2)+'M':x>=1e3?'$'+(x/1e3).toFixed(1)+'K':x>0?'$'+x.toFixed(2):'$0'}
function num(x){return Number(x||0).toLocaleString()}
function api(path,opt={}){const url=(state.base||'')+path;return fetch(url,{...opt,headers:{'Content-Type':'application/json','X-API-Key':state.apiKey,...(opt.headers||{})}}).then(async r=>{const t=await r.text();let d;try{d=JSON.parse(t)}catch{d=t}if(!r.ok)throw new Error(d?.detail||d?.message||`HTTP ${r.status}`);return d})}
function layout(content){app.innerHTML=`<aside class="side"><div class="brand"><div class="logo">W</div><span>WEB3 RADAR <small>PRO</small></span></div><nav class="nav">${nav.map(n=>`<button class="${state.page===n[0]?'active':''}" data-page="${n[0]}"><i class="ico">${n[1]}</i><span>${n[2]}</span></button>`).join('')}</nav><div class="side-foot">BSC 优先智能雷达<br>v5.4.0</div></aside><main class="main"><header class="top"><div class="crumb">Web3 Radar Pro / ${esc(nav.find(n=>n[0]===state.page)?.[2]||'控制台')}</div><div class="top-actions"><button class="btn" id="settings">⚙</button><button class="btn primary" id="refresh">刷新</button></div></header><div class="page">${content}</div></main>`;document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>{state.page=b.dataset.page;render()});document.getElementById('refresh').onclick=()=>render();document.getElementById('settings').onclick=settings}
function stat(label,val,trend='实时'){return `<div class="card"><div class="stat-label">${label}</div><div class="stat">${val}</div><div class="trend">● ${trend}</div></div>`}
function riskBadge(level,score){let c=level==='low'?'low':level==='high'?'high':'med';return `<span class="badge ${c}">${esc(level==='low'?'低风险':level==='high'?'高风险':level==='medium'?'中风险':level||'未知')}${score!==undefined&&score!==null?' '+score:''}</span>`}
function statusBadge(s){let c=s==='hot'?'hot':s==='filter'?'high':s==='watch'?'med':'low';return `<span class="badge ${c}">${esc(s==='hot'?'🔥热门':s==='filter'?'⚠过滤':s==='watch'?'👀观察':'正常')}</span>`}
function fmt(x){if(!x)return '—';try{return new Date(x).toLocaleString('zh-CN',{month:'short',day:'2-digit',hour:'2-digit',minute:'2-digit'})}catch{return x}}
function empty(message,action=''){return `<div class="empty"><div>${esc(message)}</div>${action?`<div style="margin-top:10px">${action}</div>`:''}</div>`}
function loading(){return `<div class="skeleton-list"><i></i><i></i><i></i></div>`}

async function dashboard(){
  const [o,bsc,a,wallets,signals,swaps]=await Promise.all([
    api('/api/v2/bsc/overview'),
    api('/api/v2/bsc/launches?limit=8'),
    api('/api/v2/airdrops?limit=6'),
    api('/api/v1/wallets?limit=8&chain_id=56'),
    api('/api/v1/signals?limit=8&chain_id=56'),
    api('/api/v1/swaps?limit=8&chain_id=56')
  ]);
  const smart=wallets.filter(x=>x.smart_money).length;
  return `<h1>控制台</h1><div class="sub">实时监控链上机会、风险、资金流向与空投动态。</div>
  <div class="grid4">${stat('已追踪 BSC 交易对',num(o.tracked_pairs))}${stat('热门代币',num(o.hot),'异常引擎')}${stat('观察中代币',num(o.watch))}${stat('平均异常分',Number(o.avg_anomaly||0).toFixed(2),'分 / 100')}</div>
  <div class="grid4 section-tight">${stat('聪明钱钱包',num(smart),'BSC 已索引')}${stat('鲸鱼 / Alpha 信号',num(signals.length),'最新信号')}${stat('最近 Swap',num(swaps.length),'BSC')}${stat('已过滤代币',num(o.filtered),'风险过滤')}</div>
  <div class="two section"><section class="card"><div class="section-head"><h2>🔥 BSC 热门新币</h2><button class="btn" onclick="go('bsc')">查看雷达</button></div>${bsc.length?`<div class="mini-table">${bsc.slice(0,6).map(x=>`<div class="mini-row"><div><b>${esc(short(x.token))}</b><div class="mono muted">${short(x.pair)}</div></div><div>${statusBadge(x.status)}</div><div><b>${x.anomaly_score}</b><span class="muted"> / 100</span></div><div>${riskBadge(x.risk_level,x.risk_score)}</div></div>`).join('')}</div>`:empty('暂无 BSC 新币数据。请确认 collector、DEX Worker 和 BSC_RPC_URL 正常运行。')}</section>
  <section class="card"><div class="section-head"><h2>🎁 空投机会</h2><button class="btn" onclick="go('airdrops')">查看空投</button></div>${a.length?a.slice(0,4).map(airdropMini).join(''):empty('暂无已收录空投活动。')}</section></div>
  <div class="two section"><section class="card"><div class="section-head"><h2>🧠 聪明钱</h2><button class="btn" onclick="go('smart')">查看</button></div>${wallets.length?wallets.slice(0,5).map(x=>`<div class="event"><span class="mono">${short(x.address)}</span><span><b>${x.score}</b> ${x.smart_money?'🟢 聪明钱':''}</span></div>`).join(''):empty('暂无钱包行为数据。')}</section>
  <section class="card"><div class="section-head"><h2>🚨 最新告警</h2><button class="btn" onclick="go('alerts')">查看</button></div>${signals.length?signals.slice(0,5).map(x=>`<div class="event"><span><span class="badge hot">${esc(x.type)}</span> <span class="mono">${short(x.token)}</span></span><b>${x.score}</b></div>`).join(''):empty('暂无告警信号。')}</section></div>`;
}
function airdropMini(a){
  const statusMap={upcoming:'即将开始',active:'进行中',claim_live:'可领取',expired:'已过期'};
  return `<div class="event"><div><b>${esc(a.name)}</b><div class="muted">潜力 ${a.potential_score}/100 · ${esc(statusMap[a.status]||a.status)}</div></div>${riskBadge(a.risk_level,a.risk_score)}</div>`;
}

async function bsc(){
  const rows=await api('/api/v2/bsc/launches?limit=120');
  return `<h1>BSC 新币雷达</h1><div class="sub">PancakeSwap V2 PairCreated → Swap → 买卖分析 → 聪明钱追踪 → 合约风险扫描 → 异常评分</div>
  <div class="grid4 section-tight">${stat('新交易对',num(rows.length))}${stat('🔥热门',num(rows.filter(x=>x.status==='hot').length),'评分 ≥ 80')}${stat('👀观察中',num(rows.filter(x=>x.status==='watch').length))}${stat('⚠高风险',num(rows.filter(x=>x.risk_level==='high').length),'已过滤')}</div>
  <div class="card section"><div class="section-head"><h2>实时代币流</h2><input class="search" id="bscSearch" placeholder="搜索代币 / 交易对 / 地址"></div><div id="bscTable">${bscTable(rows)}</div></div>`;
}
function bscTable(rows){
  if(!rows.length)return empty('暂无数据。BSC Collector 需要配置 BSC_RPC_URL；DEX Worker 会自动发现 PancakeSwap V2 新交易对。');
  return `<table class="table"><thead><tr><th>代币 / 交易对</th><th>状态</th><th>异常分</th><th>风险</th><th>流动性</th><th>24h 成交量</th><th>买 / 卖</th><th>买入压力</th></tr></thead><tbody>${rows.map(x=>`<tr><td><div class="token">${esc(short(x.token))}</div><div class="mono muted">${short(x.pair)}</div><div class="muted">${esc(x.dex||'DEX')}</div></td><td>${statusBadge(x.status)}</td><td><b>${x.anomaly_score}</b>/100</td><td>${riskBadge(x.risk_level,x.risk_score)}</td><td>${money(x.liquidity_usd)}</td><td>${money(x.volume_24h_usd)}</td><td>${num(x.buys_5m)} / ${num(x.sells_5m)}</td><td><div class="pressure"><i style="width:${Math.max(0,Math.min(100,x.buy_pressure||0))}%"></i></div><span class="muted">${Number(x.buy_pressure||0).toFixed(0)}%</span></td></tr>`).join('')}</tbody></table>`;
}

async function airdrops(){
  const [rows,cal]=await Promise.all([api('/api/v2/airdrops?limit=100'),api('/api/v2/airdrops/calendar?limit=30')]);
  const statusMap={upcoming:'即将开始',active:'进行中',claim_live:'可领取',expired:'已过期'};
  return `<h1>空投雷达</h1><div class="sub">发现机会、跟踪 Snapshot / Eligibility / Claim / Deadline，用公开链上行为做资格启发式分析。</div>
  <div class="grid4 section-tight">${stat('已追踪活动',num(rows.length))}${stat('即将开始',num(rows.filter(x=>x.status==='upcoming').length))}${stat('可领取',num(rows.filter(x=>x.status==='claim_live').length))}${stat('低风险',num(rows.filter(x=>x.risk_level==='low').length))}</div>
  <div class="cards section">${rows.length?rows.map(a=>`<div class="card airdrop-card" data-airdrop="${a.id}"><div style="display:flex;justify-content:space-between"><span class="badge">${esc(statusMap[a.status]||a.status)}</span>${riskBadge(a.risk_level,a.risk_score)}</div><h3>${esc(a.name)}</h3><div class="muted">Chain ${a.chain_id} · 潜力 ${a.potential_score}/100</div><div class="progress"><i style="width:${a.potential_score}%"></i></div><div class="airdrop-meta"><div class="kv"><span>快照日</span><b>${fmt(a.snapshot_at)}</b></div><div class="kv"><span>截止日</span><b>${fmt(a.deadline_at)}</b></div></div></div>`).join(''):empty('暂无已验证空投数据。将真实项目加入 config/airdrops.yaml 后运行 seed_airdrops.py。')}</div>
  <div class="two section"><section class="card"><div class="section-head"><h2>📅 空投日历</h2></div><div class="timeline">${cal.length?cal.map(e=>`<div class="event"><div><b>${esc(e.project)}</b><div class="muted">${esc(e.event==='snapshot'?'快照':e.event==='eligibility'?'资格开放':e.event==='claim'?'领取开始':'截止')}</div></div><b>${fmt(e.at)}</b></div>`).join(''):empty('暂无日历事件')}</div></section><section class="card"><div class="section-head"><h2>🔎 钱包资格查询</h2></div><div class="form"><input class="search" style="flex:1" id="wallet" placeholder="0x 钱包地址"><button class="btn primary" id="checkWallet">分析</button></div><div id="walletResult"></div></section></div>`;
}

async function smart(){
  let rows=await api('/api/v1/wallets?limit=80&chain_id=56');
  return `<h1>聪明钱</h1><div class="sub">按链上行为评分，识别高活跃、高多样性、鲸鱼事件参与钱包。</div>
  <div class="grid4 section-tight">${stat('已索引钱包',num(rows.length))}${stat('聪明钱候选',num(rows.filter(x=>x.smart_money).length),'评分 ≥ 80')}${stat('平均评分',rows.length?(rows.reduce((s,x)=>s+Number(x.score||0),0)/rows.length).toFixed(1):'0')}${stat('鲸鱼事件',num(rows.reduce((s,x)=>s+Number(x.whales||0),0)))}</div>
  <div class="card section"><table class="table"><thead><tr><th>钱包地址</th><th>链</th><th>评分</th><th>转账次数</th><th>鲸鱼事件</th><th>状态</th></tr></thead><tbody>${rows.length?rows.map(x=>`<tr><td class="mono">${short(x.address)}</td><td>${x.chain_id}</td><td><b>${x.score}</b>/100</td><td>${num(x.transfers)}</td><td>${num(x.whales)}</td><td>${x.smart_money?'<span class="badge low">聪明钱</span>':'<span class="badge">追踪中</span>'}</td></tr>`).join(''):`<tr><td colspan="6">${empty('暂无钱包数据。collector + intelligence Worker 启动后会持续建立索引。')}</td></tr>`}</tbody></table></div>`;
}

async function tokens(){
  let rows=await api('/api/v1/tokens?limit=100&chain_id=56');
  return `<h1>代币情报</h1><div class="sub">代币价格、流动性、24h 成交量与链上基础数据。</div>
  <div class="grid4 section-tight">${stat('BSC 代币',num(rows.length))}${stat('已有价格',num(rows.filter(x=>x.price_usd>0).length),'DexScreener')}${stat('追踪流动性',money(rows.reduce((s,x)=>s+Number(x.liquidity_usd||0),0)))}${stat('追踪 24h 成交量',money(rows.reduce((s,x)=>s+Number(x.volume_24h_usd||0),0)))}</div>
  <div class="card section"><table class="table"><thead><tr><th>代币</th><th>价格</th><th>流动性</th><th>24h 成交量</th></tr></thead><tbody>${rows.length?rows.map(x=>`<tr><td><b>${esc(x.symbol||'未知')}</b><div class="mono muted">${short(x.address)}</div></td><td>${Number(x.price_usd||0)?'$'+Number(x.price_usd).toFixed(8):'—'}</td><td>${money(x.liquidity_usd)}</td><td>${money(x.volume_24h_usd)}</td></tr>`).join(''):`<tr><td colspan="4">${empty('暂无代币数据。DEX Worker 先登记新交易对中的代币，Price Worker 再补充市场数据。')}</td></tr>`}</tbody></table></div>`;
}

async function whale(){
  let rows=await api('/api/v1/signals?limit=80&signal_type=WHALE_TRANSFER&chain_id=56');
  return `<h1>鲸鱼雷达</h1><div class="sub">展示真实索引到的 BSC 大额 ERC-20 转账信号。</div>
  <div class="grid4 section-tight">${stat('鲸鱼信号',num(rows.length))}${stat('高分信号',num(rows.filter(x=>x.score>=80).length))}${stat('平均分',rows.length?(rows.reduce((s,x)=>s+Number(x.score||0),0)/rows.length).toFixed(1):'0')}${stat('最新时间',rows[0]?fmt(rows[0].created_at):'—')}</div>
  <div class="card section"><table class="table"><thead><tr><th>类型</th><th>代币</th><th>钱包</th><th>评分</th><th>原因</th><th>时间</th></tr></thead><tbody>${rows.length?rows.map(x=>`<tr><td><span class="badge hot">${esc(x.type)}</span></td><td class="mono">${short(x.token)}</td><td class="mono">${short(x.wallet)}</td><td><b>${x.score}</b></td><td>${esc(x.reason)}</td><td>${fmt(x.created_at)}</td></tr>`).join(''):`<tr><td colspan="6">${empty('暂无鲸鱼信号。需要 intelligence Worker 持续索引 ERC-20 转账事件。')}</td></tr>`}</tbody></table></div>`;
}

async function dex(){
  const [pools,swaps]=await Promise.all([api('/api/v1/pools?limit=80&chain_id=56'),api('/api/v1/swaps?limit=80&chain_id=56')]);
  return `<h1>DEX 雷达</h1><div class="sub">PancakeSwap V2 交易对创建与 Swap 活动。</div>
  <div class="grid4 section-tight">${stat('交易池',num(pools.length))}${stat('Swap 记录',num(swaps.length))}${stat('独立交易对',num(new Set(swaps.map(x=>x.pair)).size))}${stat('活跃发送者',num(new Set(swaps.map(x=>x.sender)).size))}</div>
  <div class="two section"><section class="card"><div class="section-head"><h2>💧 流动性池</h2></div>${pools.length?`<table class="table"><thead><tr><th>DEX</th><th>交易对</th><th>Token0</th><th>Token1</th><th>区块</th></tr></thead><tbody>${pools.map(x=>`<tr><td>${esc(x.dex)}</td><td class="mono">${short(x.pair)}</td><td class="mono">${short(x.token0)}</td><td class="mono">${short(x.token1)}</td><td>${x.block}</td></tr>`).join('')}</tbody></table>`:empty('暂无池子数据。')}</section>
  <section class="card"><div class="section-head"><h2>🔄 最新 Swap</h2></div>${swaps.length?`<table class="table"><thead><tr><th>交易对</th><th>发送者</th><th>区块</th></tr></thead><tbody>${swaps.slice(0,30).map(x=>`<tr><td class="mono">${short(x.pair)}</td><td class="mono">${short(x.sender)}</td><td>${x.block}</td></tr>`).join('')}</tbody></table>`:empty('暂无 Swap 数据。')}</section></div>`;
}

async function alerts(){
  let rows=await api('/api/v1/signals?limit=100&min_score=0&chain_id=56');
  const typeMap={WHALE_TRANSFER:'🐋 鲸鱼转账',ALPHA_TOKEN:'📈 Alpha 代币'};
  return `<h1>Alpha 警报</h1><div class="sub">统一信号流：鲸鱼转账、Alpha 代币与后续策略信号。</div>
  <div class="grid4 section-tight">${stat('信号总数',num(rows.length))}${stat('高分 ≥ 80',num(rows.filter(x=>x.score>=80).length))}${stat('🐋 鲸鱼',num(rows.filter(x=>x.type==='WHALE_TRANSFER').length))}${stat('📈 Alpha',num(rows.filter(x=>x.type==='ALPHA_TOKEN').length))}</div>
  <div class="card section"><table class="table"><thead><tr><th>类型</th><th>代币</th><th>钱包</th><th>评分</th><th>原因</th><th>时间</th></tr></thead><tbody>${rows.length?rows.map(x=>`<tr><td><span class="badge ${x.score>=80?'hot':'med'}">${esc(typeMap[x.type]||x.type)}</span></td><td class="mono">${short(x.token)}</td><td class="mono">${short(x.wallet)}</td><td><b>${x.score}</b></td><td>${esc(x.reason)}</td><td>${fmt(x.created_at)}</td></tr>`).join(''):`<tr><td colspan="6">${empty('暂无 Alpha 警报。')}</td></tr>`}</tbody></table></div>`;
}

function settings(){const key=prompt('X-API-Key',state.apiKey);if(key!==null){state.apiKey=key.trim();localStorage.setItem('wr_api_key',state.apiKey);render()}}
window.go=p=>{state.page=p;render()};
function modal(body){const d=document.createElement('div');d.className='modal-back';d.innerHTML='<div class="modal">'+body+'</div>';d.onclick=e=>{if(e.target===d)d.remove()};document.body.appendChild(d)}
function bindPageEvents(){
  const s=document.getElementById('bscSearch');
  if(s){
    s.oninput=()=>{
      const q=s.value.toLowerCase();
      document.querySelectorAll('#bscTable tbody tr').forEach(r=>r.style.display=r.innerText.toLowerCase().includes(q)?'':'none');
    };
  }
  document.querySelectorAll('[data-airdrop]').forEach(c=>{
    c.onclick=async()=>{
      try{
        const d=await api('/api/v2/airdrops/'+c.dataset.airdrop);
        const statusMap={upcoming:'即将开始',active:'进行中',claim_live:'可领取',expired:'已过期'};
        modal(`<button class="close" onclick="this.closest('.modal-back').remove()">×</button><h2>${esc(d.name)}</h2><p class="muted">${esc(statusMap[d.status]||d.status)} · 潜力 ${d.potential_score}/100 · 风险 ${esc(d.risk_level==='low'?'低':d.risk_level==='high'?'高':'中')}</p><div class="airdrop-meta"><div class="kv"><span>官网</span><b>${d.official_website?`<a href="${esc(d.official_website)}" target="_blank" rel="noreferrer">官方链接</a>`:'—'}</b></div><div class="kv"><span>领取</span><b>${d.official_claim_url?`<a href="${esc(d.official_claim_url)}" target="_blank" rel="noreferrer">领取页面</a>`:'—'}</b></div></div><h3>任务列表</h3>${(d.tasks||[]).map(t=>`<div class="event"><span>${esc(t.title)}</span><span class="badge ${t.required?'hot':'low'}">${t.required?'必做':'可选'}</span></div>`).join('')}`);
      }catch(e){
        modal(`<h3>空投详情加载失败</h3><div class="error">${esc(e.message)}</div>`);
      }
    };
  });
  const cw=document.getElementById('checkWallet');
  if(cw){
    cw.onclick=async()=>{
      const w=document.getElementById('wallet').value.trim();
      const out=document.getElementById('walletResult');
      out.innerHTML='<div class="loading">正在分析公开链上行为…</div>';
      try{
        const r=await api('/api/v2/airdrops/check-wallet',{method:'POST',body:JSON.stringify({address:w})});
        const eligMap={likely:'很可能符合',possible:'可能符合',unlikely:'暂不符合'};
        out.innerHTML=r.map(x=>`<div class="section"><div class="card"><b>${esc(x.project)}</b> <span class="badge ${x.eligibility==='likely'?'low':x.eligibility==='possible'?'med':'high'}">${esc(eligMap[x.eligibility]||x.eligibility)}</span><div class="wallet-result"><div class="kv"><span>置信度</span><b>${x.confidence}%</b></div><div class="kv"><span>任务覆盖</span><b>${x.task_coverage}%</b></div><div class="kv"><span>活跃度</span><b>${x.activity_score}</b></div><div class="kv"><span>交易笔数</span><b>${x.tx_count}</b></div></div><p class="muted">${esc(x.warning)}</p></div></div>`).join('')||empty('暂无空投项目可分析。');
      }catch(e){
        out.innerHTML='<div class="error">'+esc(e.message)+'</div>';
      }
    };
  }
}
async function render(){
  let c='<div class="loading">加载中…</div>';
  try{
    if(state.page==='dashboard')c=await dashboard();
    else if(state.page==='bsc')c=await bsc();
    else if(state.page==='airdrops')c=await airdrops();
    else if(state.page==='smart')c=await smart();
    else if(state.page==='tokens')c=await tokens();
    else if(state.page==='whale')c=await whale();
    else if(state.page==='dex')c=await dex();
    else c=await alerts();
  }catch(e){
    c=`<h1>${esc(nav.find(n=>n[0]===state.page)?.[2])}</h1><div class="error">接口错误: ${esc(e.message)}<br><span class="muted">请检查：API Key、PostgreSQL、Redis、Worker 运行状态和 BSC RPC 配置。</span></div>`;
  }
  layout(c);bindPageEvents();
}
render();
