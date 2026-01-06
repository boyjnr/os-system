
(function () {
  const byId = (id) => document.getElementById(id);

  // Normaliza para 8 dígitos
  function normCEP(v) {
    return String(v || "").replace(/\D/g, "").slice(0, 8);
  }

  // Máscara dinâmica #####-###
  function maskCEP(e) {
    let v = normCEP(e.target.value);
    if (v.length > 5) v = v.slice(0, 5) + "-" + v.slice(5);
    e.target.value = v;
  }

  async function buscaCEP(cepRaw) {
    const cep = normCEP(cepRaw);
    if (cep.length !== 8) return null;
    try {
      const r = await fetch("https://viacep.com.br/ws/" + cep + "/json/");
      if (!r.ok) return null;
      const j = await r.json();
      if (j.erro) return null;
      return j;
    } catch {
      return null;
    }
  }

  async function onCEPBlur() {
    const cepEl = byId("cep");
    const endEl = byId("endereco");
    const numEl = byId("numero");
    if (!cepEl || !endEl) return;

    const data = await buscaCEP(cepEl.value);
    if (!data) return;

    const partes = [
      data.logradouro || "",
      data.bairro || "",
      [data.localidade, data.uf].filter(Boolean).join(" - ").trim()
    ].filter(Boolean);

    const montado = partes.join(", ");
    if (montado && !endEl.value) endEl.value = montado;
    if (numEl && !numEl.value) numEl.focus();
  }

  function init() {
    const cepEl = byId("cep");
    if (!cepEl) return;
    cepEl.addEventListener("input", maskCEP);
    cepEl.addEventListener("blur", onCEPBlur);
    // aplica máscara no valor inicial (se houver)
    if (cepEl.value) {
      const ev = new Event("input");
      cepEl.dispatchEvent(ev);
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
