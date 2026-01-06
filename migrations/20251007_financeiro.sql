-- ===== FINANCEIRO (sem tocar nos PDFs/OS/Orçamento) =====

CREATE TABLE IF NOT EXISTS orcamentos (
  id INTEGER PRIMARY KEY,
  os_id INTEGER NOT NULL,
  valor_total REAL NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'rascunho', -- rascunho|enviado|aprovado|aplicado|cancelado
  aprovado_por TEXT,
  aprovado_em TEXT, -- ISO8601
  forma_pagto TEXT, -- opcional no momento da aprovação
  parcelas INTEGER DEFAULT 1,
  entrada_valor REAL DEFAULT 0,
  obs TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS orcamentos_itens (
  id INTEGER PRIMARY KEY,
  orcamento_id INTEGER NOT NULL,
  descricao TEXT NOT NULL,
  qtd REAL NOT NULL DEFAULT 1,
  preco_unit REAL NOT NULL DEFAULT 0,
  subtotal REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS financeiro_lancamentos (
  id INTEGER PRIMARY KEY,
  os_id INTEGER NOT NULL,
  cliente_nome TEXT,
  descricao TEXT,
  valor_bruto REAL NOT NULL DEFAULT 0,
  desconto REAL NOT NULL DEFAULT 0,
  acrescimo REAL NOT NULL DEFAULT 0,
  valor_liquido REAL NOT NULL DEFAULT 0,
  forma_pagto TEXT,
  status TEXT NOT NULL DEFAULT 'a_receber', -- a_receber|recebido|cancelado
  emitido_em TEXT DEFAULT (datetime('now')),
  vencimento TEXT,
  recebido_em TEXT,
  obs TEXT
);

CREATE TABLE IF NOT EXISTS financeiro_parcelas (
  id INTEGER PRIMARY KEY,
  lancamento_id INTEGER NOT NULL,
  parcela_num INTEGER NOT NULL,
  valor REAL NOT NULL,
  vencimento TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'a_receber', -- a_receber|recebido|cancelado
  pago_em TEXT,
  meio_pagto TEXT
);

CREATE INDEX IF NOT EXISTS idx_orc_status ON orcamentos(status, os_id);
CREATE INDEX IF NOT EXISTS idx_fin_lanc_status ON financeiro_lancamentos(status, vencimento);
CREATE INDEX IF NOT EXISTS idx_fin_parc_status ON financeiro_parcelas(status, vencimento);
