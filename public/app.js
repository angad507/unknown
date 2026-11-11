const entries = [
  {edition:'ENTRY 001 · FIRST EDITION', name:'The cartographer', field:'GEOGRAPHY · FIELDWORK', line:'A life devoted to reading what the land leaves unsaid.', bio:'An editorial composite, not a real person. This sample entry demonstrates the private archive format and must be replaced with verified subjects and approved biographies before publication.', note:'The archive does not confuse visibility with significance.', image:'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=900&q=80', alt:'Editorial portrait, sample entry'},
  {edition:'ENTRY 002 · FIRST EDITION', name:'The materialist', field:'CRAFT · MATERIAL CULTURE', line:'Finding permanence in a culture of the temporary.', bio:'An editorial composite, not a real person. Sample copy illustrates how an entry can hold a biography, notable work and an editorial note without implying real credentials.', note:'A quiet practice, considered over a long horizon.', image:'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=900&q=80', alt:'Editorial portrait, sample entry'},
  {edition:'ENTRY 003 · FIRST EDITION', name:'The listener', field:'SOUND · RESEARCH', line:'An uncommon ear for the histories carried by sound.', bio:'An editorial composite, not a real person. This fictional placeholder carries no actual achievements or endorsement and should be replaced with research-checked material.', note:'The work begins with attention.', image:'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80', alt:'Editorial portrait, sample entry'},
  {edition:'ENTRY 001 · FIRST EDITION', name:'The cartographer', field:'GEOGRAPHY · FIELDWORK', line:'A life devoted to reading what the land leaves unsaid.', bio:'An editorial composite, not a real person. This sample entry demonstrates the private archive format and must be replaced with verified subjects and approved biographies before publication.', note:'The archive does not confuse visibility with significance.', image:'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=900&q=80', alt:'Editorial portrait, sample entry'},
  {edition:'ENTRY 002 · FIRST EDITION', name:'The materialist', field:'CRAFT · MATERIAL CULTURE', line:'Finding permanence in a culture of the temporary.', bio:'An editorial composite, not a real person. Sample copy illustrates how an entry can hold a biography, notable work and an editorial note without implying real credentials.', note:'A quiet practice, considered over a long horizon.', image:'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=900&q=80', alt:'Editorial portrait, sample entry'},
  {edition:'ENTRY 003 · FIRST EDITION', name:'The listener', field:'SOUND · RESEARCH', line:'An uncommon ear for the histories carried by sound.', bio:'An editorial composite, not a real person. This fictional placeholder carries no actual achievements or endorsement and should be replaced with research-checked material.', note:'The work begins with attention.', image:'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80', alt:'Editorial portrait, sample entry'},
  {edition:'ENTRY 001 · FIRST EDITION', name:'The cartographer', field:'GEOGRAPHY · FIELDWORK', line:'A life devoted to reading what the land leaves unsaid.', bio:'An editorial composite, not a real person. This sample entry demonstrates the private archive format and must be replaced with verified subjects and approved biographies before publication.', note:'The archive does not confuse visibility with significance.', image:'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=900&q=80', alt:'Editorial portrait, sample entry'},
  {edition:'ENTRY 002 · FIRST EDITION', name:'The materialist', field:'CRAFT · MATERIAL CULTURE', line:'Finding permanence in a culture of the temporary.', bio:'An editorial composite, not a real person. Sample copy illustrates how an entry can hold a biography, notable work and an editorial note without implying real credentials.', note:'A quiet practice, considered over a long horizon.', image:'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=900&q=80', alt:'Editorial portrait, sample entry'},
  {edition:'ENTRY 003 · FIRST EDITION', name:'The listener', field:'SOUND · RESEARCH', line:'An uncommon ear for the histories carried by sound.', bio:'An editorial composite, not a real person. This fictional placeholder carries no actual achievements or endorsement and should be replaced with research-checked material.', note:'The work begins with attention.', image:'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=900&q=80', alt:'Editorial portrait, sample entry'}
];

const grid = document.querySelector('#profile-grid');
grid.innerHTML = entries.map((p,i)=>`<button class="profile-card reveal" data-entry="${i}" aria-label="Read archive entry ${p.name}"><div class="profile-card__image"><img src="${p.image}" alt="${p.alt}" loading="lazy"><span class="profile-card__edition">${p.edition}</span><span class="profile-card__hover">OPEN ENTRY ↗</span></div><div class="profile-card__meta"><span class="profile-card__name">${p.name}</span><span class="profile-card__field">${p.field}</span></div><p class="profile-card__desc">${p.line}</p></button>`).join('');

const dialog = document.querySelector('.profile-dialog');
document.querySelectorAll('.profile-card').forEach(card=>card.addEventListener('click',()=>{
  const p=entries[Number(card.dataset.entry)];
  dialog.querySelector('.dialog-content').innerHTML=`<img src="${p.image}" alt="${p.alt}"><div><p class="eyebrow">${p.edition}</p><h2>${p.name}</h2><p class="eyebrow">${p.field}</p><p>${p.bio}</p><p><strong>EDITORIAL NOTE</strong><br>${p.note}</p></div>`;
  dialog.showModal();
}));
document.querySelector('.dialog-close').addEventListener('click',()=>dialog.close());
dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close()});

const observer=new IntersectionObserver(items=>items.forEach(item=>{if(item.isIntersecting){item.target.classList.add('visible');observer.unobserve(item.target)}}),{threshold:.12});
document.querySelectorAll('.reveal').forEach((el,i)=>{el.style.transitionDelay=`${Math.min(i%3,2)*90}ms`;observer.observe(el)});

const menu=document.querySelector('.menu-toggle'), nav=document.querySelector('.nav');
menu.addEventListener('click',()=>{const open=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(open));menu.setAttribute('aria-label',open?'Close navigation':'Open navigation')});
nav.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{nav.classList.remove('open');menu.setAttribute('aria-expanded','false')}));

document.querySelectorAll('[data-form]').forEach(form=>form.addEventListener('submit',async e=>{
  e.preventDefault();
  const status=form.querySelector('.form-response');
  const button=form.querySelector('button[type="submit"]');
  button.disabled=true;
  status.textContent='Submitting…';
  try{
    const response=await fetch(form.dataset.form==='nomination'?'/api/nomination':'/api/access-request',{
      method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(form)))
    });
    const result=await response.json();
    if(!response.ok) throw new Error(result.error||'Submission failed. Please try again.');
    status.textContent=result.message;
    form.reset();
  }catch(error){status.textContent=form.dataset.form==='nomination'?error.message:'Access requests are not yet connected to a submission service.';}
  finally{button.disabled=false;}
}));

document.body.classList.add('loading');
window.addEventListener('load',()=>setTimeout(()=>{document.querySelector('.loader').classList.add('done');document.body.classList.remove('loading')},500));
