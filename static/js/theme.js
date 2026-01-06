(function () {
  const KEY = 'tiextremo.theme';
  const root = document.documentElement;

  function apply(theme) {
    root.setAttribute('data-theme', theme);
    try { localStorage.setItem(KEY, theme); } catch {}
    const btn = document.getElementById('theme-toggle');
    if (btn) btn.textContent = theme === 'light' ? '🌙 Escuro' : '☀️ Claro';
    // Bootstrap 5: alterna data-bs-theme também
    root.setAttribute('data-bs-theme', theme === 'light' ? 'light' : 'dark');
  }

  let saved = 'dark';
  try {
    const val = localStorage.getItem(KEY);
    if (val === 'light' || val === 'dark') saved = val;
  } catch {}

  apply(saved);

  window.toggleTheme = function () {
    const now = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    apply(now);
  };
})();
