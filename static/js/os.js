(function () {
  const $ = (sel) => document.querySelector(sel);

  // Máscara simples de telefone BR
  const tel = $('#telefone');
  if (tel) {
    tel.addEventListener('input', () => {
      let v = tel.value.replace(/\D/g, '');
      if (v.length > 11) v = v.slice(0, 11);
      if (v.length > 10) {
        tel.value = v.replace(/(\d{2})(\d{1})(\d{4})(\d{4})/, '($1) $2$3-$4'); // (11) 9xxxx-xxxx
      } else if (v.length > 6) {
        tel.value = v.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3'); // (11) xxxx-xxxx
      } else if (v.length > 2) {
        tel.value = v.replace(/(\d{2})(\d{0,4})/, '($1) $2');
      } else {
        tel.value = v;
      }
    });
  }

  // Limite de 5 MB para o anexo (alinhado ao backend)
  const file = $('#anexo');
  const errorBox = $('#error-box');
  const form = $('#form-os');

  function setError(msg) {
    if (!errorBox) return;
    if (msg) {
      errorBox.textContent = msg;
      errorBox.style.display = 'block';
    } else {
      errorBox.textContent = '';
      errorBox.style.display = 'none';
    }
  }

  if (file) {
    file.addEventListener('change', () => {
      setError('');
      const f = file.files[0];
      if (f && f.size > 5 * 1024 * 1024) {
        setError('Arquivo excede 5 MB.');
        file.value = '';
      }
    });
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      setError('');
      const cliente = $('#cliente')?.value?.trim();
      const problema = $('#problema')?.value?.trim();
      if (!cliente || !problema) {
        e.preventDefault();
        setError('Preencha os campos obrigatórios: Cliente e Problema.');
        return false;
      }
    });
  }
})();
