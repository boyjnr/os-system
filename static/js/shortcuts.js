(function(){
  function $(sel, ctx){ return (ctx||document).querySelector(sel); }

  // confirma exclusões genéricas
  document.addEventListener('submit', (e)=>{
    const el = e.target;
    if (el.matches('form[data-confirm]')){
      if (!confirm(el.getAttribute('data-confirm'))) e.preventDefault();
    }
  });

  // ---- atalhos ----
  let gPressed = false;
  document.addEventListener('keydown', (e)=>{
    if (e.key === '/' && !e.ctrlKey && !e.metaKey) {
      const q = document.querySelector('input[name="q"]');
      if (q){ e.preventDefault(); q.focus(); q.select(); }
    } else if (e.key.toLowerCase() === 'n' && !e.ctrlKey && !e.metaKey && !e.altKey) {
      if (!/INPUT|TEXTAREA|SELECT/.test((document.activeElement||{}).tagName||'')){
        e.preventDefault(); location.href = '/os/nova';
      }
    } else if (e.key.toLowerCase()==='g'){ gPressed = true; setTimeout(()=>gPressed=false, 800); }
    else if (gPressed && e.key.toLowerCase()==='l'){ e.preventDefault(); location.href='/os/listar'; gPressed=false; }
    else if (gPressed && e.key.toLowerCase()==='r'){ e.preventDefault(); location.href='/relatorios'; gPressed=false; }
  });

  // ---- máscara telefone + validação e-mail (form Nova OS) ----
  const tel = $('input[name="telefone"]');
  if (tel){
    tel.addEventListener('input', ()=>{
      let v = tel.value.replace(/\D/g,'').slice(0,11);
      if (v.length>6) tel.value = `(${v.slice(0,2)}) ${v.slice(2,7)}-${v.slice(7)}`;
      else if (v.length>2) tel.value = `(${v.slice(0,2)}) ${v.slice(2)}`;
      else tel.value = v;
    });
  }
  const email = $('input[name="email"]');
  const form = document.querySelector('form[action="/os/criar"]');
  if (form){
    form.addEventListener('submit', (e)=>{
      const cliente = $('input[name="cliente"]');
      const problema = document.querySelector('textarea[name="problema"]');
      if (!cliente.value.trim() || !problema.value.trim()){
        alert('Cliente e Problema são obrigatórios.'); e.preventDefault(); return;
      }
      if (email && email.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)){
        alert('E-mail inválido.'); e.preventDefault(); return;
      }
    });
  }
})();
