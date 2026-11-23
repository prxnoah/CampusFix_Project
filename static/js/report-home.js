(() => {
  // Interactive report preview wizard on the landing page.
  let step=1; const panels=[...document.querySelectorAll('.demo-panel')], next=document.getElementById('demoNext'), prev=document.getElementById('demoPrev'), label=document.getElementById('demoStep'), bar=document.getElementById('demoProgress');
  const render=()=>{panels.forEach(p=>p.classList.toggle('active',+p.dataset.demo===step));label&&(label.textContent=step);bar&&(bar.style.width=`${step*25}%`);if(prev)prev.style.opacity=step===1?.35:1; if(next)next.textContent=step===4?'Start a real report →':'Next →'};
  next?.addEventListener('click',()=>{if(step===4){location.href='/reports/new';return}step++;render()}); prev?.addEventListener('click',()=>{if(step>1){step--;render()}}); render();
  document.querySelectorAll('.demo-options button').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('.demo-options button').forEach(x=>x.classList.remove('selected'));b.classList.add('selected')}));

  // Particle field without a library.
  const c=document.getElementById('heroParticles'); if(!c)return; const ctx=c.getContext('2d'), reduce=matchMedia('(prefers-reduced-motion: reduce)').matches; let w,h,dots=[],mx=0,my=0;
  const resize=()=>{w=c.width=innerWidth*devicePixelRatio;h=c.height=c.parentElement.offsetHeight*devicePixelRatio; c.style.width='100%';c.style.height='100%';dots=Array.from({length:Math.min(80,Math.floor(innerWidth/16))},()=>({x:Math.random()*w,y:Math.random()*h,vx:(Math.random()-.5)*.25*devicePixelRatio,vy:(Math.random()-.5)*.25*devicePixelRatio,r:(Math.random()*1.4+.4)*devicePixelRatio}))};
  resize();addEventListener('resize',resize);addEventListener('pointermove',e=>{mx=e.clientX*devicePixelRatio;my=e.clientY*devicePixelRatio},{passive:true});
  const draw=()=>{ctx.clearRect(0,0,w,h);dots.forEach((p,i)=>{if(!reduce){p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>w)p.vx*=-1;if(p.y<0||p.y>h)p.vy*=-1; const dx=mx-p.x,dy=my-p.y,dist=Math.hypot(dx,dy);if(dist<180*devicePixelRatio){p.x-=dx/dist*.25;p.y-=dy/dist*.25}}ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle='rgba(255,230,170,.42)';ctx.fill(); for(let j=i+1;j<dots.length;j++){const q=dots[j],dist=Math.hypot(p.x-q.x,p.y-q.y);if(dist<110*devicePixelRatio){ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.strokeStyle=`rgba(255,255,255,${.08*(1-dist/(110*devicePixelRatio))})`;ctx.stroke()}}});if(!reduce)requestAnimationFrame(draw)};draw();
})();
