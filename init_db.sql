CREATE DATABASE IF NOT EXISTS tiextremo_crm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tiextremo_crm;

CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nome_cliente VARCHAR(255) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    email VARCHAR(255),
    cep VARCHAR(15),
    endereco VARCHAR(255),
    INDEX(nome_cliente)
);

CREATE TABLE IF NOT EXISTS ordens_servico (
    id_os INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    equipamento VARCHAR(100) NOT NULL,
    marca_modelo VARCHAR(100),
    numero_serie VARCHAR(100),
    problema VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Em Análise',
    prioridade VARCHAR(50) DEFAULT 'Média',
    data_abertura DATE,
    data_fechamento DATE,
    valor_total DECIMAL(10,2) DEFAULT 0.00,
    forma_pagamento VARCHAR(50) DEFAULT '-',
    parcelas INT DEFAULT 1,
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    INDEX(status)
);
