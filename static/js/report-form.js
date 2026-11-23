(() => {
  const form = document.getElementById('reportForm'); if (!form) return;
  const steps=[...document.querySelectorAll('.wizard-step')], title=document.getElementById('wizardTitle'), num=document.getElementById('wizardStep'), progress=document.getElementById('wizardProgress');
  const titles=['What is the problem?','Where is it?','Describe & show it','Review before sending']; let current=1;
  const go = n => { current=Math.max(1,Math.min(4,n)); steps.forEach(s=>s.classList.toggle('active',+s.dataset.step===current)); title.textContent=titles[current-1]; num.textContent=current; progress.style.width=`${current*25}%`; window.scrollTo({top:document.querySelector('.report-form-section').offsetTop-80,behavior:'smooth'}); if(current===4) review(); };
  const valid = step => { const fields=[...steps[step-1].querySelectorAll('input[required],select[required],textarea[required]')]; let ok=true; fields.forEach(f=>{if(!f.checkValidity()){f.reportValidity();ok=false}}); return ok; };
  document.querySelectorAll('.next-step').forEach(b=>b.addEventListener('click',()=>{if(valid(current)) go(current+1)}));
  document.querySelectorAll('.prev-step').forEach(b=>b.addEventListener('click',()=>go(current-1)));
  form.addEventListener('submit', e=>{
    const category=form.querySelector('input[name="category"]:checked');
    const severity=form.querySelector('select[name="severity"]')?.value;
    if(!category || !severity){
      e.preventDefault();
      go(!category ? 1 : 2);
    }
  });
  const review=()=>{
    const v=n=>form.querySelector(`[name="${n}"]`)?.value||'—';
    const selectedCategory=form.querySelector('input[name="category"]:checked');
    document.getElementById('reviewCategory').textContent=selectedCategory?.value||'—';
    document.getElementById('reviewLocation').textContent=[v('building'),v('room_area')].filter(x=>x&&x!=='—').join(' • ')||'—';
    document.getElementById('reviewSeverity').textContent=v('severity');
    document.getElementById('reviewDate').textContent=v('date_noticed');
    document.getElementById('reviewDescription').textContent=v('description');
  };
  const input=document.getElementById('photoInput'), zone=document.getElementById('dropZone'), name=document.getElementById('fileName'), preview=document.getElementById('imagePreview');
  zone?.addEventListener('click',e=>{if(e.target!==input) input.click()});
  input?.addEventListener('change',()=>{const f=input.files?.[0]; if(!f)return; name.textContent=f.name; const reader=new FileReader(); reader.onload=()=>{preview.innerHTML=`<img src="${reader.result}" alt="Selected report evidence preview">`; preview.classList.add('show')}; reader.readAsDataURL(f)});
  ['dragenter','dragover'].forEach(ev=>zone?.addEventListener(ev,e=>{e.preventDefault();zone.classList.add('dragging')})); ['dragleave','drop'].forEach(ev=>zone?.addEventListener(ev,e=>{e.preventDefault();zone.classList.remove('dragging')})); zone?.addEventListener('drop',e=>{const f=e.dataTransfer.files?.[0];if(!f)return;try{const dt=new DataTransfer();dt.items.add(f);input.files=dt.files;input.dispatchEvent(new Event('change'))}catch{}});
})();
