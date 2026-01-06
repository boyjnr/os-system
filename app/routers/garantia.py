#!/usr/bin/env python3
# Módulo Garantia – Parte A

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pathlib import Path
from enum import Enum
import sqlite3

# PDF opcional
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from app.deps import get_db_connection

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(prefix="/garantia", tags=["garantia"])

class TipoGarantia(str, Enum):
    SERVICO = "Serviço"
    PECA = "Peça"
    COMPLETA = "Completa"
    ESTENDIDA = "Estendida"
    FABRICANTE = "Fabricante"

class StatusGarantia(str, Enum):
    ATIVA = "Ativa"
    EXPIRADA = "Expirada"
    CANCELADA = "Cancelada"
    SUSPENSA = "Suspensa"
    ACIONADA = "Acionada"

class StatusAcionamento(str, Enum):
    ABERTO = "Aberto"
    EM_ANALISE = "Em Análise"
    APROVADO = "Aprovado"
    NEGADO = "Negado"
    CONCLUIDO = "Concluído"

def criar_tabelas_garantia(conn):
    cur = conn.cursor()
    # garantias
    cur.execute("""
    CREATE TABLE IF NOT EXISTS garantias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        os_id INTEGER NOT NULL,
        codigo_garantia TEXT UNIQUE,
        tipo TEXT NOT NULL,
        descricao_cobertura TEXT,
        exclusoes TEXT,
        data_inicio DATE NOT NULL,
        data_fim DATE NOT NULL,
        prazo_dias INTEGER DEFAULT 365,
        status TEXT DEFAULT 'Ativa',
        cliente_nome TEXT,
        cliente_cpf TEXT,
        cliente_email TEXT,
        cliente_telefone TEXT,
        equipamento TEXT,
        modelo TEXT,
        serial TEXT,
        valor_servico REAL DEFAULT 0,
        limite_acionamentos INTEGER DEFAULT NULL,
        acionamentos_usados INTEGER DEFAULT 0,
        observacoes TEXT,
        termos_condicoes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cancelada_em TIMESTAMP,
        motivo_cancelamento TEXT,
        FOREIGN KEY (os_id) REFERENCES os(id) ON DELETE CASCADE,
        CHECK (status IN ('Ativa','Expirada','Cancelada','Suspensa','Acionada'))
    )""")
    # acionamentos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS garantia_acionamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        garantia_id INTEGER NOT NULL,
        os_nova_id INTEGER,
        protocolo TEXT UNIQUE,
        data_acionamento DATE DEFAULT CURRENT_DATE,
        problema_relatado TEXT NOT NULL,
        diagnostico TEXT,
        solucao TEXT,
        status TEXT DEFAULT 'Aberto',
        analisado_por TEXT,
        data_analise DATE,
        motivo_negacao TEXT,
        custo_total REAL DEFAULT 0,
        custo_coberto REAL DEFAULT 0,
        custo_cliente REAL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        concluido_em TIMESTAMP,
        FOREIGN KEY (garantia_id) REFERENCES garantias(id) ON DELETE CASCADE,
        FOREIGN KEY (os_nova_id) REFERENCES os(id),
        CHECK (status IN ('Aberto','Em Análise','Aprovado','Negado','Concluído'))
    )""")
    # templates
    cur.execute("""
    CREATE TABLE IF NOT EXISTS garantia_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL,
        prazo_dias INTEGER DEFAULT 365,
        descricao_cobertura TEXT,
        exclusoes TEXT,
        termos_condicoes TEXT,
        ativo BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    # alertas
    cur.execute("""
    CREATE TABLE IF NOT EXISTS garantia_alertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        garantia_id INTEGER NOT NULL,
        tipo_alerta TEXT NOT NULL,
        mensagem TEXT,
        data_alerta DATE,
        enviado BOOLEAN DEFAULT 0,
        data_envio TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (garantia_id) REFERENCES garantias(id) ON DELETE CASCADE
    )""")
    # índices
    cur.execute("CREATE INDEX IF NOT EXISTS idx_garantias_os ON garantias(os_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_garantias_status ON garantias(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_garantias_data_fim ON garantias(data_fim)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_acionamentos_garantia ON garantia_acionamentos(garantia_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_acionamentos_status ON garantia_acionamentos(status)")

    # templates básicos
    cur.executemany("""
    INSERT OR IGNORE INTO garantia_templates
      (id,nome,tipo,prazo_dias,descricao_cobertura,exclusoes,termos_condicoes,ativo)
    VALUES (?,?,?,?,?,?,?,1)
    """, [
        (1,'Garantia Padrão - Serviço','Serviço',365,
         'Cobertura total sobre mão de obra:\n• Reinstalação de sistemas\n• Configurações\n• Limpeza preventiva\n• Diagnósticos e testes',
         'Não cobre:\n• Mau uso\n• Danos físicos\n• Software não autorizado\n• Vírus/malware',
         'TERMOS:\n1) Válida com certificado\n2) Não cobre peças\n3) Trazer até a loja\n4) Análise até 48h\n5) Intransferível'),
        (2,'Garantia Premium - Completa','Completa',365,
         'Cobertura TOTAL:\n• Mão de obra ilimitada\n• Peças -50%\n• Prioridade\n• Suporte remoto\n• Backup mensal',
         'Exclusões:\n• Danos intencionais\n• Desastres naturais',
         'PREMIUM:\n1) VIP\n2) Técnico sênior\n3) Relatórios mensais\n4) -50% upgrades\n5) Transferível c/ taxa'),
        (3,'Garantia de Peça','Peça',90,
         'Cobertura peças instaladas:\n• Defeito fabricação\n• Falhas prematuras\n• Incompatibilidade',
         'Não cobre:\n• Desgaste natural\n• Uso fora de especificação\n• Danos físicos',
         'Conforme fabricante (mín. 90 dias)')
    ])
    conn.commit()
