document.addEventListener("DOMContentLoaded",()=>{
  const loader=document.getElementById("page-loader");
  const hideLoader=()=>{if(!loader)return;loader.style.opacity="0";setTimeout(()=>loader.remove(),550)};
  window.addEventListener('load',()=>setTimeout(hideLoader,500));
  setTimeout(hideLoader,2200);

  const toggle=document.getElementById("themeToggle");
  if(localStorage.getItem("campusfix-theme")==="dark") document.body.classList.add("dark");
  toggle?.addEventListener("click",()=>{document.body.classList.toggle("dark");localStorage.setItem("campusfix-theme",document.body.classList.contains("dark")?"dark":"light")});

  document.querySelector(".nav-toggle")?.addEventListener("click",()=>document.querySelector(".main-nav")?.classList.toggle("open"));

  const observer=new IntersectionObserver(entries=>{
    entries.forEach(e=>{if(e.isIntersecting){e.target.classList.add("visible");observer.unobserve(e.target)}})
  },{threshold:.08});
  document.querySelectorAll(".reveal").forEach(el=>observer.observe(el));

  document.querySelectorAll("[data-count]").forEach(el=>{
    const target=parseInt(el.dataset.count||0); let current=0; const duration=1000; const start=performance.now();
    const tick=now=>{const p=Math.min((now-start)/duration,1);const eased=1-Math.pow(1-p,3);current=Math.floor(eased*target);el.textContent=current.toLocaleString();if(p<1)requestAnimationFrame(tick)};
    requestAnimationFrame(tick);
  });

  document.querySelectorAll(".toast").forEach(t=>setTimeout(()=>t.remove(),6000));
});
