(() => {
'use strict';
const {categories, services, checkedAt}=window.LIBRARY_GUIDE;
const $=selector=>document.querySelector(selector);
const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const byId=id=>services.find(s=>s.id===id);
const categoryName=id=>categories.find(c=>c.id===id)?.name||id;
const state={category:'all',query:'',audience:'all'};
const normalize=value=>value.toLocaleLowerCase().normalize('NFKC').replace(/[’'·.,!?]/g,' ').replace(/\s+/g,' ').trim();
const targetText=s=>s.audience==='grad'?'대학원생 대상':'대상·조건 확인';
const card=s=>'<article class="service-card"><p class="service-category">'+escape(categoryName(s.category))+'</p><h3>'+escape(s.name)+'</h3><p class="service-question">'+escape(s.question)+'</p><p class="service-description">'+escape(s.description)+'</p><div class="badges"><span class="badge">'+escape(s.channel)+'</span><span class="badge'+(s.audience==='grad'?' target':'')+'">'+escape(targetText(s))+'</span></div><button type="button" data-open="'+s.id+'" aria-label="'+escape(s.name)+' 이용 방법 보기">이용 방법 보기 <span aria-hidden="true">↗</span></button></article>';
function render(){
 const terms=normalize(state.query).split(' ').filter(Boolean);
 const matches=services.filter(s=>(state.category==='all'||s.category===state.category)&&(state.audience!=='undergrad'||s.audience!=='grad')&&terms.every(term=>normalize([s.name,s.question,s.description,s.keywords,s.caution].join(' ')).includes(term)));
 $('#service-grid').innerHTML=matches.map(card).join('');
 $('#empty').hidden=matches.length!==0;
 $('#result-count').textContent=(state.category==='all'?'전체':categoryName(state.category))+' · '+matches.length+'개 안내'+(state.query?' · “'+state.query+'”':'');
 document.querySelectorAll('[data-category]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.category===state.category)));
}
function reset(){state.category='all';state.query='';state.audience='all';$('#search-input').value='';$('#audience').value='all';render();}
$('#category-grid').innerHTML=categories.map((c,i)=>'<button type="button" class="category-card" data-category="'+c.id+'"><span class="category-index"><span>0'+(i+1)+' / '+escape(c.name)+'</span><span aria-hidden="true">↗</span></span><h3>'+escape(c.question)+'</h3><p>'+escape(c.desc)+'</p></button>').join('');
$('#category-tabs').innerHTML=[{id:'all',name:'전체'},...categories].map(c=>'<button type="button" data-category="'+c.id+'" aria-pressed="'+(c.id==='all')+'">'+escape(c.name)+'</button>').join('');
$('#coverage').textContent=categories.length+'가지 상황 · '+services.length+'개 서비스 안내';$('#checked-at').textContent=checkedAt.replaceAll('-','.');
const relatedMap={loan:['night','wish'],wish:['dds','campus'],campus:['dds','wish'],missing:['loan','storage'],storage:['priority'],priority:['night'],night:['loan','mobile'],seat:['group','locker'],group:['maker','seat'],maker:['print','group'],stats:['business','domestic'],remote:['domestic','overseas','ebook'],domestic:['remote','citation','similarity'],overseas:['remote','citation','dds'],citation:['similarity','training'],similarity:['citation','training'],ebook:['oreilly','lectures'],oreilly:['ebook','discipline'],dds:['wish','other'],mobile:['seat','loan'],culture:['ebook','programs'],training:['domestic','citation']};
const dialog=$('#detail-dialog');
function openDetail(id){const s=byId(id);if(!s)return;
 $('#detail-category').textContent=categoryName(s.category)+' · '+(s.audience==='grad'?'대학원생·교직원 대상':'세부 이용자격 확인');
 $('#detail-content').innerHTML='<h2 id="detail-title">'+escape(s.name)+'</h2><p class="detail-question">'+escape(s.question)+'</p><p class="detail-summary">'+escape(s.description)+'</p><dl class="detail-facts"><div><dt>이용 경로</dt><dd>'+escape(s.channel)+'</dd></div><div><dt>실제 서비스 로그인</dt><dd>'+escape(s.login)+'</dd></div><div><dt>비용</dt><dd>'+escape(s.cost)+'</dd></div></dl><h3>이렇게 이용해요</h3><ol>'+s.steps.map(step=>'<li>'+escape(step)+'</li>').join('')+'</ol><h3>이용 전 확인할 점</h3><p class="detail-warning">'+escape(s.caution)+'</p>'+(relatedMap[id]?'<h3>함께 보면 좋은 서비스</h3><div class="related">'+relatedMap[id].map(key=>'<button type="button" data-open="'+key+'">'+escape(byId(key).name)+'</button>').join('')+'</div>':'')+'<div class="detail-source"><a class="primary" href="'+escape(s.source)+'" target="_blank" rel="noopener noreferrer">공식 안내에서 확인하기 ↗</a><p>공개 안내 확인일 '+escape(s.checkedAt)+' · 비공식 가이드 시안<br>이 가이드에서는 로그인하지 않습니다. 공식 서비스는 별도 인증이 필요할 수 있습니다.</p></div>';
 if(!dialog.open)dialog.showModal();dialog.scrollTop=0;$('#close-dialog').focus();
}
$('#close-dialog').addEventListener('click',()=>dialog.close());dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
const bookCases={loan:{text:'대출 중인 책은 예약을 검토해보세요. 반납되면 우선 대출할 수 있습니다.',ids:['loan']},missing:{text:'검색에는 대출가능인데 서가에 없다면, 부재도서 신고로 찾아달라고 요청할 수 있어요.',ids:['missing']},campus:{text:'다른 분관에 있는 대출가능 도서는 캠퍼스대출 조건을 확인해보세요.',ids:['campus']},priority:{text:'정리중인 단행본은 우선정리 요청을 검토할 수 있어요.',ids:['priority']},storage:{text:'보존서고 자료는 홈페이지에서 먼저 신청하고 제공 알림 후 이용해요.',ids:['storage']},'not-owned':{text:'새로 구입을 요청하려면 희망도서, 다른 기관 자료를 이용하려면 상호대차를 검토하세요.',ids:['wish','dds']}};
document.addEventListener('click',event=>{const open=event.target.closest('[data-open]');if(open){openDetail(open.dataset.open);return;}const category=event.target.closest('[data-category]');if(category){state.category=category.dataset.category;state.query='';$('#search-input').value='';render();if(category.classList.contains('category-card'))$('#services').scrollIntoView({behavior:'smooth'});return;}const book=event.target.closest('[data-book]');if(book){const result=bookCases[book.dataset.book];document.querySelectorAll('[data-book]').forEach(b=>b.setAttribute('aria-pressed',String(b===book)));$('#book-result').hidden=false;$('#book-result').innerHTML='<p>'+escape(result.text)+'</p>'+result.ids.map(id=>'<button type="button" data-open="'+id+'">'+escape(byId(id).name)+' 이용 방법 ↗</button>').join('');}});
$('#search-input').addEventListener('input',event=>{state.query=event.target.value.trim();render();});$('#search-form').addEventListener('submit',event=>{event.preventDefault();state.query=$('#search-input').value.trim();render();});$('#audience').addEventListener('change',event=>{state.audience=event.target.value;render();});$('#reset').addEventListener('click',reset);$('#empty-reset').addEventListener('click',()=>{reset();$('#search-input').focus();});render();
})();