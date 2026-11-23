document.addEventListener("DOMContentLoaded",()=>{
 const fab=document.getElementById("aiFab"), chat=document.getElementById("aiChat"), close=document.getElementById("aiClose"), form=document.getElementById("aiForm"), input=document.getElementById("aiInput"), box=document.getElementById("aiMessages");
 if(!fab||!chat)return;
 const history=[];
 const esc=v=>String(v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
 const format=v=>esc(v).replace(/\n/g,"<br>").replace(/\*\*(.*?)\*\*/g,"<b>$1</b>");
 const open=()=>{chat.classList.add("open");chat.setAttribute("aria-hidden","false");setTimeout(()=>input?.focus(),180)};
 const shut=()=>{chat.classList.remove("open");chat.setAttribute("aria-hidden","true")};
 fab.addEventListener("click",open); close?.addEventListener("click",shut);
 const add=(html,who="bot")=>{const d=document.createElement("div");d.className=`ai-msg ${who}`;d.innerHTML=html;box.appendChild(d);box.scrollTop=box.scrollHeight;return d};
 const send=async msg=>{
   msg=String(msg||"").trim(); if(!msg)return;
   add(`<span>${esc(msg)}</span>`,"user"); input.value="";
   history.push({role:"user",content:msg});
   const typing=add("<span class=ai-typing><i></i><i></i><i></i></span>","bot");
   try{
     const r=await fetch("/api/ai-help",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({messages:history})});
     const data=await r.json();
     if(!r.ok)throw new Error(data.error||"AI unavailable");
     const reply=String(data.reply||"").trim()||"I’m not sure how to answer that yet.";
     history.push({role:"assistant",content:reply});
     typing.innerHTML=`<span>${format(reply)}</span>`;
   }catch(e){
     typing.innerHTML="<span>Sorry, the AI assistant is temporarily unavailable. You can still use CampusFix normally to submit a report.</span>";
     history.pop();
   }
 };
 form?.addEventListener("submit",e=>{e.preventDefault();send(input.value)});
 document.querySelectorAll("[data-ai]").forEach(b=>b.addEventListener("click",()=>send(b.dataset.ai)));
});